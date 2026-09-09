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

CS round 7 (2026-09-09, T S161) then attacked the gaps BETWEEN those
operations and found a terminal ordering in which each step was correct and
the sequence was not — closed by the S164 repair here:

A-1   opt-out released the ownership claim and scrubbed the email BEFORE the
      subject tombstone; when that final write failed, nothing routed the
      mailbox back to the sealed subject, whose bearer stayed alive by
      design, so a verified ceremony minted a SECOND subject for the same
      address. The claim now outlives the tombstone: it is the fence every
      identity-creation path finds first, and hygiene runs after the point
      of no return.
A-2   only a backend outage was tolerated after the tombstone (any other
      exception negated an accepted erasure), and a bearer-valid subject with
      no account row received success with nothing revoked.
A-3   ``feedback_received: false`` accompanied text persisted in the account;
      an unconstructible Firestore client returned 201/200 with
      ``persisted: false``; and the outage receipt asserted "no account was
      created" after an ambiguous commit.
A-4   an existing address read the subject's erasure markers inside its
      claim transaction while a new address did not, so a revocation-marker
      outage was an email-existence oracle in both lanes.
S164  the author's own attacker lens, run before the push, then found the
      same state machine one step further out: a verified-ceremony heal of a
      claim-only subject racing its erasure left an ACTIVE row carrying the
      address for a tombstoned subject (new by effect, once the account-row
      gate was gone); the scrub ran before the seal; an address with no claim
      lost its only route before a fence existed; and a row keyed differently
      from its uuid field was never scrubbed. The erasure now fences, seals,
      scrubs, tombstones, then re-scrubs by uuid field, and the heal reads
      both markers through the transaction that writes the record.

Every test whose comment begins with an exact SHA was demonstrated FAILING
against that tree ("68daa5c:" for the round-5 repair, "84fd926:" for the
round-6 one, "cedc24b:" for the corrective commit that followed it,
"59424c5:" for the round-7 one). The fake is copied into the old tree with
the test, so only the source differs.

HOW THE OLD-HEAD FAILURES DIVIDE — stated exactly, because "N tests fail at
the parent" is a weaker claim than it looks (S163 Lens B). Against `84fd926`
the round-6 file, then 36 tests, failed 10: SEVEN on a behavioural assertion
and THREE because a symbol the round-6 repair introduced did not exist at
that parent (measured at S163 and re-measured by CS round 7; this file has
since grown). Against `59424c5`, 24 of the 52 fail, ALL on a
behavioural assertion and none by symbol absence — this repair introduces no
new store primitive. Nineteen are the round-7 and S164-lens tests (sixteen
new cases: fifteen tests, one parametrized over both hygiene steps; three
rewritten from the superseded ordering) failing at their intended first
assertion. The other five are round-5/6-era outage controls that fail on ONE
change counted five times — four through the shared outage-receipt helper
and one at its own inline assertion — the corrected receipt wording (A-3 /
F-6) in place of the parent's "no account was created". A symbol-absence failure is
real discrimination but weak evidence: it proves an addition, not a
behaviour. Tests labelled "pin:" pass at BOTH heads; a test that exercises a
primitive absent at the parent is labelled by the head it discriminates
against, never as a pin, because a pin that fails on an import would make
this paragraph a lie. Three round-6-era tests that pinned the superseded
ordering (claim release BEFORE the tombstone) were rewritten to T S161's
contract and are labelled "59424c5:"; the disclosure is in the S164 record.

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
    """Erasure is ONE monotonic state machine (T S161 A-1/A-2):
    scrub → seal → tombstone → hygiene. Every step before the tombstone is
    idempotent and leaves the caller's bearer alive for a retry; the ownership
    claim outlives the tombstone as the mailbox's fence; everything after the
    tombstone is hygiene whose failure cannot negate an accepted erasure."""

    def test_tombstone_failure_keeps_the_mailbox_fence(self, rdb):
        # 59424c5: the claim was released and the email scrubbed BEFORE the
        # subject tombstone, so when that final write failed nothing routed
        # the mailbox back to the sealed subject while its bearer stayed alive
        # by design — the mapping-free interval T S161 A-1 reproduced (HIGH).
        # The claim is the fence: it must still name the subject after the
        # failed tombstone, and a retry with the surviving bearer finishes.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        with patch.object(stores, "write_subject_tombstone",
                          side_effect=StoreUnavailable("marker write down")):
            result = asyncio.run(registration.process_optout(subject))
        assert result.processed is False and not _tombstoned(subject)
        # Intended first assertion: the fence survived the failed tombstone.
        claim = rdb.docs(OWNERS).get(_owner_key(VICTIM_EMAIL))
        assert claim is not None and claim["uuid"] == subject, (
            "the failed tombstone left no fence on the mailbox"
        )
        assert registration._subject_revoked(subject) is True      # seal present
        assert _bearer_alive(token)                                 # the retry credential
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)

    def test_release_failure_after_the_tombstone_is_accepted_erasure(self, rdb):
        # 59424c5: the release ran BEFORE the tombstone, so a release failure
        # returned processed=False with the bearer alive (the S162 F-03
        # contract) — the very order that, one step later, produced the A-1
        # fork. Release is now hygiene AFTER the tombstone: its failure cannot
        # negate an erasure the tombstone already made authoritative, the
        # bearer is dead because the erasure IS finished, and the stale claim
        # is left for the reclaim path the resolver already has.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)

        def boom(_doc_id):
            raise ServiceUnavailable("claim store down")

        rdb._collection_store(OWNERS)._remove = boom
        result = asyncio.run(registration.process_optout(subject))
        # Intended first assertion: the tombstone landed, so the receipt says so.
        assert result.processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"
        # The claim outlived the failed hygiene step and still names the
        # tombstoned subject: harmless, because every validation path denies
        # that subject and the resolver reclaims exactly this claim.
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == subject
        del rdb._collection_store(OWNERS)._remove
        fresh = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert fresh and fresh != subject
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == fresh
        assert not _bearer_alive(token)

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
        # 59424c5: (T S161 A-1, HIGH) the S163 version of this test interrupted
        # the erasure with a claim-RELEASE failure, a state the corrected order
        # no longer has (release now follows the tombstone); the interruption
        # that remains is a FAILED TOMBSTONE write after the seal, which leaves
        # the caller a live bearer and an expectation to retry. At 59424c5 the
        # claim had already been released and the email scrubbed, so the
        # resolver found "nothing anywhere" and minted a FRESH subject with a
        # new active account carrying the address in clear while the old bearer
        # still authorized the sealed one. Reclaiming belongs to a FINISHED
        # erasure; an unfinished one must fail closed and wait for the retry —
        # decidable only while the claim still routes the mailbox to the
        # sealed subject.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        with patch.object(stores, "write_subject_tombstone",
                          side_effect=StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(subject)).processed is False
        assert registration._subject_revoked(subject) is True       # erasure BEGUN
        assert not _tombstoned(subject)                             # but NOT finished

        # The interrupted state must not hand the address to a new identity.
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        # Intended first assertion: no fresh subject while the old bearer is admissible.
        assert resolved is None, "an unfinished erasure handed the mailbox to a fresh subject"
        assert [uuid for _, uuid, _ in _accounts(rdb, VICTIM_EMAIL)] == []
        # And the caller can still finish what they started, with the bearer
        # the interrupted erasure deliberately left alive.
        assert _bearer_alive(token)
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
            # T S161 A-3 / F-6: an ambiguous commit makes no absence claim.
            assert "could not be confirmed as saved" in body["message"]
            assert "no account" not in body["message"].lower()

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
        # 59424c5: on the receipt wording only. Under a full writes-down outage
        # the claim write fails first, so no account exists at either head and
        # the post-state assertion below passes at both. The RECEIPT no longer
        # asserts that absence (T S161 A-3 / F-6: a write exception is not
        # proof of non-commit), and the wording assertion is what fails at the
        # parent — the honest receipt must never be LESS true than the store.
        for path, email in ((EA_PATH, BRAND_NEW), (LIGHT_PATH, "second-new@example.com")):
            _writes_down(rdb, "early_adopters", "ea_registrations", OWNERS, "feedback")
            response = self._post(http, path, email)
            assert response.status_code == 503
            body = response.json()
            assert body["persisted"] is False and body["uuid"] == ""
            assert "could not be confirmed as saved" in body["message"]
            assert _accounts(rdb, email) == []  # nothing was persisted

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
        assert _accounts(rdb, None) == []   # nothing was persisted


# ── CS round 7 (T S161) · monotonic erasure, receipt truth, enumeration symmetry ─

class TestErasureIsMonotonicAndReceiptsAreTruthful:
    """T S161 attacked the gaps BETWEEN the round-6 operations and found a
    terminal ordering in which each step was correct and the sequence was not.
    The repair treats erasure as one monotonic state machine, makes every
    receipt describe post-state it can prove, and makes a new and an existing
    mailbox cross the same authorization-state failure boundary. The A-1
    fence and the post-tombstone release live with the resumability tests
    above, and the rewritten interrupted-erasure test with the seal tests;
    this class carries the rest."""

    _post = staticmethod(TestStorageOutageIsHonestAndUniform._post)
    _seed_existing = staticmethod(TestStorageOutageIsHonestAndUniform._seed_existing)

    # ── A-2 · completion and revocation depend on the right state ──────────

    @pytest.mark.parametrize("step", ["_release_claims_naming", "sweep_subject_credentials"])
    def test_a_programming_error_after_the_tombstone_cannot_negate_completion(self, rdb, step):
        # 59424c5: only StoreUnavailable was tolerated after the tombstone; any
        # other exception fell through to the outer handler and returned
        # processed=False although the authoritative marker had committed and
        # every validation path already denied the subject (T S161 F-3). The
        # claim release, which the corrected order also runs after the
        # tombstone, carries the same contract.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        target = registration if step == "_release_claims_naming" else stores
        with patch.object(target, step, side_effect=RuntimeError("a bug, not an outage")):
            result = asyncio.run(registration.process_optout(subject))
        # Intended first assertion: the erasure happened, so the receipt says so.
        assert result.processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"

    def test_an_authenticated_subject_with_no_account_row_is_still_revoked(self, rdb):
        # 59424c5: `matched` — an account document in either lane — gated the
        # seal, the tombstone, the claim sweep and the credential sweep, so a
        # bearer-valid subject whose account row was absent received
        # processed=True with nothing revoked, and a stolen credential survived
        # its holder's rights action (T S161 F-4). Revocation is authoritative
        # on the SUBJECT the caller authenticated as, not on a row being present.
        subject = "018f6b2a-7777-7abc-8def-0123456789ab"
        token = _issue_pat_for(subject)
        assert _bearer_alive(token)
        assert subject not in rdb.docs("early_adopters") and subject not in rdb.docs("ea_registrations")
        result = asyncio.run(registration.process_optout(subject))
        assert result.processed is True
        # Intended first assertion: the subject is tombstoned regardless of rows.
        assert _tombstoned(subject)
        assert not _bearer_alive(token)
        assert registration._subject_revoked(subject) is True

    def test_an_interrupted_erasure_of_a_claim_only_subject_is_not_healed(self, rdb):
        # 59424c5: found by the S164 mutation lens, not by a reviewer. The
        # interrupted-erasure tests above start from a SCRUBBED record, so the
        # resolver's refusal there is satisfied by `_adopt_verified` rejecting
        # a non-active record — which left the resolver's own "erasure in
        # progress" check, and the seal's independence from an account row,
        # unpinned (mutants M16/M27 survived the whole suite). This state has
        # neither mask: a claim names S but NO account exists in either lane
        # (claim won, record write failed — the heal branch's own state), and
        # S's erasure is interrupted after the seal. At 59424c5 an accountless
        # subject was never sealed (F-4), so the resolver HEALED a verified
        # active account for S while S's bearer was alive.
        subject = "018f6b2a-5555-7abc-8def-0123456789ab"
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(OWNERS, key, {
            "email_hash": key, "uuid": subject, "collection": "ea_registrations",
            "lane": "lightweight_v0513", "claimed_at": REGISTRATION_NOW, "verified": False,
        })
        token = _issue_pat_for(subject)
        assert _accounts(rdb, VICTIM_EMAIL) == []
        with patch.object(stores, "write_subject_tombstone",
                          side_effect=StoreUnavailable("marker write down")):
            interrupted = asyncio.run(registration.process_optout(subject))
        assert not _tombstoned(subject)

        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        # Intended first assertion: no adoption, no heal, no fresh subject.
        assert resolved is None, "an unfinished erasure handed the mailbox to a subject"
        assert _accounts(rdb, VICTIM_EMAIL) == [], "the resolver minted an account for a sealed subject"
        claim = rdb.docs(OWNERS)[key]
        assert claim["uuid"] == subject and claim["verified"] is False
        # The state the contract requires: sealed (begun), not finished, retryable.
        assert interrupted.processed is False
        assert registration._subject_revoked(subject) is True
        assert _bearer_alive(token)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert key not in rdb.docs(OWNERS)

    # ── A-1, one step further · what the author's attacker lens found (S164) ─

    def test_a_heal_racing_the_erasure_cannot_leave_an_active_row_with_the_address(self, rdb):
        # 59424c5: (S164 Lens A F1, new by effect) a claim-only subject with a
        # live bearer is healed by the verified ceremony INSIDE the erasure's
        # window — after opt-out read "no rows" and before it sealed. The
        # first pass scrubbed nothing, the tombstone landed, and an ACTIVE
        # row carrying the address for a tombstoned subject survived: the
        # receipt said PII was de-identified, both lanes answered "recorded"
        # without writing a claim, and the resolver returned None forever.
        # The parent never opened the window (its account-row gate skipped the
        # erasure) and healed afterwards, which is the same end state. The
        # erasure now seals first and re-scrubs every row of the subject after
        # the tombstone, by identifier and by uuid field.
        subject = "018f6b2a-6666-7abc-8def-0123456789ab"
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(OWNERS, key, {
            "email_hash": key, "uuid": subject, "collection": "ea_registrations",
            "lane": "lightweight_v0513", "claimed_at": REGISTRATION_NOW, "verified": False,
        })
        token = _issue_pat_for(subject)
        original_seal = stores.write_erasure_seal
        healed = {}

        def heal_then_seal(target):
            if not healed:
                healed["subject"] = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
            return original_seal(target)

        with patch.object(stores, "write_erasure_seal", side_effect=heal_then_seal):
            result = asyncio.run(registration.process_optout(subject))
        if not healed:  # a tree that never seals an accountless subject never opens the window
            healed["subject"] = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert result.processed is True
        rows = [(name, record) for name, _uuid, record in _accounts(rdb, VICTIM_EMAIL)]
        # Intended first assertion: an accepted erasure leaves no row carrying the address.
        assert rows == [], f"an accepted erasure left an active row with the address: {rows}"
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert rdb.docs("ea_registrations")[subject]["status"] == "deletion_requested"
        assert key not in rdb.docs(OWNERS)                      # released after the tombstone
        fresh = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert fresh and fresh != subject                       # the mailbox is free again

    def test_a_heal_that_commits_after_the_erasure_is_refused(self, rdb):
        # 59424c5: (S164 Lens A F1, the other ordering) the heal's checks
        # passed, a COMPLETE opt-out ran, then the heal's create landed — an
        # active row with the address for a tombstoned subject, and a claim
        # update that failed because the claim was already released. The heal
        # now reads both erasure markers through the transaction that writes
        # the record, so it refuses once the seal exists.
        subject = "018f6b2a-6667-7abc-8def-0123456789ab"
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(OWNERS, key, {
            "email_hash": key, "uuid": subject, "collection": "ea_registrations",
            "lane": "lightweight_v0513", "claimed_at": REGISTRATION_NOW, "verified": False,
        })
        token = _issue_pat_for(subject)
        ran = {"n": 0}
        original = registration._verified_record

        def erase_then_build(*args, **kwargs):
            if not ran["n"]:
                ran["n"] = 1
                assert _run_off_loop(registration.process_optout(subject)).processed is True
            return original(*args, **kwargs)

        with patch.object(registration, "_verified_record", side_effect=erase_then_build):
            resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert ran["n"] == 1, "the erasure never interleaved; the test proved nothing"
        # Intended first assertion: the late heal is refused, so no row carries the address.
        assert _accounts(rdb, VICTIM_EMAIL) == [], "a heal that committed after the erasure left an active row"
        assert resolved is None
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert key not in rdb.docs(OWNERS)

    def test_an_address_without_a_claim_is_fenced_before_it_is_scrubbed(self, rdb):
        # 59424c5: (S164 Lens A F3, pre-existing) a record carrying the address
        # but no owner claim — claim lost out of band — had its only
        # email→subject route destroyed by the scrub before the seal and the
        # tombstone; on a tombstone failure the resolver found "nothing
        # anywhere" and minted a fresh subject while this one's bearer was
        # alive: T S161 A-1's shape, one step earlier. A claim naming the
        # subject is now asserted for every address-bearing row before any
        # address is scrubbed.
        subject = "018f6b2a-9990-7abc-8def-0123456789ab"
        rdb.seed("early_adopters", subject, {
            "uuid": subject, "email": VICTIM_EMAIL, "status": "active", "email_verified": True,
        })
        token = _issue_pat_for(subject)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        with patch.object(stores, "write_subject_tombstone",
                          side_effect=StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(subject)).processed is False
        # Intended first assertion: the fence exists before the address is gone.
        claim = rdb.docs(OWNERS).get(_owner_key(VICTIM_EMAIL))
        assert claim is not None and claim["uuid"] == subject, (
            "the address was scrubbed with no claim naming its subject"
        )
        assert rdb.docs("early_adopters")[subject]["email"] == "[deletion_requested]"
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert _accounts(rdb, VICTIM_EMAIL) == [] and _bearer_alive(token)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)

    def test_a_failed_seal_leaves_the_account_untouched(self, rdb):
        # 59424c5: (S164 Lens A F2, pre-existing) the scrub ran BEFORE the
        # seal, so a seal failure left a de-identified, UNSEALED subject with a
        # live bearer; the purge the policy promises would then delete the only
        # sign that erasure was requested, and the next verified ceremony
        # healed an ACTIVE account carrying the address for it. The seal is now
        # the first write after the fence: a seal failure leaves the account
        # exactly as it was, and the retry starts over.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        with patch.object(stores, "write_erasure_seal",
                          side_effect=StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(subject)).processed is False
        # Intended first assertion: nothing was de-identified before the seal.
        assert rdb.docs("early_adopters")[subject]["email"] == VICTIM_EMAIL
        assert rdb.docs("early_adopters")[subject]["status"] == "active"
        assert not registration._subject_revoked(subject)
        assert not _tombstoned(subject) and _bearer_alive(token)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)

    def test_a_purge_after_an_interrupted_erasure_cannot_be_healed_into_an_account(self, rdb):
        # 59424c5: the other half of F2. Once the seal has landed, purging the
        # de-identified rows (the promised retention step) must not let the
        # verified ceremony heal an active account for the sealed subject —
        # the seal refuses the heal until the erasure finishes, at BOTH heads.
        # It still fails at the parent, for A-1's reason: there the claim had
        # already been released before the failed tombstone, so nothing routed
        # the purged mailbox and the resolver minted a fresh subject.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        with patch.object(stores, "write_subject_tombstone",
                          side_effect=StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(subject)).processed is False
        rdb._collection_store("early_adopters")._remove(subject)   # the promised purge
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert subject not in rdb.docs("early_adopters") and _accounts(rdb, VICTIM_EMAIL) == []
        assert _bearer_alive(token)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)

    def test_a_row_keyed_differently_from_its_uuid_field_is_still_scrubbed(self, rdb):
        # 59424c5: (S164 Lens A, LOW, pre-existing) the scrub keyed rows by
        # document id while claim release keyed by the uuid field, so a row
        # whose id differed from its uuid was never de-identified —
        # processed=True with the address in clear. Every row of the subject is
        # now scrubbed by identifier AND by uuid field.
        subject = "018f6b2a-9991-7abc-8def-0123456789ab"
        rdb.seed("early_adopters", "legacy-doc-id-89ab", {
            "uuid": subject, "email": VICTIM_EMAIL, "status": "active",
        })
        assert asyncio.run(registration.process_optout(subject)).processed is True
        # Intended first assertion: no row naming this subject still carries the address.
        assert _accounts(rdb, VICTIM_EMAIL) == []
        assert rdb.docs("early_adopters")["legacy-doc-id-89ab"]["status"] == "deletion_requested"
        assert _tombstoned(subject)

    # ── A-3 · receipts describe post-state they can prove ───────────────────

    def test_feedback_received_describes_whether_the_text_persists_anywhere(self, rdb, http):
        # 59424c5: a NEW account copied the submitted text into its own record
        # before the feedback document was attempted, so a document-write
        # failure answered feedback_received=false while the text persisted in
        # the account — and an existing address, which writes no account,
        # answered the same bytes for a different reality (T S161 F-2). The
        # text is now stored in the feedback document only: one place, one
        # truthful answer, identical for both addresses.
        text = "The CS questions were sharp."
        ok = self._post(http, EA_PATH, BRAND_NEW, feedback=text, feedback_type="general")
        assert ok.status_code == 201 and ok.json()["feedback_received"] is True
        ((_, _uuid, record),) = _accounts(rdb, BRAND_NEW)
        # Intended first assertion: the account carries no copy of the text.
        assert record.get("registration_feedback") is None
        assert [d for d in rdb.docs("feedback").values() if d.get("content") == text]
        # The document write fails: the text persists NOWHERE, and the receipt
        # says so for a new and an existing address alike.
        before = dict(rdb.docs("feedback"))
        _writes_down(rdb, "feedback")
        exist = self._post(http, EA_PATH, BRAND_NEW, feedback=text, feedback_type="general")
        new = self._post(http, EA_PATH, "third-new@example.com", feedback=text, feedback_type="general")
        assert new.status_code == exist.status_code == 201
        _same_receipt(exist, new, drop=("email_masked",))
        assert new.json()["feedback_received"] is False and exist.json()["feedback_received"] is False
        assert rdb.docs("feedback") == before
        ((_, _uuid, record),) = _accounts(rdb, "third-new@example.com")
        assert record.get("registration_feedback") is None and text not in str(record)

    def test_a_client_construction_failure_is_a_failure_status_in_both_lanes(self, rdb, http):
        # 59424c5: when no Firestore client could be constructed both bodies
        # truthfully said persisted=false, but the EA handler emitted 201 and
        # the lightweight handler 200 — a success receipt for an unsaved
        # registration to any client that reads status (T S161 F-5).
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            ea = http.post(EA_PATH, json=_ea_payload(BRAND_NEW))
            light = http.post(LIGHT_PATH, json={"consent": True, "email": BRAND_NEW})
            anon = http.post(LIGHT_PATH, json={"consent": True})
        # Intended first assertion: transport agrees with the body.
        assert ea.status_code == 503
        assert light.status_code == 503 and anon.status_code == 503
        for response in (ea, light, anon):
            assert response.json()["persisted"] is False
            assert response.headers.get("retry-after") == "60"
            assert response.headers.get("cache-control") == "no-store"

    def test_an_ambiguous_account_commit_makes_no_absence_claim(self, rdb, http):
        # 59424c5: the mid-request outage receipt said "no account was created"
        # after an account-write exception — but the installed client sends
        # writes through a Commit RPC, and a server commit whose acknowledgement
        # is lost raises exactly like a rejected one, so the exception proves
        # nothing about absence (T S161 F-6). The receipt now says only what is
        # known: the request could not be confirmed as saved.
        _writes_down(rdb, "early_adopters", "ea_registrations")  # the claim lands; the account write raises
        for path, email in ((EA_PATH, BRAND_NEW), (LIGHT_PATH, "fourth-new@example.com")):
            response = self._post(http, path, email)
            assert response.status_code == 503
            assert _owner_key(email) in rdb.docs(OWNERS)  # the claim landed; only the account write raised
            body = response.json()
            # Intended first assertion: no unprovable absence claim.
            assert "no account" not in body["message"].lower()
            assert "could not be confirmed as saved" in body["message"]
            assert body["persisted"] is False and body["uuid"] == ""

    # ── A-4 · one authorization-state failure boundary for new and existing ─

    def test_a_revocation_marker_read_outage_is_one_receipt_in_both_lanes(self, rdb, http):
        # 59424c5: an existing address re-asserted its claim inside a
        # transaction that READ the subject's erasure markers, while a new
        # address used a bare atomic create with no such read — so when only
        # the revocation-marker store failed, an existing address got 503 and
        # a new one succeeded, in both lanes: an email-existence oracle under a
        # selective outage (T S161 F-8 / A-4). A fresh identifier's claim now
        # performs the same marker read before its create.
        self._seed_existing(http, EA_PATH)
        self._seed_existing(http, LIGHT_PATH)
        restore = _reads_down(rdb, stores._c(stores._BASE_TOMBSTONES))
        try:
            e_exist = self._post(http, EA_PATH, EXISTING)
            e_new = self._post(http, EA_PATH, BRAND_NEW)
            l_exist = self._post(http, LIGHT_PATH, EXISTING)
            l_new = self._post(http, LIGHT_PATH, "fifth-new@example.com")
        finally:
            restore()
        # Intended first assertion: the new address fails exactly as the existing one.
        assert e_new.status_code == e_exist.status_code == 503
        assert l_new.status_code == l_exist.status_code == 503
        _same_receipt(e_exist, e_new, drop=("email_masked",))
        _same_receipt(l_exist, l_new)
        # And nothing was minted behind the outage.
        assert _owner_key(BRAND_NEW) not in rdb.docs(OWNERS)
        assert _accounts(rdb, BRAND_NEW) == [] and _accounts(rdb, "fifth-new@example.com") == []

    def test_a_fresh_identifier_reads_the_same_markers_an_existing_one_does(self, rdb, http):
        # 59424c5: the mechanism behind the receipt above, pinned so a later
        # change cannot keep that receipt green by accident): registering a
        # NEW address reads BOTH erasure markers for the fresh identifier —
        # the reads whose failure the existing path is exposed to — and still
        # performs exactly ONE owners write, the atomic create.
        marks = rdb._collection_store(stores._c(stores._BASE_TOMBSTONES))
        reads = []

        class _Counting(dict):
            def get(self, key, default=None):
                reads.append(str(key))
                return dict.get(self, key, default)

        marks._docs = _Counting(marks._docs)
        writes = _count_owner_writes(rdb)
        assert self._post(http, EA_PATH, BRAND_NEW).status_code == 201
        # Intended first assertion: both marker reads happened.
        assert any(k.startswith("erasure_") for k in reads) and any(k.startswith("subject_") for k in reads)
        assert writes["n"] == 1
        assert rdb.docs(OWNERS)[_owner_key(BRAND_NEW)]["uuid"]

    def test_a_fresh_identifier_under_erasure_is_refused_not_re_issued(self, rdb, http):
        # 59424c5: the marker read is not decorative. Should a fresh
        # identifier's marker ever be present, the claim is refused and no
        # account is created — the address is neither disclosed nor handed to
        # a subject under erasure (fail closed; T S161 A-4's second clause).
        fresh = "018f6b2a-8888-7abc-8def-0123456789ab"
        rdb.seed(stores._c(stores._BASE_TOMBSTONES), f"subject_{fresh}", {"kind": "subject", "key": fresh})
        with patch.object(registration, "generate_ea_uuid", return_value=fresh):
            response = self._post(http, EA_PATH, BRAND_NEW)
        assert response.status_code == 201 and response.json()["uuid"] == ""
        # Intended first assertion: no claim was written for the erased identifier.
        assert _owner_key(BRAND_NEW) not in rdb.docs(OWNERS)
        assert _accounts(rdb, BRAND_NEW) == []
