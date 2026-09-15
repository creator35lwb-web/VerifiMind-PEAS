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
"59424c5:" for the round-7 one, "0b33ee9:" for the round-8 one,
"aab9995:" for the round-9 one, "72a92ae:" for the round-10 residual). For a
PARAMETRIZED test the label is per-CASE: where only some parameters
discriminate, the comment names which ones and that round's paragraph counts
them, so a label on the function is never a claim about every case of it. The
fake is copied into the old tree with the test, so only the source differs — and
a test that must fail the AUTHORITATIVE tombstone write patches whichever
seam the tree under test has (``_tombstone_write_fails``), so it
discriminates on behaviour at every head instead of on a missing symbol.

CS round 8 (2026-09-10, T S165) then found that the S164 repair's own
additions did not cover each other — closed by the round-9 repair here:

R8-A1  the FENCE saw only the row keyed by the subject identifier while the
       SCRUB (widened for the docid LOW) also reached rows found by ``uuid``
       field, so a claimless row of that kind lost its only mailbox route
       before any anchor existed and a tombstone failure forked the mailbox
       while the old bearer was alive; and "a claim exists" was taken for
       "this mailbox is fenced to the erasing subject" even when the claim
       named another subject. Fence and scrub now share ONE selector, and
       the fence reports which case it found: created or touched for this
       subject, or anchored to another live owner (left alone, T S159 F-02);
       a fence that cannot be written stops the erasure before the seal.
R8-A2  a feedback write whose acknowledgement was lost was reported as
       ``feedback_received: false`` while the text persisted, and a retry
       could duplicate it. The document id is now deterministic per
       (mailbox, text) with create-if-absent, so an identical resubmission
       — whenever it arrives — is the same document; a raised write is
       reported as unknown (``null``), never as confirmed absence, and the
       receipt never reads the store back to resolve it (that would tell a
       submitter, during an outage, whether this mailbox already sent this
       text); the store is read back for the log only.
R8-A3  a successful erasure could leave a claim naming the tombstoned
       subject when its release failed after the tombstone — runtime-safe,
       but contradicting the governing rule. Tombstone and release now land
       in ONE commit: a release failure fails the tombstone with it and the
       retry finishes both. The fake's commit is all-or-nothing to match.

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
F-6) in place of the parent's "no account was created". Against `0b33ee9`, 12 of the 64 fail, ALL on a behavioural
assertion and none by symbol absence: the atomic tombstone-plus-release
commit (the release-failure control and the stale off-row claim), the
uuid-field fence in both lanes, the borrowed anchor kept until the
tombstone, and seven feedback receipts (the lost acknowledgement, the
unconfirmable outcome, the raised write reported unknown in the S163 and
S164 outage controls and in the oracle pin, the confirming-read programming
error, the retry across midnight). Three round-9 pins pass at both heads (a
duplicate opt-out of a finished erasure; a fence that cannot be written; the
round-5 ABA control, re-armed at the commit), and the fake-atomicity pin
discriminates the FAKE, not the source — it fails against the 0b33ee9 fake
and passes with the repaired fake copied in, which is the old-head protocol. A symbol-absence failure is
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

Round 9 (2026-09-12, T S167) accepted A-2 as closed and found that a
foreign claim was taken as an anchor whatever its owner's lifecycle, that the
terminal commit's set was not closed over a late fence, and that the success
receipt overstated deferred-PII post-state — closed by the round-10 repair
here, whose own lenses then found the first cut's carrier adoption writing
without reading the carrier's markers in its transaction (the same class the
round-6 rule R6-01 names), and its receipt read unpinned in both directions.
Against `aab9995`, 24 of the 99 fail (74 pass; the real-transaction-adapter
contract test skips where the method is absent), ALL on a behavioural
assertion and none by symbol absence: the stale owner's claim re-pointed as
the fence (both lanes); the resolver adopting a live carrier instead of
minting (both lanes); a sealed carrier refused (both lanes); a uuid-less
carrier refused; a seal, or a status change, landing inside the adoption
window; an unadoptable carrier refused without moving the claim; any sealed
candidate refusing whatever the lane order; the late fence released by the
same commit (both lanes) and a fence landing inside the commit window
conflicting it (both lanes); the stray claim at an off-row key; the terminal
set and one write per claim; the pending receipt (both lanes), pending
decided over every deferred row, an unconfirmable row pending, and the state
field on every HTTP surface; a claim with no owner identifier fenced (both
lanes). Ten pins pass at both heads: the sealed owner's claim kept (both
lanes); a tombstoned carrier never revived (both lanes); the stale owner's
own row; the lost reclaim race; a deferred row whose hygiene succeeds (both
lanes); the complete receipt and its scope; the fake's read-set test. Twenty
per-finding mutants were re-run at THAT head after both lenses (one per
finding, sha256-verified restore): nineteen killed; the one survivor drops
the identity exclusion of the stale owner's own row from the carrier scan,
which is equivalent under that branch's precondition (the owner is
tombstoned) and is kept as a statement of intent.
Round 10 (2026-09-12, T S168) accepted the round-9 repairs R9-01, R9-02 and
R9-03, and found two set-level SNAPSHOTS inside its own contract: the carrier
scan bound only the SELECTED candidate in the adoption transaction, and the
terminal set was built from current rows and a current query, so an older
request's pre-scrub row snapshot could fence outside it. The round-10 residual
closes both — the WHOLE carrier decision, membership included, moves inside the
adopting transaction, and every fence records a per-subject index the terminal
commit reads first. Against `72a92ae`, 13 of the 122 cases the file now holds
fail (109 pass, 0 skip), ALL on a behavioural or state assertion and none by
symbol absence: a seal on the NON-SELECTED carrier inside the adoption window
(in the lane order where the parent selected the other row; the reverse order is
a pin there, because the parent re-read the selected carrier anyway); two
verified carriers refused (both orders); the verified carrier selected over an
unverified first-lane row (the order the parent got wrong); the SELECTED
candidate's erasure finishing inside the window, which the parent answers by
refusing the whole request instead of deciding again; a carrier appearing
between the parent's scan and its transaction; EVERY address-bearing row of the
adopted subject sanitized while the claim names the already-proven row's lane;
an older fence from a pre-scrub snapshot inside the terminal window (both
lanes); that same fence through the stale-owner and the ownerless reclaim
branches; a fence landing before the terminal read, whose index the parent never
writes; and the terminal primitive releasing a claim from the index ALONE, with
no caller seed and its own query silenced. Ten cases pass at both heads and say
so: the two reverse lane orders; a non-selected candidate whose erasure FINISHES
inside the window (ignored, not refused, with a witness that it did); one
subject with rows in both lanes as ONE candidate rather than a conflict with
itself; an unproven, unadoptable candidate that does NOT deny the mailbox to an
adoptable one; a live subject whose own row cannot be adopted refusing rather
than being out-ranked (both shapes, for different reasons — see the test); the
adopted row sanitized and not merely claimed; a proven row counting as an
identity whatever its account status; and a fence after the tombstone writing
neither claim nor index. Three of those pins exist because a mutant, not the
parent, discriminates them, and two because a lens found this repair's own
FIRST CUT wrong: it quantified the conflict over ROWS (so one subject with rows
in both lanes conflicted with itself) and it widened the adoptability refusal to
every live candidate (so an unproven, inactive second row denied the mailbox
permanently, which `72a92ae` does not).

Twenty-eight per-finding mutants were run on this head after three adversarial
passes (one per repair element, sha256-verified restore between each):
twenty-six killed. The two survivors are equivalent under a stated precondition
and are disclosed rather than papered over — emptying the caller's current-row
SEED inside the terminal primitive changes nothing the index and the query do
not already cover (it is kept deliberately, as closure over any future claim
writer that does not consult the seal), and counting a row with NO identifier as
already proven only moves the decision further closed, since such a subject has
no adoptable row. What the lenses found and this head does NOT change is
recorded in the S169 Hub record and routed to T: the three refusals reach the
user as the same transient 503 page a real outage produces and never name the
rights channel (`oauth/endpoints.py`, a surface this repair does not touch);
the conflict question is quantified over proven ROWS rather than over credential
state; a claim naming a subject whose row id differs from its uuid lets the next
ceremony heal a duplicate row (identical at both heads); and the membership
residual covers a row UPDATED into the address as well as one created, both
routed with F-9.
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

from .oauth_fakes import FakeFirestore, FakeTransaction
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


def _tombstone_write_fails(exc):
    """Fail the AUTHORITATIVE tombstone write at whichever seam the tree under
    test has — the atomic tombstone-plus-release commit (round-9 repair) or the
    plain tombstone write (older heads) — so a test discriminates on the
    behaviour that follows the failure, never on a missing symbol."""
    seam = ("tombstone_subject_releasing_claims"
            if hasattr(stores, "tombstone_subject_releasing_claims") else "write_subject_tombstone")
    return patch.object(stores, seam, side_effect=exc)


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

        # The barrier is armed AFTER the seal, so the next transaction is the
        # one that releases the claim — the tombstone-plus-release commit since
        # round 9, the release transaction before it. Armed at the start it
        # fired in the FENCE transaction and this control stopped exercising
        # the in-commit re-check (S165 Lens B, M7).
        original_seal = stores.write_erasure_seal

        def seal_then_arm(target):
            original_seal(target)
            rdb._next_barrier = repoint_inside_the_commit_window

        with patch.object(stores, "write_erasure_seal", side_effect=seal_then_arm):
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
    """Erasure is ONE monotonic state machine (T S161 A-1/A-2; T S165 A-1/A-3):
    fence → seal → scrub → tombstone-plus-release in one commit → hygiene.
    Every step before the commit is idempotent and leaves the caller's bearer
    alive for a retry; the ownership claim is the mailbox's fence and is
    released in the same commit that makes the revocation authoritative;
    everything after that commit is hygiene whose failure cannot negate an
    accepted erasure."""

    def test_tombstone_failure_keeps_the_mailbox_fence(self, rdb):
        # 59424c5: the claim was released and the email scrubbed BEFORE the
        # subject tombstone, so when that final write failed nothing routed
        # the mailbox back to the sealed subject while its bearer stayed alive
        # by design — the mapping-free interval T S161 A-1 reproduced (HIGH).
        # The claim is the fence: it must still name the subject after the
        # failed tombstone, and a retry with the surviving bearer finishes.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
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

    def test_a_claim_release_failure_fails_the_tombstone_commit_with_it(self, rdb):
        # 0b33ee9: (T S165 A-3) the S164 version of this control blessed a
        # claim-release failure AFTER the tombstone as hygiene debt — processed
        # True with a claim still naming the tombstoned subject. Runtime-safe
        # (the tombstone denies the bearer, the resolver reclaims the claim),
        # but it contradicted the governing rule that no claim naming an
        # erased subject survives a success. Tombstone and release now land in
        # ONE commit: a release failure fails the tombstone with it, nothing
        # lands, the fence and the bearer stay, and the retry finishes both.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        owners = rdb._collection_store(OWNERS)
        armed = {"on": False}
        real_gate = owners._write_gate
        original_seal = stores.write_erasure_seal

        def gate():
            if armed["on"]:
                raise ServiceUnavailable("claim store down")
            return real_gate()

        def seal_then_arm(target):  # the owners store fails only AFTER the fence was written
            original_seal(target)
            armed["on"] = True

        owners._write_gate = gate
        with patch.object(stores, "write_erasure_seal", side_effect=seal_then_arm):
            result = asyncio.run(registration.process_optout(subject))
        # Intended first assertion: nothing landed — a failed release fails the tombstone.
        assert result.processed is False and not _tombstoned(subject), (
            "a claim-release failure left the erasure reported as, or made, authoritative"
        )
        assert rdb.docs(OWNERS)[_owner_key(VICTIM_EMAIL)]["uuid"] == subject  # the fence stands
        assert _bearer_alive(token)                                           # the retry credential
        armed["on"] = False
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)               # released in the same commit

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
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
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
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
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
        # Different text than the seeding post: the feedback document id is
        # deterministic per (mailbox, text, day) since round 9, so resubmitting
        # the SAME text would truthfully read back as stored.
        feedback = dict(feedback="The CS questions were sharper still.", feedback_type="general")
        exist = self._post(http, EA_PATH, EXISTING, **feedback)
        new = self._post(http, EA_PATH, BRAND_NEW, **feedback)
        # Intended first assertion: the registration succeeded, so say so.
        assert new.status_code == exist.status_code == 201
        _same_receipt(exist, new, drop=("email_masked",))
        # Truthful about the part that failed, for BOTH addresses alike: the
        # write raised, so the outcome is UNKNOWN (round 9) — never a confirmed
        # absence, and never read back into the receipt.
        assert new.json()["feedback_received"] is None
        assert exist.json()["feedback_received"] is None
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
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
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
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
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
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
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
        # Different text than the successful post: the document id is
        # deterministic per (mailbox, text, day) since round 9, so the SAME
        # text would truthfully read back as stored.
        later = "The CS questions were sharper still."
        exist = self._post(http, EA_PATH, BRAND_NEW, feedback=later, feedback_type="general")
        new = self._post(http, EA_PATH, "third-new@example.com", feedback=later, feedback_type="general")
        assert new.status_code == exist.status_code == 201
        _same_receipt(exist, new, drop=("email_masked",))
        assert new.json()["feedback_received"] is None and exist.json()["feedback_received"] is None  # raised ⇒ unknown (round 9)
        assert rdb.docs("feedback") == before
        ((_, _uuid, record),) = _accounts(rdb, "third-new@example.com")
        assert record.get("registration_feedback") is None and later not in str(record)

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


# ── CS round 8 (T S165) · fence covers scrub; erasure commits atomically; feedback receipts confirm ─

class TestFenceCoversScrubAndErasureCommitsAtomically:
    """T S165 found that the S164 repair's own additions did not cover each
    other: the fence quantified over fewer rows than the scrub, "a claim
    exists" was mistaken for "fenced to this subject", a lost feedback
    acknowledgement was reported as absence, and a success could leave a claim
    naming the erased subject. Tests labelled ``0b33ee9:`` discriminate that
    head; the pins pass at both heads; the harness pin discriminates the fake.
    The S165 lenses added the borrowed-anchor deferral, the tombstone-aware
    fence, the receipt-oracle closure and the in-commit ABA pin."""

    _post = staticmethod(TestStorageOutageIsHonestAndUniform._post)

    # ── A-1 · the precondition selector covers the destructive selector ─────

    @pytest.mark.parametrize("collection", ["early_adopters", "ea_registrations"])
    def test_a_row_found_by_uuid_field_is_fenced_before_it_is_scrubbed(self, rdb, collection):
        # 0b33ee9: (T S165 A-1, HIGH) the fence read only the row keyed by the
        # subject identifier while the scrub — widened for the docid LOW —
        # also reached rows found by ``uuid`` field. A claimless row of that
        # kind lost its only mailbox route before any anchor existed, and a
        # tombstone failure let a verified ceremony mint a fresh subject while
        # this subject's bearer was alive. Fence and scrub now share ONE
        # selector, in both lanes.
        subject = "018f6b2a-aaa1-7abc-8def-0123456789ab"
        rdb.seed(collection, "legacy-doc-id-aaa1", {
            "uuid": subject, "email": VICTIM_EMAIL, "status": "active",
        })
        token = _issue_pat_for(subject)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(subject)).processed is False
        # Intended first assertion: the address was fenced to the erasing subject before it was scrubbed.
        claim = rdb.docs(OWNERS).get(_owner_key(VICTIM_EMAIL))
        assert claim is not None and claim["uuid"] == subject, (
            "a row found by uuid field was scrubbed with no fence"
        )
        assert rdb.docs(collection)["legacy-doc-id-aaa1"]["email"] == "[deletion_requested]"
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert _accounts(rdb, VICTIM_EMAIL) == [] and _bearer_alive(token)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)

    def test_an_address_owned_by_another_subject_keeps_its_route_until_the_tombstone(self, rdb):
        # 0b33ee9: (S165 Lens A, the borrowed anchor) the fence must never
        # mistake "a claim exists" for "fenced to the erasing subject" (T S165
        # A-1's related weakness). An address whose claim names ANOTHER
        # subject is left to that owner (T S159 F-02) — but that owner's anchor
        # has its own lifecycle: once the owner finished its own erasure the
        # mailbox had no claim, this subject's row had already been scrubbed,
        # and the resolver minted a FRESH subject while this subject's bearer
        # was still admissible. Such a row now keeps its address until this
        # subject's tombstone and is de-identified by the hygiene pass after
        # it; the other owner's claim is not written at all.
        other = "018f6b2a-bbb2-7abc-8def-0123456789ab"
        subject = "018f6b2a-bbb3-7abc-8def-0123456789ab"
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", other, {
            "uuid": other, "email": VICTIM_EMAIL, "status": "active", "email_verified": True,
        })
        seeded = {"uuid": other, "collection": "early_adopters", "verified": True}
        rdb.seed(OWNERS, key, dict(seeded))
        rdb.seed("ea_registrations", subject, {"uuid": subject, "email": VICTIM_EMAIL, "status": "active"})
        token = _issue_pat_for(subject)
        other_token = _issue_pat_for(other)
        writes = _count_owner_writes(rdb)
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(subject)).processed is False
        # Intended first assertion: the row keeps its address while the tombstone is pending.
        assert rdb.docs("ea_registrations")[subject]["email"] == VICTIM_EMAIL, (
            "an address anchored to another subject was scrubbed before this subject's tombstone"
        )
        assert rdb.docs(OWNERS)[key] == seeded and writes["n"] == 0            # the owner's claim: not even touched
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == other      # the owner, not a fresh subject
        # The owner finishes its own erasure: its claim goes; the mailbox must
        # still not look free, because this subject's bearer is alive.
        assert asyncio.run(registration.process_optout(other)).processed is True
        assert _tombstoned(other) and not _bearer_alive(other_token) and key not in rdb.docs(OWNERS)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, (
            "the borrowed anchor vanished and the mailbox was handed to a fresh subject"
        )
        assert _accounts(rdb, VICTIM_EMAIL) != [] and _bearer_alive(token)      # the route survived
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and not _bearer_alive(token)
        assert rdb.docs("ea_registrations")[subject]["email"] == "[deletion_requested]"  # hygiene scrubbed it

    # ── A-2 · a raised feedback write is confirmed, never inferred ──────────

    def test_a_lost_feedback_acknowledgement_is_not_denied_and_the_retry_confirms_it(self, rdb, http):
        # 0b33ee9: (T S165 A-2) `feedback_received` became false whenever the
        # write raised — but a commit whose acknowledgement was lost raises
        # exactly like a rejected one, so the receipt denied text that
        # persisted, and a retry, minting a fresh document id, could duplicate
        # it. The document id is now deterministic per submission with
        # create-if-absent, and a raised write is CONFIRMED by reading it back.
        text = "Lost the acknowledgement, kept the text."
        feedback = rdb._collection_store("feedback")
        real_apply = feedback._apply_write
        lose = {"on": True}

        def apply_then_lose_ack(doc_id, data):
            real_apply(doc_id, data)                      # the commit lands…
            if lose["on"]:
                raise ServiceUnavailable("acknowledgement lost")  # …and the client never hears

        feedback._apply_write = apply_then_lose_ack
        new = self._post(http, EA_PATH, BRAND_NEW, feedback=text, feedback_type="general")
        assert new.status_code == 201
        # Intended first assertion: the text persisted, and the receipt does not deny it.
        assert new.json()["feedback_received"] is None, "a lost acknowledgement was reported as absence"
        assert len([d for d in rdb.docs("feedback").values() if d.get("content") == text]) == 1
        # The same submission again, once the store answers: idempotent — the
        # earlier document is found, no duplicate, and the receipt is True.
        lose["on"] = False
        retry = self._post(http, EA_PATH, BRAND_NEW, feedback=text, feedback_type="general")
        assert retry.status_code == 201 and retry.json()["feedback_received"] is True
        assert len([d for d in rdb.docs("feedback").values() if d.get("content") == text]) == 1
        feedback._apply_write = real_apply

    def test_an_unconfirmable_feedback_commit_is_reported_unknown_not_absent(self, rdb, http):
        # 0b33ee9: when the write raised AND the confirming read failed, the
        # receipt still said false — an absence the mechanism could not prove.
        # Unknown is now reported as unknown (null), never as confirmed absence.
        _writes_down(rdb, "feedback")
        restore = _reads_down(rdb, "feedback")
        try:
            response = self._post(http, EA_PATH, BRAND_NEW, feedback="Unconfirmable.", feedback_type="general")
        finally:
            restore()
        assert response.status_code == 201
        # Intended first assertion: unknown is not reported as absence.
        assert response.json()["feedback_received"] is None

    def test_a_raised_feedback_write_is_unknown_regardless_of_what_the_store_holds(self, rdb, http):
        # 0b33ee9: (S165 Lens A) the round-9 draft confirmed a raised write by
        # reading the deterministic document back INTO THE RECEIPT, so during a
        # feedback write outage a submitter learned whether this mailbox had
        # already sent this exact text (True) or not (False) — a guess-
        # confirmation oracle. A raised write is now reported unknown for
        # everyone; the store is read back for the log only.
        text = "Guess me."
        assert self._post(http, EA_PATH, EXISTING, feedback=text, feedback_type="general").status_code == 201
        _writes_down(rdb, "feedback")
        prior = self._post(http, EA_PATH, EXISTING, feedback=text, feedback_type="general")      # the store holds it
        fresh = self._post(http, EA_PATH, BRAND_NEW, feedback=text, feedback_type="general")     # it does not
        assert prior.status_code == fresh.status_code == 201
        # Intended first assertion: the receipt does not branch on what the store holds.
        assert prior.json()["feedback_received"] is None and fresh.json()["feedback_received"] is None
        _same_receipt(prior, fresh, drop=("email_masked",))
        assert len([d for d in rdb.docs("feedback").values() if d.get("content") == text]) == 1  # nothing new landed

    def test_a_confirming_read_programming_error_still_surfaces(self, rdb, http):
        # 0b33ee9: the log-only read after a raised feedback write classifies
        # its own exception on the node: ``is_backend_failure`` walks
        # ``__context__`` and would inherit the write's backend cause, turning
        # a programming error in the read into a quiet "unknown" (S165 Lens
        # A). A KeyError there must surface as the 500 a bug earns — not a 201.
        feedback = rdb._collection_store("feedback")
        _writes_down(rdb, "feedback")

        class _BuggyRead(dict):
            def get(self, key, default=None):
                raise KeyError("a bug in the read, not an outage")

        original = feedback._docs
        feedback._docs = _BuggyRead(original)
        try:
            response = self._post(http, EA_PATH, BRAND_NEW, feedback="Bug.", feedback_type="general")
        finally:
            feedback._docs = original
        # Intended first assertion: the bug surfaced instead of hiding behind the outage.
        assert response.status_code == 500

    def test_a_duplicate_opt_out_writes_no_fence_for_a_finished_erasure(self, rdb):
        # pin (S165 Lens A): a fence that reads no marker lets a duplicate
        # opt-out, whose rows were read before the first one finished,
        # re-create a claim naming the TOMBSTONED subject after the first
        # one's success. The duplicate's own commit would release it again —
        # unless that commit fails, and then a claim naming an erased subject
        # survives and absorbs later registrations as "owned" until a
        # ceremony reclaims the mailbox. The fence now reads the subject
        # tombstone through its own transaction and writes nothing for a
        # finished erasure; the first erasure's success stands either way.
        subject = _register_and_verify(rdb)
        key = _owner_key(VICTIM_EMAIL)
        fence_seam = ("_fence_mailbox_for_erasure" if hasattr(registration, "_fence_mailbox_for_erasure")
                      else "_assert_claim_for_existing_subject")
        commit_seam = ("tombstone_subject_releasing_claims"
                       if hasattr(stores, "tombstone_subject_releasing_claims") else "write_subject_tombstone")
        original_fence, original_commit = getattr(registration, fence_seam), getattr(stores, commit_seam)
        calls = {"fence": 0, "commit": 0}

        def first_erasure_completes_then_fence(*args, **kwargs):
            if not calls["fence"]:
                calls["fence"] = 1
                assert _run_off_loop(registration.process_optout(subject)).processed is True
            return original_fence(*args, **kwargs)

        def the_duplicates_own_commit_fails(*args, **kwargs):
            calls["commit"] += 1
            if calls["commit"] > 1:
                raise StoreUnavailable("marker write down")
            return original_commit(*args, **kwargs)

        with patch.object(registration, fence_seam, side_effect=first_erasure_completes_then_fence), \
                patch.object(stores, commit_seam, side_effect=the_duplicates_own_commit_fails):
            second = asyncio.run(registration.process_optout(subject))
        assert calls == {"fence": 1, "commit": 2}, "the interleaving never happened; the test proved nothing"
        assert _tombstoned(subject)                                              # the first erasure stands
        assert second.processed is False                                         # the duplicate's own commit failed
        # Intended first assertion: no claim naming the tombstoned subject survives.
        claim = rdb.docs(OWNERS).get(key)
        assert claim is None or claim.get("uuid") != subject, "a duplicate opt-out re-created a claim for a finished erasure"
        assert asyncio.run(registration.process_optout(subject)).processed is True   # the retry, once the store answers

    def test_a_fence_that_cannot_be_written_stops_before_the_seal(self, rdb):
        # pin (S165 Lens B, M18/M32): fence-before-seal and fence-before-scrub
        # were unpinned — the ordering held only by construction. An owners
        # write outage now proves it: nothing is sealed, nothing is scrubbed,
        # the bearer is alive, and the retry finishes.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        owners = rdb._collection_store(OWNERS)
        real_gate = owners._write_gate
        _writes_down(rdb, OWNERS)
        assert asyncio.run(registration.process_optout(subject)).processed is False
        # Intended first assertion: nothing was sealed or de-identified.
        assert not registration._subject_revoked(subject)
        assert rdb.docs("early_adopters")[subject]["email"] == VICTIM_EMAIL
        assert not _tombstoned(subject) and _bearer_alive(token)
        owners._write_gate = real_gate
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _tombstoned(subject) and _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)

    def test_a_stale_claim_on_no_current_row_is_released_by_the_commit(self, rdb):
        # 0b33ee9: (S165 Lens B, M26) the commit released the claims found by
        # the claims' OWN uuid field, not the addresses on the subject's rows;
        # a claim naming this subject for an address no current row carries
        # (the round-5 F-03 class: the row already scrubbed, the claim left
        # behind) must still go in the same commit. With the hygiene release
        # disabled, only the commit can release it.
        subject = "018f6b2a-ccc4-7abc-8def-0123456789ab"
        stale_key = _owner_key("stale-address@example.com")
        rdb.seed("early_adopters", subject, {
            "uuid": subject, "email": "[deletion_requested]", "status": "deletion_requested",
        })
        rdb.seed(OWNERS, stale_key, {"uuid": subject, "collection": "early_adopters", "verified": True})
        with patch.object(registration, "_release_claims_naming", return_value=0):
            assert asyncio.run(registration.process_optout(subject)).processed is True
        # Intended first assertion: success entails no surviving claim naming the subject.
        assert stale_key not in rdb.docs(OWNERS), "a stale claim naming the erased subject survived a success"
        assert _tombstoned(subject)

    def test_a_lost_acknowledgement_retry_across_midnight_is_still_idempotent(self, rdb, http):
        # 0b33ee9: (S165 Lens A) the round-9 draft keyed the deterministic
        # feedback id on the UTC day, so the retry of a lost-acknowledgement
        # write that arrived after midnight was a NEW document — the duplicate
        # A-2 forbids, one day late. The id now carries no time component.
        from datetime import datetime, timedelta, timezone

        text = "Late retry."
        feedback = rdb._collection_store("feedback")
        real_apply = feedback._apply_write
        lose = {"on": True}

        def apply_then_lose_ack(doc_id, data):
            real_apply(doc_id, data)
            if lose["on"]:
                raise ServiceUnavailable("acknowledgement lost")

        feedback._apply_write = apply_then_lose_ack
        try:
            first = self._post(http, EA_PATH, EXISTING, feedback=text, feedback_type="general")
            assert first.status_code == 201 and first.json()["feedback_received"] is None
            lose["on"] = False
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            with patch.object(registration, "_now_iso", return_value=tomorrow):
                retry = self._post(http, EA_PATH, EXISTING, feedback=text, feedback_type="general")
        finally:
            feedback._apply_write = real_apply
        assert retry.status_code == 201 and retry.json()["feedback_received"] is True
        # Intended first assertion: one document, not one per day.
        assert len([d for d in rdb.docs("feedback").values() if d.get("content") == text]) == 1

    # ── A-3 · the fake commits all-or-nothing, like the one Commit RPC ──────

    def test_a_transaction_commit_is_all_or_nothing(self, rdb):
        # harness pin (T S161 F-9 / T S165): the 0b33ee9 FAKE applied a
        # transaction's writes one by one, so a later write's gate failure left
        # earlier writes persisted — the half-landed state the real single
        # Commit RPC cannot produce, and exactly what the tombstone-plus-release
        # commit must never do. This discriminates the fake, not the source:
        # it passes at both heads once the repaired oauth_fakes.py is copied in
        # (the old-head protocol), and fails against the 0b33ee9 fake.
        _writes_down(rdb, "b_store")

        def _txn(txn):
            txn.set("a_store", "a", {"v": 1})
            txn.set("b_store", "b", {"v": 1})
            return True

        with pytest.raises(StoreUnavailable):
            stores.run_transaction(_txn)
        # Intended first assertion: the first write did not land without the second.
        assert "a" not in rdb.docs("a_store")
        assert "b" not in rdb.docs("b_store")


# ═══════════════════════════════════════════════════════════════════════════
# CS round 9 (T S167) — an anchor is valid only while its owner's lifecycle
# keeps it non-reclaimable; a terminal commit's set must be closed; a receipt
# must separate revocation truth from de-identification truth.
# ═══════════════════════════════════════════════════════════════════════════

class TestAnchorsHaveLifecyclesAndCommitsCloseTheirSets:
    """CS round 9 at `aab9995` (T S167 R9-01/R9-02/R9-03). R9-01: a claim
    naming ANOTHER subject was taken as an anchor whether that owner was live
    or already tombstoned; a tombstoned owner's claim is stale by the
    resolver's own rules, so after this subject's tombstone commit failed the
    resolver replaced it with a FRESH subject while this subject's row still
    carried the address and its bearer was admissible. R9-02: the terminal
    commit deleted only the claim keys snapshotted OUTSIDE it, so a duplicate
    erasure's fence committed after the snapshot survived a success when the
    hygiene sweep was unavailable. R9-03: a row deferred behind another
    subject's claim is de-identified only by post-tombstone hygiene, and when
    that failed the receipt still said the PII "has been de-identified".
    Tests labelled ``aab9995:`` fail at that head on the named assertion;
    pins pass at both heads; the measured differential and the mutation
    receipts are in the module header (round-9 paragraph)."""

    LANES = ("early_adopters", "ea_registrations")
    OTHER = "018f6b2a-bbb2-7abc-8def-0123456789ab"
    SUBJECT = "018f6b2a-bbb3-7abc-8def-0123456789ab"

    @staticmethod
    def _row(rdb, lane, subject):
        rdb.seed(lane, subject, {
            "uuid": subject, "email": VICTIM_EMAIL, "status": "active", "email_verified": True,
        })

    # ── R9-01 · the foreign anchor's lifecycle ──────────────────────────────

    @pytest.mark.parametrize("lane", LANES)
    def test_a_claim_naming_a_tombstoned_owner_becomes_this_subjects_fence(self, rdb, lane):
        # aab9995: (T S167 R9-01, HIGH) the fence read only THIS subject's
        # tombstone and took any foreign claim as an anchor. A claim whose
        # owner is already tombstoned is stale — the verified resolver would
        # reclaim it to a fresh subject — so while this subject's erasure was
        # interrupted after its seal, a ceremony for the mailbox minted a fresh
        # subject and a second account carrying the address, with this
        # subject's bearer still admissible. The fence now reads the foreign
        # owner's markers through its own transaction and re-points a stale
        # claim to this subject as its durable fence.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, lane, self.SUBJECT)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)          # the owner's erasure FINISHED; its claim is stale
        token = _issue_pat_for(self.SUBJECT)
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(self.SUBJECT)).processed is False
        # Intended first assertion: the stale claim now names THIS subject.
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT, "a stale foreign claim was left as the anchor"
        assert registration._subject_revoked(self.SUBJECT) and not _tombstoned(self.SUBJECT) and _bearer_alive(token)
        assert rdb.docs(lane)[self.SUBJECT]["email"] == "[deletion_requested]"  # fenced by the re-pointed claim, so scrubbed in the primary pass
        # A verified ceremony for the mailbox must not mint a fresh subject.
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert _accounts(rdb, VICTIM_EMAIL) == [], "a fresh account was minted for the mailbox"   # the row is de-identified; nothing new carries it
        # The retry finishes: the fence is released by the commit, the bearer dead.
        assert asyncio.run(registration.process_optout(self.SUBJECT)).processed is True
        assert _tombstoned(self.SUBJECT) and not _bearer_alive(token) and key not in rdb.docs(OWNERS)
        assert rdb.docs(lane)[self.SUBJECT]["email"] == "[deletion_requested]"

    @pytest.mark.parametrize("lane", LANES)
    def test_a_stale_claim_never_out_ranks_a_live_subject_whose_row_carries_the_mailbox(self, rdb, lane):
        # aab9995: (T S167 R9-01, the resolver half) the stale-claim reclaim
        # path minted a FRESH subject without looking at rows: a subject with
        # admissible credentials whose row carried the address (a legacy
        # duplicate, or the interrupted erasure above without the fence)
        # was forked. The resolver now looks for such a row first: a sealed
        # carrier fails closed, a live one is adopted through the stale claim.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, lane, self.SUBJECT)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        token = _issue_pat_for(self.SUBJECT)
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        # Intended first assertion: the live carrier is adopted; no fresh subject.
        assert resolved == self.SUBJECT, "a stale claim out-ranked a live subject whose row carries the mailbox"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT and rdb.docs(OWNERS)[key]["verified"] is True
        assert [u for _, u, _ in _accounts(rdb, VICTIM_EMAIL)] == [self.SUBJECT]
        assert _bearer_alive(token)

    @pytest.mark.parametrize("lane", LANES)
    def test_a_claim_naming_a_sealed_owner_stays_its_anchor_until_that_owner_commits(self, rdb, lane):
        # pin (T S167 R9-01 cross-product, the sealed-not-tombstoned owner):
        # an owner whose own erasure has begun keeps its claim — the resolver
        # refuses the mailbox while it is sealed, and the owner's own terminal
        # commit releases it. This subject's row stays deferred with its route
        # until then; nothing mints a fresh subject at any point.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, lane, self.SUBJECT)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_erasure_seal(self.OTHER)                # the owner's erasure has BEGUN
        token = _issue_pat_for(self.SUBJECT)
        with _tombstone_write_fails(StoreUnavailable("marker write down")):
            assert asyncio.run(registration.process_optout(self.SUBJECT)).processed is False
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER                      # the sealed owner keeps its claim
        assert rdb.docs(lane)[self.SUBJECT]["email"] == VICTIM_EMAIL             # deferred row keeps its route
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None       # sealed owner: refused
        assert asyncio.run(registration.process_optout(self.OTHER)).processed is True   # the owner finishes
        assert key not in rdb.docs(OWNERS)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None       # this subject is sealed: refused
        assert [u for _, u, _ in _accounts(rdb, VICTIM_EMAIL)] == [self.SUBJECT] and _bearer_alive(token)
        assert asyncio.run(registration.process_optout(self.SUBJECT)).processed is True
        assert _tombstoned(self.SUBJECT) and rdb.docs(lane)[self.SUBJECT]["email"] == "[deletion_requested]"

    # ── R9-02 · the terminal commit's set is closed over a late fence ────────

    @pytest.mark.parametrize("lane", LANES)
    def test_a_claim_fenced_after_the_snapshot_is_released_by_the_same_commit(self, rdb, lane):
        # aab9995: (T S167 R9-02) the terminal commit deleted only the keys
        # snapshotted before it. With the mailbox anchored to another owner
        # at snapshot time (empty set), that owner then finishing its own
        # erasure, and a duplicate erasure of THIS subject fencing the mailbox
        # to it before the commit, success returned with a claim naming the
        # tombstoned subject — when the hygiene sweep was unavailable. The
        # commit now re-queries the claims naming the subject THROUGH its own
        # transaction and seeds the set with every owner key of the subject's
        # post-seal rows.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        self._row(rdb, lane, self.SUBJECT)
        token = _issue_pat_for(self.SUBJECT)
        original = stores.tombstone_subject_releasing_claims
        state = {"interposed": False}

        def late_fence_then_commit(uuid_, owners, claim_keys):
            if not state["interposed"]:
                state["interposed"] = True
                # the foreign owner finishes its own erasure: its claim is released
                assert _run_off_loop(registration.process_optout(self.OTHER)).processed is True
                assert key not in rdb.docs(OWNERS)
                # a concurrent duplicate erasure of THIS subject fences the mailbox to it, after the snapshot
                outcome = registration._fence_mailbox_for_erasure(
                    OWNERS, key, subject_uuid=self.SUBJECT, collection_base=lane, now=REGISTRATION_NOW,
                )
                assert outcome == registration.FENCE_FENCED and rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT
            return original(uuid_, owners, claim_keys)

        with patch.object(stores, "tombstone_subject_releasing_claims", side_effect=late_fence_then_commit), \
                patch.object(registration, "_release_claims_naming", side_effect=StoreUnavailable("owners sweep down")):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert state["interposed"], "the late fence never happened; the test proved nothing"
        assert result.processed is True and _tombstoned(self.SUBJECT) and not _bearer_alive(token)
        # Intended first assertion: success entails no surviving claim naming the erased subject.
        claim = rdb.docs(OWNERS).get(key)
        assert claim is None or claim.get("uuid") != self.SUBJECT, "a claim fenced after the snapshot survived a success"

    # ── R9-03 · the receipt separates revocation from de-identification ─────

    @pytest.mark.parametrize("lane", LANES)
    def test_a_success_receipt_does_not_claim_de_identification_it_cannot_confirm(self, rdb, lane):
        # aab9995: (T S167 R9-03) a row deferred behind another live subject's
        # claim is de-identified only by the post-tombstone hygiene re-scrub;
        # when that failed, the receipt still said principal PII "has been
        # de-identified" while the address remained stored. Revocation stays
        # final; the receipt now says de-identification is pending and names
        # the continuation that needs no bearer.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        self._row(rdb, lane, self.SUBJECT)
        token = _issue_pat_for(self.SUBJECT)
        real_scrub = registration._scrub_subject_rows
        calls = {"n": 0}

        def primary_passes_hygiene_fails(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return real_scrub(*args, **kwargs)
            raise ServiceUnavailable("account store down")

        with patch.object(registration, "_scrub_subject_rows", side_effect=primary_passes_hygiene_fails):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert calls["n"] >= 2, "the hygiene re-scrub never ran; the test proved nothing"
        assert result.processed is True and _tombstoned(self.SUBJECT) and not _bearer_alive(token)   # revocation final
        assert rdb.docs(lane)[self.SUBJECT]["email"] == VICTIM_EMAIL                          # the address is still stored
        # Intended first assertion: the receipt does not claim what the store contradicts.
        assert "has been de-identified" not in result.message, "the receipt claimed a de-identification that did not happen"
        assert result.model_dump().get("account_deidentification") == "pending"
        assert "alton@ysenseai.org" in result.message and "no sign-in" in result.message       # bearer-independent continuation
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER                                       # the live owner's claim untouched

    def test_a_success_receipt_with_every_row_de_identified_says_so(self, rdb):
        # pin (both heads on the message; the state field is new at this
        # head): the ordinary erasure — no deferred row — still carries the
        # completed-de-identification sentence, so the pending receipt above
        # is a distinct truth, not a softened default.
        subject = _register_and_verify(rdb)
        result = asyncio.run(registration.process_optout(subject))
        assert result.processed is True and "has been de-identified" in result.message
        assert result.model_dump().get("account_deidentification", "complete") == "complete"
        # The field's scope (Lens A F4): every ACCOUNT row of the subject, both lanes.
        assert all("@" not in str(d.get("email") or "")
                   for lane in ("early_adopters", "ea_registrations")
                   for d in rdb.docs(lane).values() if d.get("uuid") == subject)

    def test_a_claim_naming_the_subject_created_after_the_snapshot_at_any_key_is_released(self, rdb):
        # aab9995: (T S167 R9-02, the closure itself) the seed built from the
        # subject's rows covers every key a duplicate fence can create, but
        # the contract is stronger — the commit must release EVERY claim that
        # names the subject at commit time, at any key, however it got there.
        # A writer interposed after the snapshot creates one at a key no row
        # of the subject carries; the transactional re-query inside the commit
        # finds it, and success leaves nothing naming the subject even with
        # the hygiene sweep unavailable.
        subject = _register_and_verify(rdb)
        stray_key = _owner_key("stray-address@example.com")
        original = stores.tombstone_subject_releasing_claims
        state = {"interposed": False}

        def stray_claim_then_commit(uuid_, owners, claim_keys):
            if not state["interposed"]:
                state["interposed"] = True
                assert stray_key not in claim_keys
                rdb.seed(OWNERS, stray_key, {"uuid": subject, "collection": "early_adopters", "verified": True})
            return original(uuid_, owners, claim_keys)

        with patch.object(stores, "tombstone_subject_releasing_claims", side_effect=stray_claim_then_commit),                 patch.object(registration, "_release_claims_naming", side_effect=StoreUnavailable("owners sweep down")):
            result = asyncio.run(registration.process_optout(subject))
        assert state["interposed"] and result.processed is True and _tombstoned(subject)
        # Intended first assertion: the stray claim naming the erased subject is gone.
        assert stray_key not in rdb.docs(OWNERS), "a claim created after the snapshot survived the commit"
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs(OWNERS)

    # ── R9-01 · the carrier's own lifecycle (Lens B: the guard's other branches) ─

    @pytest.mark.parametrize("lane", LANES)
    def test_a_sealed_carrier_refuses_the_mailbox_and_its_claim_is_untouched(self, rdb, lane):
        # aab9995: (T S167 R9-01, the sealed carrier; Lens B M8/M23) a row
        # carrying the address for a subject whose erasure has BEGUN (sealed,
        # not tombstoned, bearer alive) must neither be adopted nor out-ranked
        # by a fresh subject: the resolver refuses until that erasure
        # finishes, and writes nothing.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, lane, self.SUBJECT)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)          # the claim is stale
        stores.write_erasure_seal(self.SUBJECT)              # the carrier's erasure has begun
        token = _issue_pat_for(self.SUBJECT)
        writes = _count_owner_writes(rdb)
        # Intended first assertion: refused — not adopted, not minted.
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a sealed carrier was adopted or out-ranked"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        assert [u for _, u, _ in _accounts(rdb, VICTIM_EMAIL)] == [self.SUBJECT] and _bearer_alive(token)

    @pytest.mark.parametrize("lane", LANES)
    def test_a_tombstoned_carrier_is_never_revived_by_a_stale_claim(self, rdb, lane):
        # pin (Lens B C1/M6): a row still carrying the address for a
        # TOMBSTONED subject — the pending-de-identification end state — is
        # not a carrier. The resolver mints a fresh subject and never returns
        # or re-stamps a tombstoned identifier, at both heads.
        key = _owner_key(VICTIM_EMAIL)
        gone = "018f6b2a-dddd-7abc-8def-0123456789ab"
        self._row(rdb, lane, gone)
        stores.write_subject_tombstone(gone)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert resolved not in (None, gone, self.OTHER) and not _tombstoned(resolved), "a tombstoned identifier was revived or the mailbox refused"
        assert rdb.docs(OWNERS)[key]["uuid"] == resolved

    def test_the_stale_owners_own_row_is_not_a_carrier(self, rdb):
        # pin (Lens B M7): the tombstoned owner's own row still carrying the
        # address is excluded by identity, not only by its tombstone; a fresh
        # subject is minted and the claim moves to it.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert resolved not in (None, self.OTHER) and rdb.docs(OWNERS)[key]["uuid"] == resolved

    def test_a_carrier_row_without_a_uuid_field_is_refused_not_out_ranked(self, rdb):
        # aab9995: (Lens B M30 + Lens A F3; the S165 A-1 selector class on the
        # new selector) a legacy row keyed by the subject's identifier with no
        # ``uuid`` field still carries the address for a subject whose
        # credentials may be admissible: the carrier scan finds it through
        # its id, and because such a row is not adoptable (no identifier
        # field), the resolver refuses WITHOUT moving the claim — never a
        # fresh subject over it, never a claim pointed at a record it will
        # not adopt.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", self.SUBJECT, {"email": VICTIM_EMAIL, "status": "active", "email_verified": True})
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        token = _issue_pat_for(self.SUBJECT)
        writes = _count_owner_writes(rdb)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a row without a uuid field was out-ranked by a fresh subject"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0 and _bearer_alive(token)

    def test_a_lost_reclaim_race_adopts_the_winner_instead_of_refusing(self, rdb):
        # pin (Lens B M29): the conditional re-point of a stale claim can
        # lose to a concurrent writer; the resolver then re-reads and adopts
        # the winner rather than refusing the mailbox.
        key = _owner_key(VICTIM_EMAIL)
        winner = "018f6b2a-eeee-7abc-8def-0123456789ab"
        self._row(rdb, "early_adopters", self.SUBJECT)
        self._row(rdb, "ea_registrations", winner)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        fired = {"n": 0}

        def a_rival_repoints_the_claim():
            fired["n"] += 1
            rdb.seed(OWNERS, key, {"uuid": winner, "collection": "ea_registrations", "verified": True})

        rdb._next_barrier = a_rival_repoints_the_claim        # fires at the reclaim transaction's commit
        resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert fired["n"] == 1, "the rival never landed; the test proved nothing"
        assert resolved == winner, "a lost reclaim race refused the mailbox instead of adopting the winner"
        assert rdb.docs(OWNERS)[key]["uuid"] == winner

    # ── R9-02 · the seed is in the read set (Lens B M10) ────────────────────

    @pytest.mark.parametrize("lane", LANES)
    def test_a_fence_landing_inside_the_terminal_commits_window_conflicts_it(self, rdb, lane):
        # aab9995: (T S167 R9-02, the concurrent case) with the mailbox
        # anchored to another owner at the terminal read, that owner's
        # erasure and a duplicate fence of THIS subject land after the read
        # and before the commit. The seed key is in the read set, so the
        # commit conflicts, retries, sees the claim naming this subject and
        # releases it — even with the hygiene sweep unavailable. Without the
        # seed nothing in the read set changed and the claim survived.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        self._row(rdb, lane, self.SUBJECT)
        token = _issue_pat_for(self.SUBJECT)
        state = {"fired": 0, "armed": False}

        def inside_the_commit_window():
            if state["fired"]:
                return                                          # the window is entered once
            state["fired"] += 1
            assert _run_off_loop(registration.process_optout(self.OTHER)).processed is True
            assert key not in rdb.docs(OWNERS)
            outcome = registration._fence_mailbox_for_erasure(
                OWNERS, key, subject_uuid=self.SUBJECT, collection_base=lane, now=REGISTRATION_NOW,
            )
            assert outcome == registration.FENCE_FENCED and rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT

        original_seal = stores.write_erasure_seal

        def seal_then_arm(target):
            original_seal(target)
            if target == self.SUBJECT and not state["armed"]:
                state["armed"] = True
                rdb._next_barrier = inside_the_commit_window   # the next transaction is THIS subject's terminal commit

        with patch.object(stores, "write_erasure_seal", side_effect=seal_then_arm), \
                patch.object(registration, "_release_claims_naming", side_effect=StoreUnavailable("owners sweep down")):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert state["fired"] == 1, "the window was never entered; the test proved nothing"
        assert result.processed is True and _tombstoned(self.SUBJECT) and not _bearer_alive(token)
        # Intended first assertion: the claim fenced inside the window did not survive the success.
        claim = rdb.docs(OWNERS).get(key)
        assert claim is None or claim.get("uuid") != self.SUBJECT, "a fence inside the commit window survived a success"

    def test_the_terminal_set_is_the_owner_keys_of_address_bearing_rows_and_each_claim_is_written_once(self, rdb):
        # aab9995: (Lens B M19/M14) the commit is handed exactly the owner key of
        # every address-bearing post-seal row, de-duplicated; it releases each
        # distinct claim naming the subject once and reports that count (the
        # parent wrote a repeated key once per repetition and reported three).
        subject = _register_and_verify(rdb)
        second = "second-address@example.com"
        rdb.seed("ea_registrations", subject, {"uuid": subject, "email": second, "status": "active"})
        rdb.seed("ea_registrations", "sibling-row", {"uuid": subject, "email": "[deletion_requested]", "status": "deletion_requested"})
        original = stores.tombstone_subject_releasing_claims
        seen = {}

        def record(uuid_, owners, claim_keys):
            seen["keys"] = list(claim_keys)
            seen["released"] = original(uuid_, owners, claim_keys)
            return seen["released"]

        with patch.object(stores, "tombstone_subject_releasing_claims", side_effect=record):
            assert asyncio.run(registration.process_optout(subject)).processed is True
        assert sorted(seen["keys"]) == sorted({_owner_key(VICTIM_EMAIL), _owner_key(second)})   # no junk key for the scrubbed row
        assert len(seen["keys"]) == len(set(seen["keys"])) and seen["released"] == 2
        # De-duplication inside the primitive: a repeated key is one write.
        other = "018f6b2a-ffff-7abc-8def-0123456789ab"
        rdb.seed(OWNERS, _owner_key("dup@example.com"), {"uuid": other, "collection": "early_adopters", "verified": True})
        writes = _count_owner_writes(rdb)
        assert stores.tombstone_subject_releasing_claims(other, OWNERS, [_owner_key("dup@example.com")] * 3) == 1
        assert writes["n"] == 1

    def test_the_real_transaction_adapter_queries_through_the_transaction(self):
        # adapter contract (Lens B M28; skipped where the method is absent):
        # no other test constructs ``_RealTxn``; its query must carry the
        # transaction handle or the closure is a query outside the
        # transaction — the round-9 defect itself.
        from unittest.mock import MagicMock
        if not hasattr(stores._RealTxn, "where_ids"):
            pytest.skip("adapter method absent at this head")
        db, handle = MagicMock(), object()
        snap = MagicMock(); snap.id = "k1"
        db.collection.return_value.where.return_value.get.return_value = [snap]
        assert stores._RealTxn(db, handle).where_ids("email_owners", "uuid", "s") == ["k1"]
        db.collection.assert_called_with("email_owners")
        db.collection.return_value.where.assert_called_with("uuid", "==", "s")
        db.collection.return_value.where.return_value.get.assert_called_once_with(transaction=handle)

    # ── R9-03 · the confirming read, in both directions (Lens B M33/M22/M17) ─

    @pytest.mark.parametrize("lane", LANES)
    def test_a_deferred_row_whose_hygiene_succeeds_gets_a_complete_receipt(self, rdb, lane):
        # pin (Lens B M33): "pending" comes from a READ of the deferred rows
        # after hygiene, not from the deferral itself — when the re-scrub
        # succeeds the receipt says complete and the row is de-identified.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        self._row(rdb, lane, self.SUBJECT)
        result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert result.processed is True and _tombstoned(self.SUBJECT)
        assert rdb.docs(lane)[self.SUBJECT]["email"] == "[deletion_requested]"
        assert "has been de-identified" in result.message
        assert result.model_dump().get("account_deidentification", "complete") == "complete"

    def test_pending_is_decided_over_every_deferred_row_not_the_last_one_read(self, rdb):
        # aab9995: (Lens B M22) a subject with a deferred row that keeps its
        # address AND a fenced row that was scrubbed: the receipt is pending
        # because ANY deferred row still carries an address, not because the
        # last row read does.
        key = _owner_key(VICTIM_EMAIL)
        second = "second-address@example.com"
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        self._row(rdb, "early_adopters", self.SUBJECT)                                   # deferred (anchored to OTHER)
        rdb.seed("ea_registrations", self.SUBJECT, {"uuid": self.SUBJECT, "email": second, "status": "active"})   # fenced, scrubbed
        real_scrub = registration._scrub_subject_rows
        calls = {"n": 0}

        def primary_passes_hygiene_fails(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return real_scrub(*args, **kwargs)
            raise ServiceUnavailable("account store down")

        with patch.object(registration, "_scrub_subject_rows", side_effect=primary_passes_hygiene_fails):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert calls["n"] >= 2 and result.processed is True and _tombstoned(self.SUBJECT)
        assert rdb.docs("ea_registrations")[self.SUBJECT]["email"] == "[deletion_requested]"     # the fenced row went
        assert rdb.docs("early_adopters")[self.SUBJECT]["email"] == VICTIM_EMAIL                # the deferred one stayed
        # Intended first assertion: pending, decided over every deferred row.
        assert "has been de-identified" not in result.message and result.model_dump().get("account_deidentification") == "pending"

    def test_an_unconfirmable_deferred_row_is_reported_pending_not_complete(self, rdb):
        # aab9995: (Lens B M17) when the hygiene re-scrub fails AND the read
        # that would confirm the deferred row fails too, unknown is reported
        # as pending — never as completed de-identification.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, "early_adopters", self.OTHER)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        self._row(rdb, "ea_registrations", self.SUBJECT)
        real_scrub = registration._scrub_subject_rows
        calls = {"n": 0}

        def hygiene_fails_and_reads_go_down(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return real_scrub(*args, **kwargs)
            _reads_down(rdb, "ea_registrations")            # the confirming read will fail too
            raise ServiceUnavailable("account store down")

        with patch.object(registration, "_scrub_subject_rows", side_effect=hygiene_fails_and_reads_go_down):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert calls["n"] >= 2 and result.processed is True and _tombstoned(self.SUBJECT)
        # Intended first assertion: unknown is pending.
        assert "has been de-identified" not in result.message and result.model_dump().get("account_deidentification") == "pending"

    def test_the_receipt_state_rides_every_opt_out_http_surface(self, rdb, http):
        # aab9995: (Lens B, the wire shape) the state field is on the 200
        # success receipt; the 401 mismatch and the 503 outage receipts carry
        # it as null, so every opt-out response has the same keys.
        subject = _register_and_verify(rdb)
        token = _issue_pat_for(subject)
        headers = {"Authorization": f"Bearer {token}"}
        denied = http.post(f"/early-adopters/optout/{self.OTHER}", headers=headers)
        assert denied.status_code == 401 and "account_deidentification" in denied.json() and denied.json()["account_deidentification"] is None
        ok = http.post(f"/early-adopters/optout/{subject}", headers=headers)
        assert ok.status_code == 200
        # Intended first assertion: the success receipt states its de-identification truth.
        assert ok.json().get("account_deidentification") == "complete"
        other = _register_and_verify_second = None  # noqa: F841 — the outage surface below needs no second subject
        again = http.post(f"/early-adopters/optout/{subject}", headers=headers)   # the bearer is dead now: 401, same keys
        assert again.status_code == 401 and again.json()["account_deidentification"] is None
        assert set(ok.json()) == set(denied.json()) == set(again.json())

    # ── Lens A · the carrier adoption is one transaction (F1/F2/F3/F5/F6) ────

    def test_a_seal_landing_inside_the_adoption_window_refuses_and_writes_nothing(self, rdb):
        # aab9995: (S168 Lens A F1, HIGH — introduced by this repair's first
        # cut) the carrier path checked the carrier's seal OUTSIDE the
        # transaction that re-pointed the claim, so a seal landing between
        # the check and the commit let a ceremony adopt a subject whose
        # erasure had begun, mark the claim verified for it, and rewrite
        # consent onto its record while its bearer was admissible. The
        # adoption now reads the carrier's seal and tombstone through its own
        # transaction: the commit conflicts, the retry sees the seal, nothing
        # is written.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "active", "email_verified": False})
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        token = _issue_pat_for(self.SUBJECT)
        writes = _count_owner_writes(rdb)
        rdb._next_barrier = lambda: stores.write_erasure_seal(self.SUBJECT)   # fires at the adoption's commit
        # Intended first assertion: refused, not adopted.
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a subject sealed inside the adoption window was adopted"
        assert registration._subject_revoked(self.SUBJECT) and _bearer_alive(token)
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        row = rdb.docs("early_adopters")[self.SUBJECT]
        assert row["email_verified"] is False and "consent" not in row                     # nothing rewritten

    def test_a_carrier_that_stops_being_adoptable_inside_the_window_is_refused(self, rdb):
        # aab9995: (S168 Lens A F2) adoptability was decided on a snapshot
        # read before the claim write; a row that changed in between was
        # adopted anyway. The row is now read inside the adopting
        # transaction: a change conflicts the commit and the retry refuses.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "active", "email_verified": False})
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        writes = _count_owner_writes(rdb)

        def the_row_is_no_longer_active():
            rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "suspended", "email_verified": False})

        rdb._next_barrier = the_row_is_no_longer_active
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a record that changed inside the window was adopted from a stale snapshot"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        assert "consent" not in rdb.docs("early_adopters")[self.SUBJECT]

    def test_an_unadoptable_carrier_is_refused_without_moving_the_claim(self, rdb):
        # aab9995: (S168 Lens A F3) the claim was re-pointed to a carrier the
        # adopter then refused, leaving the canonical owner pointing at a
        # record every later ceremony rejects — permanently. Adoptability is
        # now decided before the claim write, inside the same transaction;
        # an unadoptable carrier is refused with nothing written, and the
        # mailbox routes again as soon as the record is adoptable.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "suspended", "email_verified": True})
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        writes = _count_owner_writes(rdb)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a fresh subject was minted over an unadoptable carrier"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "active", "email_verified": True})
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SUBJECT                # routable again
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT and rdb.docs(OWNERS)[key]["verified"] is True

    def test_any_sealed_candidate_refuses_the_mailbox_whatever_the_lane_order(self, rdb):
        # aab9995: (S168 Lens A F5) with a sealed carrier in one lane and a
        # live carrier in the other, the refusal is a property of the
        # candidate SET: the live one is not adopted while the sealed one's
        # erasure is in progress, and nothing is written.
        key = _owner_key(VICTIM_EMAIL)
        live = "018f6b2a-abab-7abc-8def-0123456789ab"
        self._row(rdb, "ea_registrations", live)                 # the second lane holds the live carrier
        self._row(rdb, "early_adopters", self.SUBJECT)
        stores.write_erasure_seal(self.SUBJECT)                   # the first lane's carrier is sealed
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        writes = _count_owner_writes(rdb)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        # Lane order reversed: the sealed candidate sits in the second lane.
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        rdb._collection_store("early_adopters")._remove(self.SUBJECT)
        rdb._collection_store("ea_registrations")._remove(live)
        self._row(rdb, "early_adopters", live)
        self._row(rdb, "ea_registrations", self.SUBJECT)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER

    @pytest.mark.parametrize("lane", LANES)
    def test_a_claim_with_no_owner_identifier_is_fenced_not_anchored(self, rdb, lane):
        # aab9995: (S168 Lens A F6, pre-existing) a claim whose ``uuid`` is
        # empty has no lifecycle and anchors nothing, yet it was treated as
        # "anchored elsewhere": never released by any erasure, and the
        # mailbox stayed unroutable forever (the resolver refuses a malformed
        # claim). The fence now takes it as this subject's fence, the
        # commit releases it, and the mailbox routes again.
        key = _owner_key(VICTIM_EMAIL)
        self._row(rdb, lane, self.SUBJECT)
        rdb.seed(OWNERS, key, {"uuid": "", "collection": "early_adopters", "verified": True})
        token = _issue_pat_for(self.SUBJECT)
        assert asyncio.run(registration.process_optout(self.SUBJECT)).processed is True
        assert _tombstoned(self.SUBJECT) and not _bearer_alive(token)
        # Intended first assertion: the ownerless claim did not survive the erasure.
        assert key not in rdb.docs(OWNERS), "a claim with no owner identifier survived as an anchor"
        assert rdb.docs(lane)[self.SUBJECT]["email"] == "[deletion_requested]"
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) not in (None, self.SUBJECT)   # routable: a fresh subject

    # ── harness · the fake's transactional query joins the read set ─────────

    def test_a_transactional_query_puts_its_matches_in_the_read_set(self, rdb):
        # harness test (not a pin: the fake gained ``where_ids`` at this head,
        # so it cannot run against the parent's own fake): ``where_ids``
        # through a transaction records the version of every matched
        # document, so a matched claim re-pointed — or deleted and re-created
        # — before the commit conflicts the transaction, the way the real
        # client's ``Query.get(transaction=...)`` plus the server's update-time
        # check serve the terminal commit.
        from .oauth_fakes import TransactionConflict
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(OWNERS, key, {"uuid": self.SUBJECT, "collection": "early_adopters", "verified": True})
        txn = rdb.new_transaction()
        assert txn.where_ids(OWNERS, "uuid", self.SUBJECT) == [key]
        rdb.seed(OWNERS, key, {"uuid": "someone-else", "collection": "early_adopters", "verified": True})
        txn.delete(OWNERS, key)
        with pytest.raises(TransactionConflict):
            txn._commit()
        assert rdb.docs(OWNERS)[key]["uuid"] == "someone-else"                  # nothing landed
        # Delete-then-recreate is a change too (Lens B: the version used to reset on delete).
        txn = rdb.new_transaction()
        assert txn.where_ids(OWNERS, "uuid", "someone-else") == [key]
        rdb._collection_store(OWNERS)._remove(key)
        rdb.seed(OWNERS, key, {"uuid": "someone-else", "collection": "early_adopters", "verified": True})
        txn.delete(OWNERS, key)
        with pytest.raises(TransactionConflict):
            txn._commit()
        assert key in rdb.docs(OWNERS)
        # A delete alone is a change too: a document read, then deleted, conflicts the reader's commit.
        txn = rdb.new_transaction()
        assert txn.where_ids(OWNERS, "uuid", "someone-else") == [key]
        rdb._collection_store(OWNERS)._remove(key)
        txn.delete(OWNERS, key)
        with pytest.raises(TransactionConflict):
            txn._commit()


# ═══════════════════════════════════════════════════════════════════════════
# CS round 10 (T S168) — a set-level decision binds every live participant:
# every candidate of the carrier set, and every in-flight request that has
# already read enough to write.
# ═══════════════════════════════════════════════════════════════════════════

class TestSetDecisionsBindEveryLiveParticipant:
    """CS round 10 at `72a92ae` (T S168 R10-01/R10-02). R10-01: the carrier
    set was scanned outside the adoption transaction and only the SELECTED
    carrier's markers and row were read inside it, so a different candidate
    could seal after the scan while the selected one was adopted — two
    verified subjects on one mailbox and the sealed subject's bearer still
    admissible. R10-02: the terminal commit's set was seeded from current
    rows and a current query, so an older duplicate erasure holding a row
    snapshot from before a scrub could fence the address inside the commit
    window at a key the transaction never read; success returned with a
    claim naming the tombstoned subject when hygiene was unavailable. Tests
    labelled ``72a92ae:`` fail at that head on the named assertion; the
    measured differential is in the module header."""

    OTHER = "018f6b2a-bbb2-7abc-8def-0123456789ab"
    SUBJECT = "018f6b2a-bbb3-7abc-8def-0123456789ab"
    SECOND = "018f6b2a-c0c0-7abc-8def-0123456789ab"
    ORDERS = (("early_adopters", "ea_registrations"), ("ea_registrations", "early_adopters"))

    @staticmethod
    def _row(rdb, lane, subject, *, verified):
        rdb.seed(lane, subject, {
            "uuid": subject, "email": VICTIM_EMAIL, "status": "active", "email_verified": verified,
        })

    @staticmethod
    def _fence_index(rdb, subject):
        """The subject's fence index as stored — resolved through the same
        namespaced ``tombstone_ref`` the code uses, so an absent index is a
        real absence and not a wrong collection name."""
        collection, doc_id = stores.tombstone_ref("fence", subject)
        return rdb.docs(collection).get(doc_id)

    def _stale_claim(self, rdb):
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
        stores.write_subject_tombstone(self.OTHER)
        return key

    # ── R10-01 · the whole candidate set is bound at adoption ────────────────

    @pytest.mark.parametrize("first_lane,second_lane", ORDERS)
    def test_a_seal_on_a_non_selected_carrier_inside_the_adoption_window_refuses(self, rdb, first_lane, second_lane):
        # 72a92ae (in the order where the parent selected the OTHER row —
        # lane order is fixed, so the reverse parameter is a pin: there the
        # sealed candidate IS the selected one and the parent re-read it):
        # (T S168 R10-01, HIGH) two live unverified carriers; the first in
        # lane order is selected. The other candidate's erasure seal lands
        # after the scan and before the adoption commit. The
        # transaction now reads every candidate's markers and row, so the
        # commit conflicts, the retry sees the seal, and nothing is written:
        # no second verified subject, the sealed subject's bearer alive.
        key = self._stale_claim(rdb)
        self._row(rdb, first_lane, self.SUBJECT, verified=False)      # selected (first lane)
        self._row(rdb, second_lane, self.SECOND, verified=False)      # the non-selected candidate
        token = _issue_pat_for(self.SECOND)
        writes = _count_owner_writes(rdb)
        rdb._next_barrier = lambda: stores.write_erasure_seal(self.SECOND)   # fires at the adoption commit
        # Intended first assertion: refused — no candidate adopted while another sealed.
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a carrier was adopted after another candidate sealed"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        assert rdb.docs(first_lane)[self.SUBJECT]["email_verified"] is False          # nothing rewritten
        assert registration._subject_revoked(self.SECOND) and _bearer_alive(token)

    @pytest.mark.parametrize("first_lane,second_lane", ORDERS)
    def test_two_verified_carriers_refuse_the_mailbox_without_writes(self, rdb, first_lane, second_lane):
        # 72a92ae: (T S168 R10-01, the conflicting-identity clause) two live
        # VERIFIED carriers for one mailbox — adopting either would leave the
        # other verified with an admissible bearer. The transaction refuses
        # with nothing written; both bearers stay as they were.
        key = self._stale_claim(rdb)
        self._row(rdb, first_lane, self.SUBJECT, verified=True)
        self._row(rdb, second_lane, self.SECOND, verified=True)
        tokens = (_issue_pat_for(self.SUBJECT), _issue_pat_for(self.SECOND))
        writes = _count_owner_writes(rdb)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "one of two verified carriers was adopted over the other"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        assert all(_bearer_alive(t) for t in tokens)

    @pytest.mark.parametrize("first_lane,second_lane", ORDERS)
    def test_the_verified_carrier_is_selected_whatever_the_lane_order(self, rdb, first_lane, second_lane):
        # 72a92ae (in the order where the verified row sits in the second
        # lane; the reverse parameter is a pin — the parent's first-lane
        # rule picked it anyway): (T S168 R10-01, selection) one verified and
        # one unverified carrier: the verified one — the identity the mailbox
        # was already proven for — is adopted whatever lane it sits in; the
        # unverified row is not rewritten and the claim names the verified
        # subject.
        key = self._stale_claim(rdb)
        self._row(rdb, first_lane, self.SUBJECT, verified=False)
        self._row(rdb, second_lane, self.SECOND, verified=True)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SECOND, "the unverified first-lane row out-ranked the verified carrier"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SECOND and rdb.docs(OWNERS)[key]["verified"] is True
        assert rdb.docs(first_lane)[self.SUBJECT]["email_verified"] is False and "consent" not in rdb.docs(first_lane)[self.SUBJECT]

    def test_a_candidate_whose_erasure_finishes_inside_the_window_is_ignored_not_refused(self, rdb):
        # pin (Lens B M6/MX3: the production shape — seal, THEN tombstone):
        # a non-selected candidate whose erasure FINISHES inside the window
        # is no longer a carrier; the retry adopts the remaining live
        # candidate instead of refusing the mailbox forever on its seal.
        key = self._stale_claim(rdb)
        self._row(rdb, "early_adopters", self.SUBJECT, verified=False)
        self._row(rdb, "ea_registrations", self.SECOND, verified=False)

        def the_other_candidates_erasure_finishes():
            stores.write_erasure_seal(self.SECOND)
            stores.write_subject_tombstone(self.SECOND)

        rdb._next_barrier = the_other_candidates_erasure_finishes
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SUBJECT, "a finished erasure on another candidate refused the mailbox"
        # without this witness the test passes with its interleaving DELETED: two live
        # candidates also resolve to SUBJECT by lane order (a lens found exactly that)
        assert _tombstoned(self.SECOND), "the other candidate's erasure never finished; the test proved nothing"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT

    def test_the_selected_candidate_whose_erasure_finishes_inside_the_window_is_never_adopted(self, rdb):
        # 72a92ae: (Lens B M7; Lens A F-D) the SELECTED candidate's erasure
        # finishes (seal, then tombstone) inside the window. The retry
        # decides the set again inside the transaction: the tombstoned
        # candidate is gone, the remaining live one is adopted — never the
        # tombstoned identifier, never a refusal of the whole request.
        key = self._stale_claim(rdb)
        self._row(rdb, "early_adopters", self.SUBJECT, verified=False)     # selected (first lane)
        self._row(rdb, "ea_registrations", self.SECOND, verified=False)

        def the_selected_candidates_erasure_finishes():
            stores.write_erasure_seal(self.SUBJECT)
            stores.write_subject_tombstone(self.SUBJECT)

        rdb._next_barrier = the_selected_candidates_erasure_finishes
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SECOND, "a tombstoned selected candidate refused the request or was adopted"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SECOND

    def test_one_subject_with_rows_in_both_lanes_is_one_candidate_not_a_conflict(self, rdb):
        # pin (Lens A F-B): a subject holding a verified row in BOTH lanes is
        # ONE candidate, never a conflict with itself. It passes at 72a92ae,
        # which decided over a single selected row and so could not conflict
        # with itself; the FIRST CUT of this repair introduced that bug by
        # quantifying the conflict rule over ROWS, and the adversarial lens
        # caught it before this commit. The set is quantified over DISTINCT
        # subject identifiers: the subject is adopted, the claim names it.
        key = self._stale_claim(rdb)
        self._row(rdb, "early_adopters", self.SUBJECT, verified=True)
        self._row(rdb, "ea_registrations", self.SUBJECT, verified=True)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SUBJECT, "a subject conflicted against its own second-lane row"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT and rdb.docs(OWNERS)[key]["verified"] is True

    def test_an_unproven_unadoptable_candidate_does_not_deny_the_mailbox(self, rdb):
        # pin at 72a92ae, and a repair of THIS repair's first cut. A second live
        # candidate whose row never proved the mailbox and cannot be adopted
        # (suspended) holds no credential for this address, so it must not deny
        # the mailbox to the candidate that can be adopted. The first cut judged
        # adoptability over EVERY live candidate and refused here — permanently,
        # since nothing in the state changes — which is an availability loss on
        # a state R10-01 never named. A lens found it before this commit.
        key = self._stale_claim(rdb)
        self._row(rdb, "early_adopters", self.SUBJECT, verified=False)
        rdb.seed("ea_registrations", self.SECOND, {
            "uuid": self.SECOND, "email": VICTIM_EMAIL, "status": "suspended", "email_verified": False,
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SUBJECT, "an unproven, unadoptable candidate denied the mailbox"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT and rdb.docs(OWNERS)[key]["verified"] is True
        assert rdb.docs("ea_registrations")[self.SECOND]["email_verified"] is False     # left alone

    @pytest.mark.parametrize("shape", ("inactive_verified", "uuid_less_verified"))
    def test_a_live_subject_with_an_unadoptable_row_refuses_not_out_ranked(self, rdb, shape):
        # pin (Lens A F-C, Lens B M4a/M5b — the accepted fail-closed cost,
        # stated per shape). `inactive_verified`: the suspended row PROVED this
        # mailbox, so its subject is the identity the mailbox belongs to and no
        # other carrier may be verified over it — but the row is not an
        # adoption target, so the mailbox refuses with nothing written and the
        # rights channel is the continuation. `uuid_less_verified`: nothing
        # proved the mailbox (no identifier, so `_already_proven` is false), and
        # lane order selects it — the round-9 rule that a carrier row is never
        # out-ranked by minting a fresh subject. Both refuse; the reasons
        # differ, and only the first is about credentials.
        key = self._stale_claim(rdb)
        if shape == "inactive_verified":
            rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "suspended", "email_verified": True})
        else:
            rdb.seed("early_adopters", self.SUBJECT, {"email": VICTIM_EMAIL, "status": "active", "email_verified": True})
        self._row(rdb, "ea_registrations", self.SECOND, verified=False)
        writes = _count_owner_writes(rdb)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a live carrier was verified over a subject whose row cannot be adopted"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0

    def test_membership_is_decided_inside_the_transaction_not_from_a_scan(self, rdb):
        # 72a92ae: (Lens A F-A) a carrier row that appears after the parent's
        # pre-transaction scan and before the adopting transaction was not a
        # member of the set that transaction decided over: the parent adopted
        # the row it had scanned while a VERIFIED, SEALED second carrier
        # existed in the same lane — two verified subjects for one mailbox and
        # the sealed one's bearer still admissible. Membership is enumerated
        # inside the transaction now, so the second carrier is bound and the
        # mailbox refuses with nothing written. (A row created after the
        # transaction's OWN read, by a writer that reads nothing this
        # transaction writes, is the predicate-lock limit disclosed as F-9;
        # every in-repo writer reads the claim first.)
        key = self._stale_claim(rdb)
        self._row(rdb, "early_adopters", self.SUBJECT, verified=False)
        token = _issue_pat_for(self.SECOND)
        real = stores.run_transaction
        state = {"n": 0}

        def a_verified_sealed_carrier_appears_first(func):
            if state["n"] == 0:                            # the adopting transaction is the first
                state["n"] = 1
                self._row(rdb, "early_adopters", self.SECOND, verified=True)
                stores.write_erasure_seal(self.SECOND)     # a plain marker write, not a transaction
            return real(func)

        writes = _count_owner_writes(rdb)
        with patch.object(stores, "run_transaction", side_effect=a_verified_sealed_carrier_appears_first):
            resolved = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert state["n"] == 1, "no transaction ran; the second carrier never appeared"
        assert resolved is None, "a member that appeared before the adopting transaction was not bound"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        assert rdb.docs("early_adopters")[self.SUBJECT]["email_verified"] is False and _bearer_alive(token)


    def test_the_adopted_row_is_sanitized_not_only_the_claim_repointed(self, rdb):
        # pin (mutant M10 survived without it): adoption is a claim re-point
        # AND a sanitizing write, in one transaction. Everything an unverified
        # caller chose on the carrier row is neutralised, the ceremony's own
        # consent provenance is stamped, the cohort privilege returns to the
        # lane default, and the earlier registration moment is kept as
        # provenance rather than presented as the verified actor's.
        key = self._stale_claim(rdb)
        rdb.seed("early_adopters", self.SUBJECT, {
            "uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
            "display_name": "chosen by an unverified caller", "name": "also chosen",
            "registration_feedback": "unverified prose", "feedback_type": "praise",
            "tier": "pioneer", "pilot_source": "invite-code", "updates_consent": True,
            "registered_at": "2026-01-01T00:00:00+00:00",
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SUBJECT
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT and rdb.docs(OWNERS)[key]["verified"] is True
        row = rdb.docs("early_adopters")[self.SUBJECT]
        assert row["email_verified"] is True and row["verification_path"] == "oauth_ceremony_v2", "the row was claimed but never sanitized"
        assert row["display_name"] is None and row["name"] is None
        assert row["registration_feedback"] is None and row["feedback_type"] is None
        assert row["tier"] == "early_adopter" and row["pilot_source"] is None
        assert row["consent"] is True and row["updates_consent"] is False
        assert row["tc_accepted"] is True and row["privacy_acknowledged"] is True
        assert row["preregistration"]["created_at"] == "2026-01-01T00:00:00+00:00"
        assert "registered_at" in row["preregistration"]["neutralized"]

    def test_adoption_sanitizes_every_address_bearing_row_of_the_adopted_subject(self, rdb):
        # 72a92ae for the claim's lane, and a repair of THIS repair's first cut
        # for the sibling row. A lens found that preferring the already-proven
        # row as the write target left the subject's OTHER row exactly as an
        # unverified caller wrote it — and that row is what `/whoami` and the
        # status endpoint serve for the now-verified subject. The proof belongs
        # to the SUBJECT: every row of it carrying this address is sanitized in
        # the same transaction, while the claim still names the lane of the
        # already-proven row (which is what the parent gets wrong here: its
        # fixed first-lane rule names the other one).
        key = self._stale_claim(rdb)
        self._row(rdb, "ea_registrations", self.SUBJECT, verified=True)
        rdb.seed("early_adopters", self.SUBJECT, {
            "uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
            "display_name": "chosen before the proof", "tier": "pioneer",
            "updates_consent": True, "registered_at": "2026-01-01T00:00:00+00:00",
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == self.SUBJECT
        assert rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT
        assert rdb.docs(OWNERS)[key]["collection"] == "ea_registrations", "the claim names a lane other than the already-proven row's"
        sibling = rdb.docs("early_adopters")[self.SUBJECT]
        assert sibling["email_verified"] is True, "a sibling row of the adopted subject kept its pre-proof state"
        assert sibling["display_name"] is None and sibling["tier"] == "early_adopter"
        assert sibling["updates_consent"] is False and sibling["consent"] is True
        assert sibling["preregistration"]["created_at"] == "2026-01-01T00:00:00+00:00"

    def test_a_proven_row_is_an_identity_whatever_its_account_status(self, rdb):
        # pin, discriminated by mutant M11, not by the parent: "already
        # proven" is an IDENTITY question and account status is not part of
        # it — a suspended row that proved this mailbox leaves its subject
        # holding credentials only the tombstone kills. Here SUBJECT has a
        # suspended PROVEN row and an active unverified one (so it does have
        # an adoptable row), and SECOND has an active proven row. Two proven
        # subjects for one mailbox: refuse with nothing written. 72a92ae also
        # refuses, for an unrelated reason — its fixed first-lane rule
        # selected the suspended row and could not adopt it — so this is a
        # pin there; what it discriminates is the predicate, and the mutant
        # that gates it on status again is killed by this test.
        key = self._stale_claim(rdb)
        rdb.seed("early_adopters", self.SUBJECT, {
            "uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "suspended", "email_verified": True,
        })
        rdb.seed("ea_registrations", self.SUBJECT, {
            "uuid": self.SUBJECT, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
        })
        self._row(rdb, "ea_registrations", self.SECOND, verified=True)
        tokens = (_issue_pat_for(self.SUBJECT), _issue_pat_for(self.SECOND))
        writes = _count_owner_writes(rdb)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None, "a proven subject was out-ranked because one of its rows was suspended"
        assert rdb.docs(OWNERS)[key]["uuid"] == self.OTHER and writes["n"] == 0
        assert rdb.docs("ea_registrations")[self.SUBJECT]["email_verified"] is False
        assert all(_bearer_alive(x) for x in tokens)

    # ── R10-02 · an older request-local fence is bound to the terminal commit ─

    @pytest.mark.parametrize("lane", ("early_adopters", "ea_registrations"))
    def test_an_older_fence_from_a_pre_scrub_snapshot_conflicts_the_terminal_commit(self, rdb, lane):
        # 72a92ae: (T S168 R10-02) the resumable state — seal present, row
        # already scrubbed, no claim, no tombstone — gives the retry an empty
        # seed and an empty query. An older duplicate request still holds
        # the pre-scrub address and fences it inside the commit window. The
        # fence now records its key in the subject's fence index in its own
        # transaction; the terminal commit read that index first, so the
        # commit conflicts, retries, and releases the claim — even with the
        # hygiene sweep unavailable. Nothing naming the subject survives.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(lane, self.SUBJECT, {"uuid": self.SUBJECT, "email": "[deletion_requested]", "status": "deletion_requested"})
        stores.write_erasure_seal(self.SUBJECT)
        token = _issue_pat_for(self.SUBJECT)
        state = {"fired": 0, "armed": False}

        def the_older_request_fences_from_its_snapshot():
            if state["fired"]:
                return
            state["fired"] += 1
            outcome = registration._fence_mailbox_for_erasure(
                OWNERS, key, subject_uuid=self.SUBJECT, collection_base=lane, now=REGISTRATION_NOW,
            )
            assert outcome == registration.FENCE_FENCED and rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT

        original_seal = stores.write_erasure_seal

        def seal_then_arm(target):
            original_seal(target)
            if target == self.SUBJECT and not state["armed"]:
                state["armed"] = True
                rdb._next_barrier = the_older_request_fences_from_its_snapshot   # the next transaction is the terminal commit

        with patch.object(stores, "write_erasure_seal", side_effect=seal_then_arm), \
                patch.object(registration, "_release_claims_naming", side_effect=StoreUnavailable("owners sweep down")):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert state["fired"] == 1, "the older fence never landed; the test proved nothing"
        assert result.processed is True and _tombstoned(self.SUBJECT) and not _bearer_alive(token)
        # Intended first assertion: success entails no surviving claim naming the erased subject.
        claim = rdb.docs(OWNERS).get(key)
        assert claim is None or claim.get("uuid") != self.SUBJECT, "an older fence from a pre-scrub snapshot survived a success"
        assert self._fence_index(rdb, self.SUBJECT) is None                                  # the index is gone with the commit

    @pytest.mark.parametrize("branch", ("stale_owner", "ownerless"))
    def test_an_older_fence_through_the_reclaim_branches_is_bound_too(self, rdb, branch):
        # 72a92ae: (Lens B M9c/M9d) the older request's fence can also land
        # through the STALE-OWNER branch (the claim at the terminal read
        # names an already-tombstoned other owner) or the OWNERLESS branch
        # (the claim has no owner identifier): at read time neither claim
        # names this subject, so the query does not hold them and only the
        # fence index binds them. Each branch records the index; success
        # leaves nothing naming the subject.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": "[deletion_requested]", "status": "deletion_requested"})
        if branch == "stale_owner":
            rdb.seed(OWNERS, key, {"uuid": self.OTHER, "collection": "early_adopters", "verified": True})
            stores.write_subject_tombstone(self.OTHER)
        else:
            rdb.seed(OWNERS, key, {"uuid": "", "collection": "early_adopters", "verified": True})
        stores.write_erasure_seal(self.SUBJECT)
        token = _issue_pat_for(self.SUBJECT)
        state = {"fired": 0, "armed": False}

        def the_older_request_fences_from_its_snapshot():
            if state["fired"]:
                return
            state["fired"] += 1
            outcome = registration._fence_mailbox_for_erasure(
                OWNERS, key, subject_uuid=self.SUBJECT, collection_base="early_adopters", now=REGISTRATION_NOW,
            )
            assert outcome == registration.FENCE_FENCED and rdb.docs(OWNERS)[key]["uuid"] == self.SUBJECT

        original_seal = stores.write_erasure_seal

        def seal_then_arm(target):
            original_seal(target)
            if target == self.SUBJECT and not state["armed"]:
                state["armed"] = True
                rdb._next_barrier = the_older_request_fences_from_its_snapshot

        with patch.object(stores, "write_erasure_seal", side_effect=seal_then_arm), \
                patch.object(registration, "_release_claims_naming", side_effect=StoreUnavailable("owners sweep down")):
            result = asyncio.run(registration.process_optout(self.SUBJECT))
        assert state["fired"] == 1 and result.processed is True and _tombstoned(self.SUBJECT) and not _bearer_alive(token)
        claim = rdb.docs(OWNERS).get(key)
        assert claim is None or claim.get("uuid") != self.SUBJECT, f"an older fence through the {branch} branch survived a success"
        assert self._fence_index(rdb, self.SUBJECT) is None

    def test_a_fence_landing_before_the_terminal_read_is_in_the_index_and_released(self, rdb):
        # 72a92ae: the same older fence landing BEFORE the terminal
        # transaction's read is released by the commit at BOTH heads (the
        # transactional query finds it), but only this head records the keys
        # in the subject's index — and a single pre-scrub snapshot can carry
        # more than one address, so the index accumulates both. The parent
        # writes no index, which is the assertion that fails there.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed("early_adopters", self.SUBJECT, {"uuid": self.SUBJECT, "email": "[deletion_requested]", "status": "deletion_requested"})
        stores.write_erasure_seal(self.SUBJECT)
        assert registration._fence_mailbox_for_erasure(
            OWNERS, key, subject_uuid=self.SUBJECT, collection_base="early_adopters", now=REGISTRATION_NOW,
        ) == registration.FENCE_FENCED
        second_key = _owner_key("second-address@example.com")             # a second address from the same snapshot
        assert registration._fence_mailbox_for_erasure(
            OWNERS, second_key, subject_uuid=self.SUBJECT, collection_base="ea_registrations", now=REGISTRATION_NOW,
        ) == registration.FENCE_FENCED
        index = self._fence_index(rdb, self.SUBJECT)
        assert index is not None and index["keys"] == sorted({key, second_key}), "the fence recorded no index entry"   # both keys, accumulated
        with patch.object(registration, "_release_claims_naming", side_effect=StoreUnavailable("owners sweep down")):
            assert asyncio.run(registration.process_optout(self.SUBJECT)).processed is True
        assert _tombstoned(self.SUBJECT) and key not in rdb.docs(OWNERS) and second_key not in rdb.docs(OWNERS)
        assert self._fence_index(rdb, self.SUBJECT) is None

    def test_the_terminal_primitive_releases_a_claim_from_the_index_alone(self, rdb):
        # 72a92ae, isolated primitive. End to end the index's recorded KEYS are
        # invisible: whenever they hold a key, the caller's current-row seed or
        # the commit's own transactional query holds the same one, so deleting
        # the keys — or the record written by the fence branch that merely
        # TOUCHES an already-own claim — leaves the whole suite green (two
        # lenses measured exactly that). With NO seed and the owners query
        # silenced, the index keys are the only remaining path, which is what
        # keeps them from being deleted silently. What this does NOT claim is
        # that the keys close the set: the index DOCUMENT's presence in the
        # read set does that, and the docstrings now say so.
        key = _owner_key(VICTIM_EMAIL)
        rdb.seed(OWNERS, key, {"uuid": self.SUBJECT, "collection": "early_adopters", "verified": True})
        assert registration._fence_mailbox_for_erasure(          # the own-claim touch branch
            OWNERS, key, subject_uuid=self.SUBJECT, collection_base="early_adopters", now=REGISTRATION_NOW,
        ) == registration.FENCE_FENCED
        real_where_ids = FakeTransaction.where_ids

        def without_the_owner_query(self, collection, field, value):
            return [] if collection == OWNERS else real_where_ids(self, collection, field, value)

        with patch.object(FakeTransaction, "where_ids", without_the_owner_query):
            assert stores.tombstone_subject_releasing_claims(self.SUBJECT, OWNERS, []) == 1, "no seed and no query: the index keys released nothing"
        assert key not in rdb.docs(OWNERS)
        assert _tombstoned(self.SUBJECT) and self._fence_index(rdb, self.SUBJECT) is None

    def test_a_fence_after_the_tombstone_writes_neither_claim_nor_index(self, rdb):
        # pin: a fence that runs after the terminal commit reads the
        # tombstone and writes nothing — no claim, no index entry.
        key = _owner_key(VICTIM_EMAIL)
        subject = _register_and_verify(rdb)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        writes = _count_owner_writes(rdb)
        assert registration._fence_mailbox_for_erasure(
            OWNERS, key, subject_uuid=subject, collection_base="early_adopters", now=REGISTRATION_NOW,
        ) == registration.FENCE_ERASED
        assert writes["n"] == 0 and key not in rdb.docs(OWNERS) and self._fence_index(rdb, subject) is None
