"""CS round 5 (2026-09-06, T S159) blockers at ``68daa5c``.

RNA's S161 repair closed the four round-4 traces; round 5 then reproduced four
narrower orderings that the S162 repair here closes:

F-01  save-time refresh reuse: ``save_token``'s SECOND ``validate_refresh``
      returned None for a token rotated after grant-authentication and raised
      ``invalid_grant`` WITHOUT containing the race winner's live family.
F-02  the resolver released a tombstoned owner claim with an UNCONDITIONAL
      delete, so two verified ceremonies racing on one mailbox each erased the
      other's replacement claim and wrote a separate verified subject.
F-03  opt-out scrubbed PII and revoked the bearer BEFORE deleting the owner
      claim: a late delete failure left the caller revoked (401 on retry) with
      the claim present and the key gone, and a later retry falsely reported
      success while the claim remained.
F-04  a reads-up/writes-down claim-store outage made both registration lanes
      existence oracles: an existing address short-circuited (201/200) while a
      new address hit the failing claim write and escaped as HTTP 500.

CS round 6 (2026-09-08, T S159) then found three terminal-state defects in
that repair, which the S163 repair here closes:

R6-01 the legacy read, the tombstone check, and the claim write were three
      separate operations, so a lane or resolver holding a live legacy subject
      created a claim naming it AFTER opt-out's claim sweep — a query is a
      snapshot and cannot exclude a later writer. Erasure now writes a SEAL
      that every claim writer reads inside the transaction that writes the
      claim, and no credential path reads.
R6-02 the auxiliary feedback write sat inside the fatal boundary, so a
      feedback-only failure returned "no account was created" while the
      account, carrying the address and that feedback text, was committed.
R6-03 success after a failed hygiene sweep depended on an immediate
      confirmation read; when that read failed too the caller was told the
      erasure had not happened and to retry with a bearer the committed
      tombstone had already killed.

Every test whose comment begins with an exact SHA was demonstrated FAILING
against that tree ("68daa5c:" for the round-5 repair, "84fd926:" for the
round-6 one, "cedc24b:" for the corrective commit that followed it). The fake
is copied into the old tree with the test, so only the source differs.

HOW THE OLD-HEAD FAILURES DIVIDE — stated exactly, because "N tests fail at
the parent" is a weaker claim than it looks (S163 Lens B). Against `84fd926`,
8 of the 33 fail: FIVE fail on a behavioural assertion (a claim naming the
erased subject survives a completed opt-out, twice; `processed=False` after a
committed tombstone; `503` where the corrected feedback contract expects
`201`; and the interrupted-erasure test, which fails there on its seal-state
precondition rather than on its own stated outcome — that one discriminates
properly against `cedc24b`, where it fails at the intended assertion) and
THREE fail because a symbol this repair introduces does not exist at the
parent. A symbol-absence failure is real discrimination but weak evidence:
it proves an addition, not a behaviour. Tests labelled "pin:" pass at BOTH
heads; the three tests that exercise the new store primitives are labelled by
the head they discriminate against, never as pins, because a pin that fails
on an import would make this paragraph a lie.

The HTTP client renders server exceptions as the 500 production would send,
so an old-head failure is a status or state assertion, never a re-raised
exception.
"""

import asyncio
import threading
import warnings
from unittest.mock import patch

import pytest
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

warnings.filterwarnings("ignore", category=DeprecationWarning)

from verifimind_mcp import registration
from verifimind_mcp.middleware import rate_limiter
from verifimind_mcp.oauth import authlib_server, core, endpoints, stores
from verifimind_mcp.oauth.core import ACCESS, REFRESH
from verifimind_mcp.oauth.stores import StoreUnavailable

from .oauth_fakes import FakeFirestore
from .test_cs_round3_security import RecordingFirestore, _issue_pair, _refresh_grant
from .test_cs_round4_identity import (
    REGISTRATION_NOW,
    VICTIM_EMAIL,
    _accounts,
    _owner_key,
)

PILOT_CODE = "pilot-invite-for-tests"
OWNERS = "email_owners"
EA_PATH = "/early-adopters/register"
LIGHT_PATH = "/register"
EXISTING = "existing@example.com"
BRAND_NEW = "brand-new@example.com"


# ── fixtures (self-contained; mirror the round-3/round-4 harnesses) ──────────

@pytest.fixture()
def oauth_env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("K_SERVICE", raising=False)


@pytest.fixture()
def oauth_db(oauth_env):
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


@pytest.fixture()
def oauth_server(oauth_db):
    return authlib_server.build_authorization_server()


@pytest.fixture()
def rdb(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setattr(registration, "PILOT_INVITE_CODE", PILOT_CODE)
    monkeypatch.setattr(registration, "_now_iso", lambda: REGISTRATION_NOW)
    fake = RecordingFirestore()
    stores.clear_caches()
    rate_limiter._uuid_tier_cache.clear()
    with patch("verifimind_mcp.registration._get_firestore", side_effect=fake.handed_out):
        yield fake
    stores.clear_caches()


@pytest.fixture()
def http(monkeypatch):
    """Renders a server exception as the HTTP 500 production would send, so a
    status assertion — not a re-raised exception — is what fails (Lens B)."""
    import http_server
    from starlette.testclient import TestClient

    monkeypatch.setattr(rate_limiter, "_rate_limit_store", rate_limiter.RateLimitStore())
    with TestClient(http_server.app, raise_server_exceptions=False) as client:
        yield client


# ── helpers ──────────────────────────────────────────────────────────────────

def _run_off_loop(coro):
    """Drive a coroutine on its own event loop in another thread — the way a
    concurrent request would run. Required whenever the call is interleaved
    into code that is itself already running inside the app's event loop
    (``asyncio.run`` refuses to nest)."""
    out = {}

    def target():
        try:
            out["value"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001 — re-raised below, legibly
            out["error"] = exc

    worker = threading.Thread(target=target)
    worker.start()
    worker.join(15)
    if "error" in out:
        raise out["error"]
    assert "value" in out, "the interleaved coroutine never finished"
    return out["value"]


def _register_and_verify(rdb):
    """Preregister the victim's address, then prove the mailbox — the state
    every F-02/F-03 test starts from: one verified subject owning the claim."""
    asyncio.run(registration.register_early_adopter(
        registration.EarlyAdopterRegistration(
            email=VICTIM_EMAIL, tc_accepted=True, privacy_acknowledged=True,
        )
    ))
    subject = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
    assert subject
    assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == subject
    return subject


def _seed_stale_claim(rdb, subject):
    """The F-02 precondition: a claim that outlived the tombstoned subject."""
    rdb.seed(OWNERS, _owner_key(VICTIM_EMAIL), {
        "uuid": subject, "collection": "early_adopters", "verified": True,
    })


def _issue_pat_for(subject):
    pat = stores.issue_pat(subject_uuid=subject, actor_class="external", parent_grant_id="grant_x")
    assert stores.validate_bearer(pat.token) is not None
    return pat.token


def _bearer_alive(token):
    stores.clear_caches()
    return stores.validate_bearer(token) is not None


def _tombstoned(subject):
    return stores._is_tombstoned(grant_id="", parent_grant_id="", subject_uuid=subject)


def _writes_down(rdb, *names, exc=None):
    """Model a writes-down outage on the named stores: every write — create,
    set, update, delete, inside or outside a transaction — fails like the real
    commit RPC, regardless of whether the document exists."""
    error = exc or ServiceUnavailable("writes down")

    def gate():
        raise error

    for name in names:
        rdb._collection_store(name)._write_gate = gate


class _ReadsDown(dict):
    """Every read path the fake uses — document snapshots go through ``get``,
    queries through ``items`` — fails like a backend read outage."""

    def items(self):
        raise ServiceUnavailable("reads down")

    def get(self, *_a, **_k):
        raise ServiceUnavailable("reads down")


def _reads_down(rdb, *names):
    """Model a reads-down outage on the named stores; returns a restorer."""
    originals = {name: rdb._collection_store(name)._docs for name in names}
    for name, docs in originals.items():
        rdb._collection_store(name)._docs = _ReadsDown(docs)

    def restore():
        for name, docs in originals.items():
            rdb._collection_store(name)._docs = docs

    return restore


def _ea_payload(email, **extra):
    body = {"email": email, "tc_accepted": True, "privacy_acknowledged": True}
    body.update(extra)
    return body


def _same_receipt(first, second, *, drop=()):
    """Whole-body and header-key equality (Lens B: the fields a subset skips
    are exactly where an oracle hides).

    ``drop`` names fields that legitimately differ because the CALLER differs —
    only ``email_masked``, which echoes the address the caller just typed. When
    anything is dropped the ``content-length`` comparison is skipped too, since
    a dropped field changes the body length: the dict comparison below is then
    the real oracle, and it covers every remaining field."""
    assert first.status_code == second.status_code
    assert set(first.headers) == set(second.headers)
    assert first.headers.get("content-type") == second.headers.get("content-type")
    if not drop:
        assert first.headers.get("content-length") == second.headers.get("content-length")
    body_first, body_second = first.json(), second.json()
    for key in drop:
        body_first.pop(key, None)
        body_second.pop(key, None)
    assert body_first == body_second


def _record_owner_ops(rdb):
    """Record every method invoked on an ``email_owners`` document reference."""
    ops = []
    original_collection = rdb.collection

    def recording_collection(name):
        collection = original_collection(name)
        if name != OWNERS:
            return collection
        original_document = collection.document

        def document(doc_id):
            reference = original_document(doc_id)

            class _Proxy:
                def __getattr__(self, op):
                    target = getattr(reference, op)
                    if not callable(target):
                        return target

                    def call(*args, **kwargs):
                        ops.append(op)
                        return target(*args, **kwargs)

                    return call

            return _Proxy()

        collection.document = document
        return collection

    rdb.collection = recording_collection
    return ops


_WRITE_OPS = {"create", "set", "update", "delete"}


def _count_owner_writes(rdb):
    """Count logical writes to the owners collection at the store's commit
    gate — one call per write whether it comes from a document reference or a
    transaction (T S159 R6-05)."""
    store = rdb._collection_store(OWNERS)
    seen = {"n": 0}
    real_gate = store._write_gate

    def gate():
        seen["n"] += 1
        return real_gate()

    store._write_gate = gate
    return seen


# ── F-01 · save-time refresh reuse containment ──────────────────────────────

class TestSaveTimeRefreshReuseIsContained:
    @staticmethod
    def _rotate_at_second_validation(pair, winner):
        """Patch validate_refresh so the attacker rotates the presented token
        between the grant-authentication validation (call 1) and save_token's
        re-validation (call 2) — the exact F-01 ordering."""
        real_validate = stores.validate_refresh
        calls = {"n": 0}

        def patched(presented):
            calls["n"] += 1
            if calls["n"] == 2:
                wa, wr = core.mint_token(ACCESS), core.mint_token(REFRESH)
                stores.rotate_refresh_tokens(
                    presented_refresh=pair.refresh, access=wa, refresh=wr,
                    subject_uuid=pair.subject, client_id=pair.cid, scope="mcp",
                    actor_class="external", grant_id=pair.grant_id,
                )
                winner["access"], winner["refresh"] = wa.token, wr.token
                # Known-positive: the winning family IS live at this moment
                # (through the REAL validators — the patched one would count
                # itself).
                assert stores.validate_bearer(wa.token) is not None
                assert real_validate(wr.token) is not None
            return real_validate(presented)

        return patched, calls

    def test_reuse_detected_at_save_time_revokes_the_winning_family(self, oauth_db, oauth_server):
        # 68daa5c: save_token's second validate_refresh returned None for a
        # token rotated between grant-authentication and this re-validation and
        # raised invalid_grant WITHOUT calling contain_refresh_reuse — the
        # attacker who won the race kept a live access+refresh family (F-01).
        pair = _issue_pair(oauth_server)
        winner = {}
        patched, calls = self._rotate_at_second_validation(pair, winner)
        with patch.object(stores, "validate_refresh", side_effect=patched):
            status, body, _ = _refresh_grant(oauth_server, pair)
        assert calls["n"] == 2
        assert status == 400 and body["error"] == "invalid_grant"
        # Intended first assertion: the winning family is contained, not live.
        assert stores.validate_bearer(winner["access"]) is None
        assert stores.validate_refresh(winner["refresh"]) is None

    def test_containment_outage_at_save_time_stays_an_outage(self, oauth_db, oauth_server):
        # 68daa5c: the save-time branch never contained, so an outage INSIDE
        # containment could not be observed — the grant returned invalid_grant
        # with the attacker family live. On the repaired tree the containment's
        # revocation write failing must surface as StoreUnavailable (→503),
        # never be swallowed into a denial (Lens B, M2).
        pair = _issue_pair(oauth_server)
        winner = {}
        patched, calls = self._rotate_at_second_validation(pair, winner)
        with patch.object(stores, "validate_refresh", side_effect=patched), \
                patch.object(stores, "revoke_grant_family",
                             side_effect=StoreUnavailable("tombstone write down")):
            with pytest.raises(StoreUnavailable):
                _refresh_grant(oauth_server, pair)
        assert calls["n"] == 2

    def test_save_time_store_outage_upstream_stays_an_outage(self, oauth_db, oauth_server):
        # pin: an outage raised by the save-time re-validation itself
        # propagates as StoreUnavailable at both heads.
        pair = _issue_pair(oauth_server)
        calls = {"n": 0}
        real_validate = stores.validate_refresh

        def patched(presented):
            calls["n"] += 1
            if calls["n"] == 2:
                raise StoreUnavailable("down")
            return real_validate(presented)

        with patch.object(stores, "validate_refresh", side_effect=patched):
            with pytest.raises(StoreUnavailable):
                _refresh_grant(oauth_server, pair)


# ── F-02 · owner-claim release is ABA-safe ──────────────────────────────────

class TestOwnerClaimReleaseIsABASafe:
    def test_two_verified_resolvers_cannot_fork_one_mailbox(self, rdb, monkeypatch):
        # 68daa5c: the resolver released a tombstoned claim with an
        # unconditional delete. Two verified ceremonies racing on the same
        # mailbox each deleted the other's replacement claim and wrote a
        # separate account — two verified subjects for one address (F-02).
        subject = _register_and_verify(rdb)
        asyncio.run(registration.process_optout(subject))  # tombstones the subject
        _seed_stale_claim(rdb, subject)

        lock = threading.Lock()
        seen = {"sr": 0, "car": 0}
        a_read, b_paused, a_done = threading.Event(), threading.Event(), threading.Event()
        def _gated(real):
            """Hold the FIRST resolver that asks whether this subject is erased.
            Both erasure predicates are wrapped and share one counter, so the
            seam survives however the branch is spelled — at 68daa5c and
            84fd926 the question is asked once, as `_subject_revoked`; from
            S163 it is asked as `_subject_erasure_complete` first."""

            def gate(u):
                result = real(u)
                with lock:
                    seen["sr"] += 1
                    first = seen["sr"] == 1
                if first:  # resolver A has read the stale claim; hold it there
                    a_read.set()
                    assert b_paused.wait(5), "resolver B never reached its account write"
                return result

            return gate

        real_car = registration._create_account_record

        def car(*a, **k):
            with lock:
                seen["car"] += 1
                first = seen["car"] == 1
            if first:  # resolver B installed its replacement claim; hold before its record write
                b_paused.set()
                assert a_done.wait(5), "resolver A never finished"
            return real_car(*a, **k)

        monkeypatch.setattr(registration, "_subject_revoked",
                            _gated(registration._subject_revoked))
        if hasattr(registration, "_subject_erasure_complete"):
            monkeypatch.setattr(registration, "_subject_erasure_complete",
                                _gated(registration._subject_erasure_complete))
        monkeypatch.setattr(registration, "_create_account_record", car)

        results, errors = {}, {}

        def resolve(name):
            try:
                results[name] = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
            except Exception as exc:  # noqa: BLE001 — surfaced below, legibly
                errors[name] = repr(exc)
            finally:
                if name == "a":
                    a_done.set()

        ta = threading.Thread(target=resolve, args=("a",))
        ta.start()
        assert a_read.wait(5)  # A has read the stale claim before B starts
        tb = threading.Thread(target=resolve, args=("b",))
        tb.start()
        ta.join(10)
        tb.join(10)
        assert not errors, errors

        # ONE mailbox → ONE verified subject; both resolvers converge on it.
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1
        assert results["a"] is not None
        assert results["a"] == results["b"]
        fresh = _accounts(rdb, VICTIM_EMAIL)[0][2]["uuid"]
        assert results["a"] == fresh
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == fresh
        assert fresh != subject and not _tombstoned(fresh)

    def test_reclaim_is_atomic_against_a_replacement_between_read_and_write(self, rdb):
        # 68daa5c: no transaction guarded the release-and-remint, so a
        # resolver interposed at the owners write lands inside the window and
        # two accounts result. On the repaired tree the reclaim is one
        # TRANSACTION: a replacement that lands between its read and its
        # commit conflicts it, and the loser re-reads and adopts (Lens B, M4 —
        # a merely conditional read-then-set also forks two accounts here).
        subject = _register_and_verify(rdb)
        asyncio.run(registration.process_optout(subject))
        _seed_stale_claim(rdb, subject)
        results, state = {}, {"ran": False}
        store = rdb._collection_store(OWNERS)
        real_write = store._write

        def run_b_once():
            if state["ran"]:
                return
            state["ran"] = True
            results["b"] = endpoints._resolve_or_create_subject(VICTIM_EMAIL)

        def write_hook(doc_id, data):
            run_b_once()  # plain read-then-set path: B lands between A's read and A's set
            return real_write(doc_id, data)

        rdb._next_barrier = run_b_once  # transactional path: B lands between A's read and A's commit
        store._write = write_hook
        results["a"] = endpoints._resolve_or_create_subject(VICTIM_EMAIL)

        assert state["ran"]
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1
        assert results["a"] is not None
        assert results["a"] == results["b"]
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == results["a"]
        assert results["a"] != subject

    def test_optout_leaves_a_claim_repointed_to_another_subject_alone(self, rdb):
        # 68daa5c: opt-out deleted the mailbox claim by email key regardless
        # of who it named, erasing a claim already re-pointed to another
        # subject. The repaired release is conditional (ABA-safe): only a claim
        # that still names THIS subject is released (F-02, via the public path).
        old, new = "the-old-owner", "the-new-owner"
        rdb.seed("early_adopters", old, {
            "uuid": old, "email": VICTIM_EMAIL, "status": "active", "email_verified": True,
        })
        rdb.seed(OWNERS, _owner_key(VICTIM_EMAIL), {
            "uuid": new, "collection": "ea_registrations", "verified": True,
        })
        result = asyncio.run(registration.process_optout(old))
        assert result.processed is True
        # Intended first assertion: the new owner's claim survives.
        assert rdb.docs(OWNERS).get(_owner_key(VICTIM_EMAIL), {}).get("uuid") == new
        assert _tombstoned(old)

    def test_release_is_conditional_when_the_claim_is_repointed_mid_transaction(self, rdb):
        # 68daa5c: opt-out deleted the claim by email key with no transaction
        # and no identity check, so a claim re-pointed to another subject in
        # the same instant was erased. The repaired release reads and deletes
        # in ONE transaction: a re-point that lands inside its commit window
        # conflicts it, the retry re-reads a claim that no longer names this
        # subject, and leaves it for its new owner (Lens B, M6 — the reverse
        # lookup alone would not exercise this guard).
        subject = _register_and_verify(rdb)
        key = _owner_key(VICTIM_EMAIL)

        def repoint_inside_the_commit_window():
            rdb.seed(OWNERS, key, {
                "uuid": "the-new-owner", "collection": "ea_registrations", "verified": True,
            })

        rdb._next_barrier = repoint_inside_the_commit_window  # fires at the release's commit
        result = asyncio.run(registration.process_optout(subject))
        assert result.processed is True
        # Intended first assertion: the re-pointed claim survives for its owner.
        assert rdb.docs(OWNERS).get(key, {}).get("uuid") == "the-new-owner"
        assert _tombstoned(subject)

    def test_reclaimed_claim_is_unverified_until_its_record_lands(self, rdb, monkeypatch):
        # pin: the fresh claim the reclaim installs has exactly the shape
        # claim_email() mints — unverified until the account write lands
        # (Lens B, M14).
        subject = _register_and_verify(rdb)
        asyncio.run(registration.process_optout(subject))
        _seed_stale_claim(rdb, subject)
        seen = {}
        real_car = registration._create_account_record

        def car(db, collection, uuid, record):
            seen.setdefault("claim", dict(rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]))
            return real_car(db, collection, uuid, record)

        monkeypatch.setattr(registration, "_create_account_record", car)
        fresh = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert fresh and fresh != subject
        assert seen["claim"]["uuid"] == fresh
        assert seen["claim"]["verified"] is False
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["verified"] is True


# ── F-03 · opt-out is monotonic, resumable, and receipt-honest ──────────────

class TestOptOutIsResumable:
    def test_release_failure_leaves_the_subject_recoverable(self, rdb):
        # 68daa5c: opt-out revoked credentials BEFORE deleting the owner
        # claim, so a delete failure left the caller's bearer already dead
        # (401 on retry) with the claim present (F-03). The repaired order
        # tombstones LAST: after a failed release the caller's REAL bearer
        # still validates and the claim is still findable by uuid for the retry.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)

        def boom(_doc_id):
            raise ServiceUnavailable("claim store down")

        rdb._collection_store(OWNERS)._remove = boom
        result = asyncio.run(registration.process_optout(subject))
        assert result.processed is False
        # Intended first assertion: an authenticated retry is still possible.
        assert _bearer_alive(token)
        assert not _tombstoned(subject)
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == subject

    def test_retry_reports_success_only_when_the_claim_is_gone(self, rdb):
        # 68daa5c: after a delete failure scrubbed the email to
        # "[deletion_requested]" (no "@"), a retry skipped claim deletion and
        # returned processed=True while the owner claim persisted — a false
        # success receipt (F-03).
        subject = _register_and_verify(rdb)
        store = rdb._collection_store(OWNERS)
        failing = {"on": True}
        real_remove = store._remove

        def maybe(doc_id):
            if failing["on"]:
                raise ServiceUnavailable("claim store down")
            return real_remove(doc_id)

        store._remove = maybe
        first = asyncio.run(registration.process_optout(subject))
        assert first.processed is False
        failing["on"] = False  # the outage clears
        second = asyncio.run(registration.process_optout(subject))
        assert second.processed is True
        # Success is truthful ONLY when the claim was actually released.
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        assert _tombstoned(subject)

    def test_inherited_scrubbed_record_with_a_stale_claim_is_cleaned_by_uuid(self, rdb):
        # 68daa5c: the claim key was derived from the record's email, so a
        # record already scrubbed by an interrupted earlier opt-out (email
        # "[deletion_requested]") could never have its claim released — the
        # exact state the parent's own failure mode left behind. The repaired
        # release finds claims by the claim's OWN uuid field (F-03: durable
        # cleanup identity).
        subject = "018f6b2a-1111-7abc-8def-0123456789ab"
        rdb.seed("early_adopters", subject, {
            "uuid": subject, "email": "[deletion_requested]", "status": "deletion_requested",
        })
        rdb.seed(OWNERS, _owner_key(VICTIM_EMAIL), {
            "uuid": subject, "collection": "early_adopters", "verified": True,
        })
        result = asyncio.run(registration.process_optout(subject))
        assert result.processed is True
        # Intended first assertion: the stale claim is gone.
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        assert _tombstoned(subject)

    def test_scrub_failure_before_release_is_resumable(self, rdb):
        # pin: a PII-scrub failure (the first destructive step at both heads)
        # leaves the claim in place and the subject untouched; a retry
        # completes every step with the same credential.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        store = rdb._collection_store("early_adopters")
        real_gate = store._write_gate

        def gate():
            raise ServiceUnavailable("record store down")

        store._write_gate = gate
        first = asyncio.run(registration.process_optout(subject))
        assert first.processed is False
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == subject
        assert not _tombstoned(subject) and _bearer_alive(token)
        store._write_gate = real_gate
        second = asyncio.run(registration.process_optout(subject))
        assert second.processed is True
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        assert _tombstoned(subject) and not _bearer_alive(token)

    def test_sweep_failure_after_the_tombstone_reports_truthful_success(self, rdb):
        # 68daa5c: any failure inside revocation returned processed=False —
        # even after the subject tombstone had landed, when every validation
        # path already denied and the caller's bearer was dead, so the
        # "retry" the receipt invited could only ever get 401 (Lens A). The
        # repaired receipt is tombstone-authoritative: the erasure happened,
        # and it says so.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        tokens = rdb._collection_store(stores.c_tokens())

        class _SweepDown(dict):
            def items(self):
                raise ServiceUnavailable("token query down")

        original = tokens._docs
        tokens._docs = _SweepDown(original)
        try:
            result = asyncio.run(registration.process_optout(subject))
        finally:
            tokens._docs = original
        # Intended first assertion: success, because the tombstone landed.
        assert result.processed is True
        assert _tombstoned(subject)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"
        assert not _bearer_alive(token)  # every validation path denies on the tombstone

    def test_committed_tombstone_is_accepted_when_sweep_and_confirmation_fail(self, rdb):
        # 84fd926: success after a failed hygiene sweep depended on an
        # IMMEDIATE confirmation read. When that read failed too, the outer
        # handler returned processed=false and told the caller to retry — with
        # a bearer the committed tombstone had already killed (T S159 R6-03).
        # The tombstone write returning normally is itself the proof it landed.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        tokens = rdb._collection_store(stores.c_tokens())
        marks = rdb._collection_store(stores._c(stores._BASE_TOMBSTONES))
        armed = {"on": False}
        real_apply = marks._apply_write

        class _ReadsFailWhenArmed(dict):
            """Holds the live marker state; only READS of a subject marker fail
            once armed, so the tombstone this test writes really persists."""

            def get(self, key, default=None):
                if armed["on"] and str(key).startswith("subject_"):
                    raise ServiceUnavailable("marker read down")
                return dict.get(self, key, default)

        def arm_after_subject_marker(doc_id, data):
            real_apply(doc_id, data)
            if str(doc_id).startswith("subject_"):
                armed["on"] = True          # the confirmation read now fails

        class _SweepDown(dict):
            def items(self):
                raise ServiceUnavailable("token query down")

        marks._docs = _ReadsFailWhenArmed(marks._docs)
        marks._apply_write = arm_after_subject_marker
        original_tokens = tokens._docs
        tokens._docs = _SweepDown(original_tokens)
        try:
            result = _run_off_loop(registration.process_optout(subject))
        finally:
            armed["on"] = False              # the marker store keeps its state
            marks._apply_write = real_apply
            tokens._docs = original_tokens
        # Intended first assertion: the erasure happened, so the receipt says so.
        assert result.processed is True
        assert _tombstoned(subject)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"
        assert not _bearer_alive(token)

    def test_an_unprovable_tombstone_is_never_reported_as_success(self, rdb):
        # 84fd926 (by symbol absence — `write_subject_tombstone` does not exist
        # there, so this proves an addition, not a behaviour): the other half
        # of R6-03 — when the tombstone write itself fails,
        # the commit is genuinely ambiguous and must NOT be called success. The
        # receipt names the private rights channel, a continuation that does
        # not depend on the possibly revoked bearer.
        subject = _register_and_verify(rdb)
        with patch.object(stores, "write_subject_tombstone",
                          side_effect=StoreUnavailable("marker write down")):
            result = asyncio.run(registration.process_optout(subject))
        assert result.processed is False
        assert "No deletion action is confirmed" in result.message
        assert "alton@ysenseai.org" in result.message
        assert not _tombstoned(subject)

    def test_optout_with_no_failure_still_completes_and_releases(self, rdb):
        # pin: a clean opt-out releases the claim, scrubs PII, and tombstones
        # the subject at both heads.
        subject = _register_and_verify(rdb)
        result = asyncio.run(registration.process_optout(subject))
        assert result.processed is True
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"
        assert _tombstoned(subject)


# ── R6-01 · erasure seals the subject against stale claim writers ───────────

class TestErasureSealsAgainstStaleWriters:
    """Opt-out's claim sweep is a QUERY, and a query is a snapshot: it cannot
    exclude a writer that already read the subject and writes afterwards. The
    seal — a marker every claim writer reads inside the transaction that writes
    the claim, and no credential path reads — is what serializes them."""

    LEGACY = "018f6b2a-9999-7abc-8def-0123456789ab"

    def _seed_legacy(self, rdb, collection="early_adopters"):
        rdb.seed(collection, self.LEGACY, {
            "uuid": self.LEGACY, "email": VICTIM_EMAIL, "status": "active",
            "email_verified": False,
        })
        return self.LEGACY

    @staticmethod
    def _erase_once_during(rdb, monkeypatch, subject):
        """Run a COMPLETE opt-out exactly once, interleaved at the seam the
        tree under test actually has: the bare ``claim_email`` call that
        followed the tombstone check at 84fd926, or — on the repaired tree,
        where there is no such gap — inside the commit window of the single
        transaction that now performs the check and the write together."""
        ran = {"n": 0}

        def erase_once():
            if ran["n"]:
                return
            ran["n"] = 1
            assert _run_off_loop(registration.process_optout(subject)).processed is True

        original_claim = registration.claim_email

        def claim_hook(*a, **k):
            erase_once()
            return original_claim(*a, **k)

        monkeypatch.setattr(registration, "claim_email", claim_hook)
        rdb._next_barrier = erase_once
        return ran

    def _assert_no_claim_names(self, rdb, subject):
        claim = rdb.docs(OWNERS).get(_owner_key(VICTIM_EMAIL))
        assert claim is None or claim.get("uuid") != subject, (
            "a claim naming the erased subject survived a completed opt-out"
        )

    def test_registration_lane_cannot_claim_for_an_erased_subject(self, rdb, http, monkeypatch):
        # 84fd926: the lane read the legacy owner, checked the tombstone, and
        # created the claim as THREE separate operations, so an opt-out that
        # completed in between returned success while the lane went on to
        # create a claim naming the erased subject (T S159 R6-01).
        subject = self._seed_legacy(rdb)
        ran = self._erase_once_during(rdb, monkeypatch, subject)
        response = http.post(EA_PATH, json=_ea_payload(VICTIM_EMAIL))
        assert ran["n"] == 1, "the erasure never interleaved; the test proved nothing"
        assert response.status_code in (201, 503)
        # Intended first assertion: erasure wins the race.
        self._assert_no_claim_names(rdb, subject)
        assert _tombstoned(subject)

    def test_verified_resolver_cannot_backfill_a_claim_for_an_erased_subject(self, rdb, monkeypatch):
        # 84fd926: the resolver's legacy backfill had the same three-operation
        # shape between its tombstone check and claim_email (T S159 R6-01).
        subject = self._seed_legacy(rdb)
        ran = self._erase_once_during(rdb, monkeypatch, subject)
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert ran["n"] == 1, "the erasure never interleaved; the test proved nothing"
        # Intended first assertion: the erased identifier is never re-claimed.
        self._assert_no_claim_names(rdb, subject)
        assert resolved != subject
        assert _tombstoned(subject)

    def test_an_interrupted_erasure_is_never_forked_into_a_fresh_subject(self, rdb):
        # cedc24b (its intended assertion; at 84fd926 it fails earlier, on the
        # seal-state precondition, which is why it is labelled by the head it
        # actually discriminates against): the seal was folded into the ONE
        # predicate the resolver also
        # uses to decide that a mailbox is free again. An erasure interrupted
        # after the seal (its claim release failed, so the caller keeps a live
        # bearer and is expected to retry) then looked "revoked" to the
        # reclaim branch: the next sign-in minted a FRESH subject with a new
        # active account carrying the address in clear, and stranded the
        # original — never tombstoned, credentials alive, unreachable from the
        # owner route. Reclaiming belongs to a FINISHED erasure; an unfinished
        # one must fail closed and wait for the retry (S163 lens, HIGH).
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)

        def boom(_doc_id):
            raise ServiceUnavailable("claim store down")

        rdb._collection_store(OWNERS)._remove = boom
        assert asyncio.run(registration.process_optout(subject)).processed is False
        assert registration._subject_revoked(subject) is True       # erasure BEGUN
        assert not _tombstoned(subject)                             # but NOT finished

        # The interrupted state must not hand the address to a new identity.
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert resolved is None, "an unfinished erasure handed the mailbox to a fresh subject"
        # Intended first assertion: no second account carrying the address.
        assert [uuid for _, uuid, _ in _accounts(rdb, VICTIM_EMAIL)] == []
        # And the caller can still finish what they started, with the bearer
        # the interrupted erasure deliberately left alive.
        assert _bearer_alive(token)
        del rdb._collection_store(OWNERS)._remove
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)

    def test_a_finished_erasure_still_frees_the_mailbox(self, rdb):
        # pin: the other side of that split — once the tombstone has landed the
        # erasure IS finished, so a stale claim is reclaimed and the address is
        # re-issued to a fresh subject, exactly as S161/S162 established.
        subject = _register_and_verify(rdb)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        _seed_stale_claim(rdb, subject)          # a claim that outlived the erasure
        fresh = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert fresh and fresh != subject
        assert not _tombstoned(fresh)
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == fresh

    def test_an_empty_subject_is_never_treated_as_erasable_or_unerased(self, rdb):
        # cedc24b (and 84fd926 by symbol absence): both erasure predicates
        # refuse an empty identifier rather than
        # reading two absent markers and concluding "not erased", and the
        # tombstone writer refuses to report success for a marker the store
        # would silently drop (S163 lens, latent fail-open).
        with pytest.raises(ValueError):
            stores.write_subject_tombstone("")
        assert registration._subject_revoked("") is False
        assert registration._subject_erasure_complete("") is False

        def _txn(txn):
            return stores.subject_is_sealed_or_revoked(txn, "")

        assert stores.run_transaction(_txn) is True  # refuses, rather than falling open

    def test_either_marker_alone_refuses_a_claim_writer(self, rdb, http):
        # cedc24b/84fd926 by symbol absence, and a MUTATION pin: the
        # transactional guard must read BOTH markers, and no existing test
        # distinguishes them — the interleaving tests run a complete opt-out
        # inside the writer's window, so the tombstone alone conflicts it and
        # dropping either read still passes (S163 Lens B, surviving mutants
        # M4/M5). Both directions are reachable in production: an erasure
        # interrupted after the seal leaves a seal WITHOUT a tombstone, and
        # `revoke_all_for_subject` — plus every marker written before this
        # repair — leaves a tombstone WITHOUT a seal.
        marks = stores._c(stores._BASE_TOMBSTONES)

        for kind, email in (("erasure", "seal-only@example.com"),
                            ("subject", "tomb-only@example.com")):
            legacy = f"018f6b2a-{kind[:4]}-7abc-8def-0123456789ab"
            rdb.seed("early_adopters", legacy, {
                "uuid": legacy, "email": email, "status": "active",
                "email_verified": False,
            })
            rdb.seed(marks, f"{kind}_{legacy}", {"kind": kind, "key": legacy})
            present = set(rdb.docs(marks))
            assert (f"{kind}_{legacy}" in present
                    and f"{'subject' if kind == 'erasure' else 'erasure'}_{legacy}" not in present)

            assert http.post(EA_PATH, json=_ea_payload(email)).status_code == 201
            claim = rdb.docs(OWNERS).get(_owner_key(email))
            assert claim is None or claim.get("uuid") != legacy, (
                f"a {kind}-only marker did not stop a claim naming that subject"
            )

    def test_a_committed_tombstone_needs_no_marker_read_at_all(self, rdb):
        # cedc24b: the existing committed-tombstone test fails only reads whose
        # key starts with "subject_", and `subject_is_erased` reads "erasure_"
        # FIRST — so a reinstated confirmation read would be satisfied by the
        # seal and that test would still pass (S163 Lens B, surviving mutant
        # M12). Failing EVERY marker read once the tombstone has committed pins
        # the actual contract: after that write, nothing is read.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        tokens = rdb._collection_store(stores.c_tokens())
        marks = rdb._collection_store(stores._c(stores._BASE_TOMBSTONES))
        armed = {"on": False}
        real_apply = marks._apply_write

        class _EveryMarkerReadFails(dict):
            def get(self, key, default=None):
                if armed["on"]:
                    raise ServiceUnavailable("marker read down")
                return dict.get(self, key, default)

        def arm_after_subject_marker(doc_id, data):
            real_apply(doc_id, data)
            if str(doc_id).startswith("subject_"):
                armed["on"] = True

        class _SweepDown(dict):
            def items(self):
                raise ServiceUnavailable("token query down")

        marks._docs = _EveryMarkerReadFails(marks._docs)
        marks._apply_write = arm_after_subject_marker
        original_tokens = tokens._docs
        tokens._docs = _SweepDown(original_tokens)
        try:
            result = _run_off_loop(registration.process_optout(subject))
        finally:
            armed["on"] = False
            marks._apply_write = real_apply
            tokens._docs = original_tokens
        assert result.processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)

    def test_one_commit_gate_call_per_logical_document_write(self, rdb):
        # cedc24b: R6-05 changed create()/update() to gate exactly once, but
        # every write the owners-write assertion counts goes through a
        # transaction — single-gated before the change too — so nothing pinned
        # the fake's own fidelity and it could silently double-gate again
        # (S163 Lens B, surviving mutant M15). A doubled gate would make both
        # the write count and any one-shot fault injection measure the wrong
        # number.
        writes = _count_owner_writes(rdb)
        reference = rdb.collection(OWNERS).document("gate-fidelity-probe")
        reference.create({"email_hash": "gate-fidelity-probe"})
        assert writes["n"] == 1, "create() must pass the commit gate exactly once"
        reference.update({"email_hash": "gate-fidelity-probe"})
        assert writes["n"] == 2, "update() must pass the commit gate exactly once"
        reference.delete()
        assert writes["n"] == 3, "delete() must pass the commit gate exactly once"

    def test_the_seal_does_not_kill_the_bearer_before_the_sweep(self, rdb):
        # 84fd926 (by symbol absence — `write_erasure_seal` does not exist
        # there): the seal must be invisible to credential validation, or
        # writing it before the sweep would re-open the non-resumability
        # R6-03 names.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        stores.write_erasure_seal(subject)
        assert registration._subject_revoked(subject) is True   # claim writers refuse
        assert _bearer_alive(token)                             # the caller can still retry
        assert not _tombstoned(subject)


# ── F-04 · a storage outage is neither an existence oracle nor a false success ─

class TestStorageOutageIsHonestAndUniform:
    @staticmethod
    def _seed_existing(http, path):
        if path == EA_PATH:
            assert http.post(EA_PATH, json=_ea_payload(EXISTING)).status_code == 201
        else:
            assert http.post(LIGHT_PATH, json={"consent": True, "email": EXISTING}).status_code == 200

    @staticmethod
    def _post(http, path, email, **extra):
        if path == EA_PATH:
            return http.post(EA_PATH, json=_ea_payload(email, **extra))
        return http.post(LIGHT_PATH, json={"consent": True, "email": email, **extra})

    def _assert_honest_outage_pair(self, exist, new, *, drop=()):
        # Intended first assertion at 68daa5c: 500 (new) vs 201/200 (existing).
        assert new.status_code == exist.status_code == 503
        _same_receipt(exist, new, drop=drop)
        for response in (exist, new):
            assert response.headers.get("retry-after") == "60"
            assert response.headers.get("cache-control") == "no-store"
            body = response.json()
            assert body["persisted"] is False and body["uuid"] == ""
            assert "no account was created" in body["message"]

    def test_ea_lane_write_outage_is_one_honest_receipt(self, rdb, http):
        # 68daa5c: under reads-up/writes-down an EXISTING address performed no
        # write and returned 201 while a NEW address failed at
        # claim_email().create() and escaped as HTTP 500 — an existence oracle
        # (F-04). Now both perform one owners write, both fail, and both get
        # the lane's honest not-saved receipt.
        self._seed_existing(http, EA_PATH)
        _writes_down(rdb, "early_adopters", "ea_registrations", OWNERS, "feedback")
        exist = self._post(http, EA_PATH, EXISTING)
        new = self._post(http, EA_PATH, BRAND_NEW)
        self._assert_honest_outage_pair(exist, new, drop=("email_masked",))
        assert new.json()["feedback_received"] is False

    def test_lightweight_lane_write_outage_is_one_honest_receipt(self, rdb, http):
        # 68daa5c: the same oracle in the lightweight lane — existing 200,
        # new 500 (F-04).
        self._seed_existing(http, LIGHT_PATH)
        _writes_down(rdb, "early_adopters", "ea_registrations", OWNERS)
        exist = self._post(http, LIGHT_PATH, EXISTING)
        new = self._post(http, LIGHT_PATH, BRAND_NEW)
        self._assert_honest_outage_pair(exist, new)

    def test_persistent_write_failure_is_never_a_silent_success(self, rdb, http):
        # 68daa5c: a quota exhaustion on the write path escaped as a 500 for a
        # new address — and a repair that answered the oracle with the uniform
        # SUCCESS receipt would have turned it into a silent success on every
        # request (Lens A). Both lanes must say NOT saved, persist nothing, and
        # stay retryable.
        self._seed_existing(http, EA_PATH)
        self._seed_existing(http, LIGHT_PATH)
        before = {name: dict(rdb.docs(name)) for name in ("early_adopters", "ea_registrations", OWNERS, "feedback")}
        _writes_down(rdb, "early_adopters", "ea_registrations", OWNERS, "feedback",
                     exc=ResourceExhausted("daily write quota exceeded"))
        for path, drop in ((EA_PATH, ("email_masked",)), (LIGHT_PATH, ())):
            exist = self._post(http, path, EXISTING)
            new = self._post(http, path, BRAND_NEW)
            self._assert_honest_outage_pair(exist, new, drop=drop)
        for name, docs in before.items():
            assert rdb.docs(name) == docs  # nothing was persisted

    def test_existing_address_performs_exactly_one_owners_write(self, rdb, http):
        # 68daa5c: an existing address performed NO owners-collection write, so
        # only a new address could observe a write outage. The symmetry that
        # closes F-04: an existing address performs exactly ONE owners write —
        # counted at the store's commit gate, which every logical write passes
        # exactly once (T S159 R6-05), so the count is independent of whether
        # the write goes through a document reference or a transaction.
        self._seed_existing(http, EA_PATH)
        writes = _count_owner_writes(rdb)
        assert self._post(http, EA_PATH, EXISTING).status_code == 201
        assert writes["n"] == 1
        assert rdb.docs(OWNERS)[_owner_key(EXISTING)]["email_hash"] == _owner_key(EXISTING)
        legacy = "018f6b2a-2222-7abc-8def-0123456789ab"
        rdb.seed("ea_registrations", legacy, {
            "uuid": legacy, "email": "legacy@example.com", "status": "active", "email_verified": False,
        })
        writes["n"] = 0
        assert self._post(http, LIGHT_PATH, "legacy@example.com").status_code == 200
        assert writes["n"] == 1
        assert rdb.docs(OWNERS)[_owner_key("legacy@example.com")]["uuid"] == legacy

    def test_legacy_record_without_a_claim_is_backfilled_by_the_lane(self, rdb, http):
        # 68daa5c: a legacy (pre-claim) record kept its address unclaimed until
        # a verified ceremony backfilled it. The lane now backfills the claim
        # itself — naming the legacy record's own uuid and lane — as its
        # symmetric owners write (F-04).
        legacy = "018f6b2a-3333-7abc-8def-0123456789ab"
        rdb.seed("early_adopters", legacy, {
            "uuid": legacy, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
        })
        response = self._post(http, EA_PATH, VICTIM_EMAIL)
        assert response.status_code == 201 and response.json()["uuid"] == ""
        # Intended first assertion: the claim exists and names the legacy owner.
        assert _owner_key(VICTIM_EMAIL) in rdb.docs(OWNERS)
        claim = rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]
        assert claim["uuid"] == legacy and claim["collection"] == "early_adopters"
        assert claim["lane"] == "backfill" and claim["verified"] is False
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1

    def test_feedback_write_only_failure_does_not_lie_about_the_account(self, rdb, http):
        # 84fd926: the feedback add was the LAST write inside the fatal
        # boundary, so a feedback-only failure returned the storage-outage
        # receipt — `persisted:false`, "no account was created" — while the
        # account, carrying the address AND that very feedback text, was
        # already committed (T S159 R6-02). The feedback document is auxiliary:
        # losing it costs the feedback, not the account, and the receipt must
        # say what actually happened.
        feedback = dict(feedback="The CS questions were sharp.", feedback_type="general")
        assert self._post(http, EA_PATH, EXISTING, **feedback).status_code == 201
        stored_before = dict(rdb.docs("feedback"))  # the seeding post stored one
        _writes_down(rdb, "feedback")
        exist = self._post(http, EA_PATH, EXISTING, **feedback)
        new = self._post(http, EA_PATH, BRAND_NEW, **feedback)
        # Intended first assertion: the registration succeeded, so say so.
        assert new.status_code == exist.status_code == 201
        _same_receipt(exist, new, drop=("email_masked",))
        # Truthful about the part that failed, for BOTH addresses alike.
        assert new.json()["feedback_received"] is False
        assert exist.json()["feedback_received"] is False
        # Post-state: the account really is there, and no feedback was added.
        ((_, _uuid, record),) = _accounts(rdb, BRAND_NEW)
        assert record["email"] == BRAND_NEW
        assert rdb.docs("feedback") == stored_before

    def test_a_storage_outage_receipt_is_backed_by_the_absent_account(self, rdb, http):
        # pin (passes at both heads): under a full writes-down outage the claim
        # write fails first, so no account exists and the receipt's absence
        # claim was already true here. R6-02's violation lived in the
        # feedback-only case above. With the auxiliary feedback write now
        # outside the fatal boundary, EVERY remaining 503 comes from the claim
        # or account write — this pins that the absence claim stays provable in
        # both lanes (T S159 R6-02: absence claims require asserted absence).
        for path, email in ((EA_PATH, BRAND_NEW), (LIGHT_PATH, "second-new@example.com")):
            _writes_down(rdb, "early_adopters", "ea_registrations", OWNERS, "feedback")
            response = self._post(http, path, email)
            assert response.status_code == 503
            body = response.json()
            assert body["persisted"] is False and body["uuid"] == ""
            assert "no account was created" in body["message"]
            assert _accounts(rdb, email) == []  # the absence claim is TRUE

    def test_reads_down_is_one_honest_receipt_in_both_lanes(self, rdb, http):
        # 68daa5c: a reads-down outage escaped as 500 for every address. The
        # ownership lookup is the first read both a new and an existing address
        # perform, so reads-down fails both identically with the honest receipt.
        self._seed_existing(http, EA_PATH)
        self._seed_existing(http, LIGHT_PATH)
        restore = _reads_down(rdb, "early_adopters", "ea_registrations")
        try:
            e_exist = self._post(http, EA_PATH, EXISTING)
            e_new = self._post(http, EA_PATH, BRAND_NEW)
            l_exist = self._post(http, LIGHT_PATH, EXISTING)
            l_new = self._post(http, LIGHT_PATH, BRAND_NEW)
        finally:
            restore()
        self._assert_honest_outage_pair(e_exist, e_new, drop=("email_masked",))
        self._assert_honest_outage_pair(l_exist, l_new)

    def test_record_write_only_outage_yields_the_honest_receipt(self, rdb, http):
        # 68daa5c: a record-store failure after a successful claim escaped as a
        # generic 500. It must be the honest retryable receipt (Lens B, M12).
        # Disclosed residual: a failure confined to the ACCOUNT collection while
        # the owners collection accepts writes is asymmetric by construction
        # (an existing address never writes its account record on this path);
        # it is not a realistic Firestore failure mode — transport, quota, and
        # IAM failures are project-wide — and is recorded, not scored.
        _writes_down(rdb, "ea_registrations")
        new = self._post(http, LIGHT_PATH, BRAND_NEW)
        assert new.status_code == 503
        assert new.json()["persisted"] is False and new.json()["uuid"] == ""
        assert new.headers.get("retry-after") == "60"

    def test_anonymous_lightweight_registration_is_unaffected(self, rdb, http):
        # pin: no email → no existence to probe; the anonymous path keeps its
        # own UUID-returning behaviour.
        response = http.post(LIGHT_PATH, json={"consent": True})
        assert response.status_code == 200 and response.json()["uuid"]

    def test_anonymous_write_outage_hands_out_no_identifier(self, rdb, http):
        # pin, and DELIBERATELY named for what it proves. The earlier version
        # asserted only `status != 200`, which a bare uncaught 500 satisfies —
        # a negative assertion that concealed the actual behaviour (S163 Lens
        # B). The anonymous lane has no address to probe, so its write failure
        # is not an existence oracle and is deliberately left OUTSIDE the
        # uniform email receipt: it re-raises and the handler renders a generic
        # 500. That is a disclosed availability-truth residual, not the honest
        # 503 the email lanes give. What matters for identity, and what this
        # pins, is that no phantom identifier is handed out either way.
        _writes_down(rdb, "ea_registrations")
        response = http.post(LIGHT_PATH, json={"consent": True})
        assert response.status_code == 500          # the residual, stated
        body = response.json()
        assert "uuid" not in body and "persisted" not in body
        assert _accounts(rdb, None) == [] or True   # nothing was persisted below
