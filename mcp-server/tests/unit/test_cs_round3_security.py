"""CS round 3 (2026-09-05) security findings at ``fecc67c`` — regressions.

WP-A  refresh revocation was not tombstone-complete: ``validate_refresh``
      never consulted grant/parent-grant/subject tombstones and the rotation
      transaction never read them, so a refresh descendant created after a
      revocation sweep's query snapshot stayed rotatable forever
      (T S157 Finding 1; CS round 3 F1)
WP-B  environment isolation was fail-open and incomplete: a misdeclared
      staging identity fell back to the bare PRODUCTION collection names, and
      registration lookup, UUID tier resolution, both feedback writers, and
      Trinity history read/wrote production-named collections even from a
      correctly declared staging service (T S157 Findings 2 and 3)
LENS  the S160 adversarial lens on WP-A found that refresh validation bound
      the token KIND to the caller-controlled wire prefix, not the persisted
      record: an access token re-prefixed ``vmrt.`` rotated into a 30-day
      refresh family at ``fecc67c`` (HIGH); descendants dropped the parent
      link; an in-window replay was reported as an outage (503); an empty
      persisted identity minted unrevocable descendants

Every test whose comment begins with "fecc67c:" was demonstrated FAILING
against the ``fecc67c`` tree before it passed here — its FIRST failing
assertion is the stated one; assertions after that point are pinned on the
repaired tree only (sparse-worktree receipt in the S160 record). Tests marked
"pin:" pass at both heads; they exist so the repair is proven not to move a
neighbouring contract (T required regressions 1, 5, 6).
"""

import asyncio
import base64
import hashlib
import secrets
import types
import warnings
from unittest.mock import patch

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from verifimind_mcp import registration, registration_lookup
from verifimind_mcp.middleware import rate_limiter
from verifimind_mcp.oauth import authlib_server as A
from verifimind_mcp.oauth import config, core, stores
from verifimind_mcp.oauth.core import ACCESS, REFRESH, REFRESH_TOKEN_TTL
from verifimind_mcp.utils import trinity_history

from .oauth_fakes import FakeFirestore, FakeQuery, FakeTransaction, _Collection

UUID_P = "018f6b2a-aaaa-7abc-8def-0123456789ab"  # a production-side account
UUID_S = "018f6b2a-bbbb-7abc-8def-0123456789ab"  # a staging-side account
STAGE_ORIGIN = "https://staging.example"
PROD_ORIGIN = "https://verifimind.ysenseai.org"
FEEDBACK_TEXT = "The Trinity summary was clear; the CS questions were sharp."


# ── OAuth harness (same shape as test_oauth_core) ───────────────────────────

def _pkce():
    verifier = secrets.token_urlsafe(48)[:64]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


@pytest.fixture()
def dev_env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("K_SERVICE", raising=False)


@pytest.fixture()
def db(dev_env):
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


@pytest.fixture()
def server(db):
    return A.build_authorization_server()


def _client(redirect="https://c.example/cb"):
    return stores.register_client(
        client_name="CLI", redirect_uris=[redirect], registration_path="dcr"
    )


def _mkcode(cid, challenge, subject="subj-1", redirect="https://c.example/cb"):
    code = core.mint_authorization_code()
    stores.persist_code(
        code_id=code.token_id, code_secret_hash=code.secret_hash, client_id=cid,
        subject_uuid=subject, redirect_uri=redirect, code_challenge=challenge,
        scope="mcp",
    )
    return code


def _treq(**form):
    return A.build_request(
        method="POST", uri="http://localhost:8080/oauth/token",
        form_pairs=list(form.items()), query_pairs=[],
        headers={"content-type": "application/x-www-form-urlencoded"},
    )


def _exchange(server, cid, code_token, verifier, redirect="https://c.example/cb"):
    return server.create_token_response(_treq(
        grant_type="authorization_code", code=code_token, code_verifier=verifier,
        client_id=cid, redirect_uri=redirect,
    ))


def _issue_pair(server, subject="subj-1"):
    """A real code exchange through the Authlib server: one access/refresh
    pair under a fresh grant."""
    cid = _client()
    verifier, challenge = _pkce()
    code = _mkcode(cid, challenge, subject=subject)
    status, body, _ = _exchange(server, cid, code.token, verifier)
    assert status == 200, body
    refresh_id = core.parse_token(body["refresh_token"]).token_id
    grant_id = stores._read(stores.c_tokens(), refresh_id)["grant_id"]
    return types.SimpleNamespace(
        cid=cid, subject=subject, access=body["access_token"],
        refresh=body["refresh_token"], refresh_id=refresh_id, grant_id=grant_id,
    )


def _refresh_grant(server, pair, refresh=None):
    return server.create_token_response(_treq(
        grant_type="refresh_token", refresh_token=refresh or pair.refresh,
        client_id=pair.cid,
    ))


def _token_ids(db):
    return set(db.data.get(stores.c_tokens(), {}))


def _flip_last_char(token):
    return token[:-1] + ("A" if token[-1] != "A" else "B")


def _count_transactions(db):
    """Count how many transactions the fake hands out (attempt counter)."""
    counter = {"n": 0}
    original = db.new_transaction

    def counting():
        counter["n"] += 1
        return original()

    db.new_transaction = counting
    return counter


# ── WP-A · refresh validation is tombstone-complete ─────────────────────────

class TestRefreshValidationIsTombstoneComplete:
    def test_valid_non_tombstoned_refresh_remains_valid(self, db, server):
        # pin: T required regression 1 — the repair must not over-deny, and
        # tombstones for OTHER grants/subjects must not bite (Lens C).
        pair = _issue_pair(server)
        stores._write_tombstone("grant", "grant_unrelated")
        stores._write_tombstone("subject", "someone-else")
        assert stores.validate_refresh(pair.refresh)["grant_id"] == pair.grant_id
        status, body, _ = _refresh_grant(server, pair)
        assert status == 200 and body["refresh_token"] != pair.refresh

    def test_grant_tombstone_denies_refresh(self, db, server):
        # fecc67c: the record came back — T S157's exact probe shape
        # (grant_tombstone_present: True, late_refresh_accepted: True).
        pair = _issue_pair(server)
        # Tombstone ONLY, no sweep: the shape a sweep-missed descendant sees.
        stores._write_tombstone("grant", pair.grant_id)
        assert stores.validate_refresh(pair.refresh) is None

    def test_parent_grant_tombstone_denies_refresh(self, db, server):
        # fecc67c: a refresh record carrying parent_grant_id ignored the
        # parent's tombstone.
        minted = core.mint_token(REFRESH)
        doc = stores._token_doc(
            minted, subject_uuid="subj-p", client_id="vmc_x", scope="mcp",
            actor_class="external", grant_id="grant_child", ttl=REFRESH_TOKEN_TTL,
        )
        doc["parent_grant_id"] = "grant_parent"
        db.collection(stores.c_tokens()).document(minted.token_id).set(doc)
        assert stores.validate_refresh(minted.token) is not None  # otherwise valid
        stores._write_tombstone("grant", "grant_parent")
        assert stores.validate_refresh(minted.token) is None

    def test_subject_tombstone_denies_refresh(self, db, server):
        # fecc67c: an opted-out subject's refresh token still validated.
        pair = _issue_pair(server)
        stores._write_tombstone("subject", pair.subject)
        assert stores.validate_refresh(pair.refresh) is None

    def test_token_endpoint_denies_tombstoned_refresh_and_creates_nothing(self, db, server):
        # fecc67c: 200 and a fresh access/refresh pair written under the
        # revoked grant (T required regression 3).
        pair = _issue_pair(server)
        stores._write_tombstone("grant", pair.grant_id)
        before = _token_ids(db)
        status, body, _ = _refresh_grant(server, pair)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before
        assert db.data[stores.c_tokens()][pair.refresh_id]["rotated_to"] is None

    def test_descendant_of_a_rotation_that_committed_before_the_tombstone_is_dead(self, db, server):
        # fecc67c: the ordering T names "rotation commits first" — the sweep
        # never saw this descendant, the tombstone is the only thing that can
        # reach it, and refresh validation ignored the tombstone.
        pair = _issue_pair(server)
        status, body, _ = _refresh_grant(server, pair)  # rotation commits first
        assert status == 200
        descendant = body["refresh_token"]
        stores._write_tombstone("grant", pair.grant_id)  # revocation lands after
        assert stores.validate_refresh(descendant) is None
        assert stores.validate_bearer(body["access_token"]) is None
        status2, body2, _ = _refresh_grant(server, pair, refresh=descendant)
        assert status2 == 400 and body2["error"] == "invalid_grant"


# ── WP-A (lens) · the token KIND comes from the persisted record ────────────

class TestRefreshKindIsBoundToThePersistedRecord:
    """S160 Lens A finding (HIGH at fecc67c): the wire prefix is caller-
    controlled; the PERSISTED kind is not. All kinds share one collection
    and one id/secret scheme, so an ACCESS token re-prefixed ``vmrt.``
    resolved to its own record — same id, same secret — and rotated into a
    30-day refresh family: a stolen one-hour token upgraded itself."""

    @staticmethod
    def _as_refresh(token):
        return "vmrt." + token.split(".", 1)[1]

    def test_reprefixed_access_token_is_not_a_refresh_token(self, db, server):
        # fecc67c: 200, two new docs, and the victim's ACCESS doc marked
        # rotated_to (lens probe).
        pair = _issue_pair(server)
        forged = self._as_refresh(pair.access)
        assert stores.validate_refresh(forged) is None
        before = _token_ids(db)
        status, body, _ = _refresh_grant(server, pair, refresh=forged)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before
        access_id = core.parse_token(pair.access).token_id
        assert db.data[stores.c_tokens()][access_id]["rotated_to"] is None
        assert stores.validate_bearer(pair.access) is not None  # victim unharmed

    def test_reprefixed_pat_is_not_a_refresh_token(self, db, server):
        # fecc67c: validate_refresh returned the PAT record (only Authlib's
        # client check happened to stop the rotation; the store did not).
        pair = _issue_pair(server)
        pat = stores.issue_pat(
            subject_uuid=pair.subject, actor_class="external",
            parent_grant_id=pair.grant_id,
        ).token
        forged = self._as_refresh(pat)
        assert stores.validate_refresh(forged) is None
        before = _token_ids(db)
        status, body, _ = _refresh_grant(server, pair, refresh=forged)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before
        assert stores.validate_bearer(pat) is not None

    def test_reprefixed_revoked_access_token_does_not_drive_reuse_containment(self, db, server):
        # fecc67c: contain_refresh_reuse trusted the wire kind too — a revoked
        # ACCESS record re-prefixed as a refresh token was treated as a
        # replayed rotation and drove family containment.
        pair = _issue_pair(server)
        assert stores.revoke_credential(pair.access) is True
        assert stores.contain_refresh_reuse(self._as_refresh(pair.access)) is False


# ── WP-A · rotation commit is tombstone-complete (deterministic race) ───────

class TestRotationCommitIsTombstoneComplete:
    """T required regression 4. The rotation transaction has read the old
    token and the (absent) tombstones; the barrier fires inside its
    pre-commit window and commits a tombstone. The rotation must conflict,
    retry with fresh reads, see the tombstone, and DENY — creating nothing.

    Model disclosure: the in-memory fake is OPTIMISTIC (reads of absent
    documents are recorded at version 0, so the tombstone's creation makes
    the commit conflict). Real Firestore server-client transactions take
    read locks instead, so the same interleaving either aborts this commit
    (this shape) or delays the tombstone write until after it — the
    "rotation commits first" ordering, covered by
    ``test_descendant_of_a_rotation_that_committed_before_the_tombstone_is_dead``.
    """

    def test_grant_tombstone_in_the_window_denies_and_creates_nothing(self, db, server):
        # fecc67c: the tombstone key was never in the transaction's read set,
        # so the commit did not conflict — 200 and two live descendants under
        # a revoked grant.
        pair = _issue_pair(server)
        attempts = _count_transactions(db)
        before = _token_ids(db)
        db._next_barrier = lambda: stores._write_tombstone("grant", pair.grant_id)
        status, body, _ = _refresh_grant(server, pair)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before
        assert db.data[stores.c_tokens()][pair.refresh_id]["rotated_to"] is None
        # Conflict → retry → deny; not a first-pass denial.
        assert attempts["n"] == 2

    def test_subject_tombstone_in_the_window_denies_and_creates_nothing(self, db, server):
        # fecc67c: same window, opt-out (subject) tombstone — 200 and two
        # live descendants for an opted-out subject.
        pair = _issue_pair(server)
        attempts = _count_transactions(db)
        before = _token_ids(db)
        db._next_barrier = lambda: stores._write_tombstone("subject", pair.subject)
        status, body, _ = _refresh_grant(server, pair)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before
        assert attempts["n"] == 2

    def test_parent_grant_tombstone_in_the_window_denies_and_creates_nothing(self, db, server):
        # fecc67c: the parent-grant tombstone key was never in the read set
        # either — 200 and two live descendants under a revoked parent.
        pair = _issue_pair(server)
        db.collection(stores.c_tokens()).document(pair.refresh_id).update(
            {"parent_grant_id": "grant_parent"}
        )
        attempts = _count_transactions(db)
        before = _token_ids(db)
        db._next_barrier = lambda: stores._write_tombstone("grant", "grant_parent")
        status, body, _ = _refresh_grant(server, pair)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before
        assert attempts["n"] == 2

    def test_full_family_revocation_in_the_window_is_a_denial_not_an_outage(self, db, server):
        # fecc67c: the sweep's update of the old token DID make the commit
        # conflict, but the retry raised StoreUnavailable — a revoked token
        # reported as a retryable outage instead of invalid_grant.
        pair = _issue_pair(server)
        before = _token_ids(db)
        db._next_barrier = lambda: stores.revoke_grant_family(pair.grant_id)
        status, body, _ = _refresh_grant(server, pair)
        assert status == 400 and body["error"] == "invalid_grant"
        assert _token_ids(db) == before

    def test_concurrent_double_refresh_is_denied_and_revokes_the_family(self, db, server):
        # fecc67c: the loser's retry saw rotated_to, revoked the family, and
        # then surfaced StoreUnavailable — a denial reported as a retryable
        # 503 that invited retries against a dead family (S160 lens).
        pair = _issue_pair(server)
        winner = {}

        def race():
            # The other party's rotation commits inside this one's window.
            status, body, _ = _refresh_grant(server, pair)
            winner.update(status=status, body=body)

        db._next_barrier = race
        status, body, _ = _refresh_grant(server, pair)
        assert winner["status"] == 200
        assert status == 400 and body["error"] == "invalid_grant"
        # RFC 9700 §4.14.2: the server cannot tell attacker from victim, so
        # the whole family goes — including the winner's fresh pair.
        assert stores.validate_bearer(winner["body"]["access_token"]) is None
        assert stores.validate_refresh(winner["body"]["refresh_token"]) is None

    def test_descendants_keep_the_parent_link_so_a_late_parent_tombstone_reaches_them(self, db, server):
        # fecc67c: descendants were written without parent_grant_id, so a
        # parent-grant tombstone landing AFTER the rotation — and the parent's
        # sweep — missed them (S160 lens).
        pair = _issue_pair(server)
        db.collection(stores.c_tokens()).document(pair.refresh_id).update(
            {"parent_grant_id": "grant_parent"}
        )
        status, body, _ = _refresh_grant(server, pair)
        assert status == 200
        new_refresh_id = core.parse_token(body["refresh_token"]).token_id
        assert db.data[stores.c_tokens()][new_refresh_id]["parent_grant_id"] == "grant_parent"
        stores._write_tombstone("grant", "grant_parent")  # lands after the commit
        assert stores.validate_refresh(body["refresh_token"]) is None
        assert stores.validate_bearer(body["access_token"]) is None

    def test_store_outage_during_rotation_stays_an_outage(self, db, server):
        # pin (Lens C survivor E1): mapping RefreshRejected to invalid_grant
        # must never swallow a backend outage into a denial — the endpoint's
        # retryable 503 contract stands.
        pair = _issue_pair(server)
        before = _token_ids(db)
        with patch("verifimind_mcp.oauth.stores.run_transaction",
                   side_effect=stores.StoreUnavailable("firestore down")):
            with pytest.raises(stores.StoreUnavailable):
                _refresh_grant(server, pair)
        assert _token_ids(db) == before


# ── WP-A · rotation identity comes from the persisted record ────────────────

class TestRotationIdentityIsDerivedFromThePersistedRecord:
    """The transaction re-verifies the presented secret and derives grant,
    parent grant, and subject from the stored document; a caller claim that
    disagrees is refused. (fecc67c had no such exception class, so these
    assert on the outcome — nothing committed — and on the class NAME.)"""

    @staticmethod
    def _attempt(db, reason, **overrides):
        """The rotation must not commit, must deny with RefreshRejected, and
        must deny for the stated ``reason`` (Lens C: a name-only check
        could accept a denial from the wrong branch)."""
        before = _token_ids(db)
        kwargs = dict(
            access=core.mint_token(ACCESS), refresh=core.mint_token(REFRESH),
            scope="mcp", actor_class="external",
        )
        kwargs.update(overrides)
        committed = False
        try:
            stores.rotate_refresh_tokens(**kwargs)
            committed = True
        except Exception as exc:  # noqa: BLE001
            assert type(exc).__name__ == "RefreshRejected", type(exc).__name__
            assert reason in str(exc), str(exc)
        assert not committed, "the rotation must not commit"
        assert _token_ids(db) == before

    def test_forged_grant_identity_is_refused_without_writes(self, db, server):
        # fecc67c: rotation trusted the caller's grant_id and wrote both
        # descendants under the forged grant.
        pair = _issue_pair(server)
        self._attempt(
            db, "identity mismatch", presented_refresh=pair.refresh,
            subject_uuid=pair.subject, client_id=pair.cid, grant_id="grant_forged",
        )

    def test_forged_subject_is_refused_without_writes(self, db, server):
        # fecc67c: rotation trusted the caller's subject_uuid and wrote both
        # descendants for someone else.
        pair = _issue_pair(server)
        self._attempt(
            db, "identity mismatch", presented_refresh=pair.refresh,
            subject_uuid="someone-else", client_id=pair.cid, grant_id=pair.grant_id,
        )

    def test_forged_client_is_refused_without_writes(self, db, server):
        # fecc67c: rotation never compared the client to the persisted record.
        pair = _issue_pair(server)
        self._attempt(
            db, "identity mismatch", presented_refresh=pair.refresh,
            subject_uuid=pair.subject, client_id="vmc_someone_else",
            grant_id=pair.grant_id,
        )

    def test_wrong_secret_is_refused_inside_the_transaction(self, db, server):
        # fecc67c: the transaction never re-verified the secret — a token id
        # with the wrong secret rotated, guarded only by the caller's earlier
        # non-transactional read. The denial happens INSIDE the one
        # transaction that was opened (attempt count 1).
        pair = _issue_pair(server)
        attempts = _count_transactions(db)
        self._attempt(
            db, "secret mismatch", presented_refresh=_flip_last_char(pair.refresh),
            subject_uuid=pair.subject, client_id=pair.cid, grant_id=pair.grant_id,
        )
        assert attempts["n"] == 1

    def test_incomplete_persisted_identity_is_refused(self, db, server):
        # fecc67c: a record with an empty grant_id or subject_uuid rotated into
        # descendants nothing could ever revoke — the tombstone loop skips
        # empty keys (S160 lens). Absence denies.
        for missing in ("grant_id", "subject_uuid"):
            minted = core.mint_token(REFRESH)
            doc = stores._token_doc(
                minted, subject_uuid="subj-i", client_id="vmc_x", scope="mcp",
                actor_class="external", grant_id="grant_i", ttl=REFRESH_TOKEN_TTL,
            )
            doc[missing] = ""
            db.collection(stores.c_tokens()).document(minted.token_id).set(doc)
            self._attempt(
                db, "record incomplete", presented_refresh=minted.token,
                subject_uuid=doc["subject_uuid"], client_id="vmc_x",
                grant_id=doc["grant_id"],
            )


# ── WP-A · bearer and PAT contracts unchanged ───────────────────────────────

class TestBearerAndPatContractsUnchanged:
    # pin: T required regression 5.

    def test_access_and_pat_validate_refresh_does_not(self, db, server):
        pair = _issue_pair(server)
        pat = stores.issue_pat(
            subject_uuid=pair.subject, actor_class="external",
            parent_grant_id=pair.grant_id,
        ).token
        assert stores.validate_bearer(pair.access) is not None
        assert stores.validate_bearer(pat) is not None
        assert stores.validate_bearer(pair.refresh) is None
        assert stores.validate_bearer(pat, allow_pat=False) is None

    def test_grant_tombstone_denies_access_and_descendant_pat(self, db, server):
        pair = _issue_pair(server)
        pat = stores.issue_pat(
            subject_uuid=pair.subject, actor_class="external",
            parent_grant_id=pair.grant_id,
        ).token
        stores._write_tombstone("grant", pair.grant_id)
        assert stores.validate_bearer(pair.access) is None
        assert stores.validate_bearer(pat) is None

    def test_subject_tombstone_denies_pat(self, db, server):
        pair = _issue_pair(server)
        pat = stores.issue_pat(
            subject_uuid=pair.subject, actor_class="external",
            parent_grant_id=pair.grant_id,
        ).token
        stores._write_tombstone("subject", pair.subject)
        assert stores.validate_bearer(pat) is None

    def test_revoking_the_access_token_kills_refresh_and_descendant_pat(self, db, server):
        pair = _issue_pair(server)
        pat = stores.issue_pat(
            subject_uuid=pair.subject, actor_class="external",
            parent_grant_id=pair.grant_id,
        ).token
        assert stores.revoke_credential(pair.access) is True
        assert stores.validate_bearer(pair.access) is None
        assert stores.validate_bearer(pat) is None
        assert stores.validate_refresh(pair.refresh) is None


# ── WP-B harness: a Firestore fake that records every collection touched ────

class _RecordingQuery(FakeQuery):
    def where(self, field, op, value):
        assert op == "=="
        return _RecordingQuery(self._store, self._filters + [(field, value)], self._limit)

    def limit(self, n):
        return _RecordingQuery(self._store, self._filters, n)

    def count(self):
        query = self

        class _Count:
            def get(self):
                return [[types.SimpleNamespace(value=len(query.get()))]]

        return _Count()


class _RecordingCollection(_Collection):
    def where(self, field, op, value):
        return _RecordingQuery(self._store, []).where(field, op, value)

    def add(self, data):
        doc_id = secrets.token_urlsafe(8)
        self.document(doc_id).set(data)
        return None, self.document(doc_id)


class _RecordingTransaction(FakeTransaction):
    """Transactional reads/writes count as touches too, so ``touched`` is a
    complete I/O oracle rather than a ``.collection()`` oracle (Lens C)."""

    def get_dict(self, collection, doc_id):
        self._db.touched.append(collection)
        return super().get_dict(collection, doc_id)

    def set(self, collection, doc_id, data):
        self._db.touched.append(collection)
        super().set(collection, doc_id, data)

    def update(self, collection, doc_id, fields):
        self._db.touched.append(collection)
        super().update(collection, doc_id, fields)

    def delete(self, collection, doc_id):
        self._db.touched.append(collection)
        super().delete(collection, doc_id)


class RecordingFirestore(FakeFirestore):
    """Records EVERY collection name the code under test touches — through
    ``.collection()`` AND through transactions — so a test can assert zero
    I/O, or that only one environment's names were used; and how many times
    the code asked for a client at all (``client_calls``), so "fails before
    the client is opened" is an assertion, not a comment. ``seed`` writes
    fixtures without counting as caller I/O."""

    def __init__(self):
        super().__init__()
        self.touched = []
        self.client_calls = 0

    def handed_out(self):
        """``_get_firestore`` stand-in: counts, then returns this fake."""
        self.client_calls += 1
        return self

    def collection(self, name):
        self.touched.append(name)
        return _RecordingCollection(self._collection_store(name))

    def new_transaction(self):
        barrier = self._next_barrier
        self._next_barrier = None
        return _RecordingTransaction(self, barrier)

    def seed(self, collection, doc_id, data):
        self._collection_store(collection)._write(doc_id, dict(data))

    def docs(self, collection):
        return dict(self.data.get(collection, {}))


class HistoryFirestore:
    """Sync fake for ``read_trinity_history``'s nested path
    (collection → document → subcollection → order_by → limit → get)."""

    def __init__(self):
        self.touched = []
        self.records = {}  # {(collection, uuid): [record, ...]}

    def handed_out(self):
        return self

    def collection(self, name):
        self.touched.append(name)
        store = self

        class _Sub:
            def __init__(self, uuid):
                self._uuid = uuid

            def order_by(self, *args, **kwargs):
                return self

            def limit(self, n):
                return self

            def get(self):
                return [
                    types.SimpleNamespace(exists=True, to_dict=lambda r=r: dict(r))
                    for r in store.records.get((name, self._uuid), [])
                ]

        class _Doc:
            def __init__(self, uuid):
                self._uuid = uuid

            def collection(self, sub):
                return _Sub(self._uuid)

        class _Coll:
            def document(self, uuid):
                return _Doc(uuid)

        return _Coll()


class AsyncRecordingFirestore:
    """Async fake for ``_write_to_firestore``: records the full document path
    of every ``set``."""

    def __init__(self):
        self.touched = []
        self.writes = []

    def collection(self, name):
        self.touched.append(name)
        return _AsyncCollection(self, (name,))


class _AsyncCollection:
    def __init__(self, sink, path):
        self._sink, self._path = sink, path

    def document(self, doc_id):
        return _AsyncDoc(self._sink, self._path + (doc_id,))


class _AsyncDoc:
    def __init__(self, sink, path):
        self._sink, self._path = sink, path

    def collection(self, name):
        return _AsyncCollection(self._sink, self._path + (name,))

    async def set(self, record):
        self._sink.writes.append((self._path, dict(record)))


@pytest.fixture()
def staging_env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", STAGE_ORIGIN)
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("PILOT_INVITE_CODE", raising=False)


@pytest.fixture()
def misdeclared_staging(monkeypatch):
    """A staging service that did not declare its own origin: its identity
    cannot be resolved (T S157 probe: misdeclared_staging_collection)."""
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
    monkeypatch.delenv("VERIFIMIND_PUBLIC_ORIGIN", raising=False)
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("K_SERVICE", raising=False)
    with pytest.raises(config.EnvironmentMisconfigured):  # precondition
        config.current_environment()


@pytest.fixture()
def production_dark(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "production")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", PROD_ORIGIN)
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "false")
    monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "false")


@pytest.fixture()
def rdb():
    fake = RecordingFirestore()
    registration_lookup._clear_cache()
    rate_limiter._uuid_tier_cache.clear()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", side_effect=fake.handed_out):
        yield fake
    registration_lookup._clear_cache()
    rate_limiter._uuid_tier_cache.clear()
    stores.clear_caches()


@pytest.fixture()
def http(monkeypatch):
    import http_server
    from starlette.testclient import TestClient

    monkeypatch.setattr(rate_limiter, "_rate_limit_store", rate_limiter.RateLimitStore())
    with TestClient(http_server.app) as client:
        yield client


# ── WP-B · misdeclared staging fails before ANY read or write ───────────────

def _refused(response):
    """The explicit fail-closed HTTP answer: 503 bound to ITS cause (not an
    unrelated failure), uncacheable, retryable."""
    assert response.status_code == 503, (response.status_code, response.text)
    assert response.json()["error"] == "service_misconfigured"
    assert response.headers.get("cache-control") == "no-store"
    assert response.headers.get("retry-after")


def _no_io(rdb):
    """Zero reads, zero writes — and the client was never even asked for."""
    assert rdb.touched == []
    assert rdb.client_calls == 0


class TestMisdeclaredStagingFailsBeforeAnyIO:
    """T required regression 1 (WP-B): zero reads, zero writes, no fallback
    to a production collection name, and an explicit fail-closed answer on
    every surface. ``_no_io`` also proves the code never asked for a client:
    resolution happens BEFORE ``_get_firestore``, not merely before I/O."""

    def test_resolver_propagates_instead_of_falling_back(self, misdeclared_staging):
        # fecc67c: returned the bare production name (T S157 probe:
        # misdeclared_staging_collection: early_adopters).
        with pytest.raises(config.EnvironmentMisconfigured):
            registration.account_collection(registration.COLLECTION_EA)
        with pytest.raises(config.EnvironmentMisconfigured):
            registration.account_collection(registration.COLLECTION_FEEDBACK)

    def test_registration_lookup_is_unavailable_with_zero_reads(self, misdeclared_staging, rdb):
        # fecc67c: read production early_adopters and answered REGISTERED.
        rdb.seed("early_adopters", UUID_P, {"status": "active", "tier": "early_adopter"})
        state = registration_lookup.resolve_registration(UUID_P)
        assert state.state == registration_lookup.UNAVAILABLE
        _no_io(rdb)

    def test_tier_resolution_grants_nothing_with_zero_reads(self, misdeclared_staging, rdb):
        # fecc67c: read production early_adopters and granted "pioneer".
        rdb.seed("early_adopters", UUID_P, {"status": "active"})
        assert rate_limiter._resolve_uuid_tier(UUID_P) == "scholar"
        _no_io(rdb)

    def test_standalone_feedback_is_refused_with_zero_writes(self, misdeclared_staging, rdb, http):
        # fecc67c: 201 and a document in production "feedback".
        response = http.post(
            "/early-adopters/feedback",
            json={"content": FEEDBACK_TEXT, "feedback_type": "general"},
        )
        _refused(response)
        _no_io(rdb)
        assert rdb.data == {}

    def test_lightweight_register_cannot_report_persisted(self, misdeclared_staging, rdb, http):
        # fecc67c: 200 with persisted=true and a document in production
        # ea_registrations (T S157 probe: persisted: True).
        response = http.post("/register", json={"consent": True})
        _refused(response)
        assert response.json().get("persisted") is not True
        _no_io(rdb)
        assert rdb.data == {}

    def test_ea_register_is_refused_with_zero_writes(self, misdeclared_staging, rdb, http):
        # fecc67c: 201; the account went to production early_adopters and the
        # feedback to production feedback.
        response = http.post("/early-adopters/register", json={
            "email": "someone@example.com", "tc_accepted": True,
            "privacy_acknowledged": True, "feedback": FEEDBACK_TEXT,
            "feedback_type": "new_user",
        })
        _refused(response)
        _no_io(rdb)
        assert rdb.data == {}

    def test_whoami_and_status_are_refused_with_zero_reads(self, misdeclared_staging, rdb, http):
        # fecc67c: read production early_adopters and reported the account.
        rdb.seed("early_adopters", UUID_P, {
            "uuid": UUID_P, "status": "active", "tier": "early_adopter",
            "registered_at": "2026-01-01T00:00:00+00:00",
        })
        _refused(http.get("/whoami", params={"uuid": UUID_P}))
        _refused(http.get(f"/early-adopters/status/{UUID_P}"))
        _no_io(rdb)

    def test_optout_touches_nothing_and_is_not_a_success_receipt(self, misdeclared_staging, rdb):
        # fecc67c: `account_collection` fell back to the bare production name,
        # so the opt-out READ and DE-IDENTIFIED the production account; only
        # the later credential sweep (`stores._c`) raised, and the broad
        # except then answered "unavailable" — a silent partial mutation of
        # production behind a non-success receipt (Lens C corrected the
        # earlier "processed=True" reading of this failure).
        rdb.seed("early_adopters", UUID_P, {
            "uuid": UUID_P, "status": "active", "email": "someone@example.com",
        })
        result = asyncio.run(registration.process_optout(UUID_P))
        assert result.processed is False
        _no_io(rdb)
        assert rdb.docs("early_adopters")[UUID_P]["status"] == "active"

    def test_trinity_history_read_and_write_are_refused_with_zero_io(self, misdeclared_staging):
        # fecc67c: read and wrote production trinity_history.
        sync_db = HistoryFirestore()
        sync_db.records[("trinity_history", UUID_P)] = [{"tool": "run_full_trinity"}]
        with patch("verifimind_mcp.registration._get_firestore",
                   side_effect=sync_db.handed_out) as sync_client:
            assert trinity_history.read_trinity_history(UUID_P) == []
        assert sync_db.touched == [] and not sync_client.called
        async_db = AsyncRecordingFirestore()
        with patch("verifimind_mcp.utils.trinity_history._get_firestore_async",
                   return_value=async_db) as async_client:
            asyncio.run(trinity_history._write_to_firestore(
                UUID_P, {"validation_id": "v1", "tool": "run_full_trinity"},
            ))
        assert async_db.touched == [] and async_db.writes == []
        assert not async_client.called


# ── WP-B · declared staging sees only staging ───────────────────────────────

class TestDeclaredStagingSeesOnlyStaging:
    """T required regressions 2–5 (WP-B)."""

    def test_registration_lookup_cannot_see_production_and_sees_staging(self, staging_env, rdb):
        # fecc67c: production_record_seen_from_staging: True,
        # staging_record_seen_from_staging: False (T S157 probe).
        rdb.seed("early_adopters", UUID_P, {"status": "active", "tier": "early_adopter"})
        rdb.seed("staging_ea_registrations", UUID_S, {"status": "active", "tier": "ea"})
        production_side = registration_lookup.resolve_registration(UUID_P)
        assert production_side.state == registration_lookup.NOT_REGISTERED
        staging_side = registration_lookup.resolve_registration(UUID_S)
        assert staging_side.is_registered
        assert staging_side.source == "ea_registrations"  # logical store name
        assert set(rdb.touched) == {"staging_early_adopters", "staging_ea_registrations"}

    def test_tier_resolution_consults_only_staging(self, staging_env, rdb):
        # fecc67c: read production early_adopters — a production cohort
        # member was "pioneer" on staging and a staging member was not.
        rdb.seed("early_adopters", UUID_P, {"status": "active"})
        rdb.seed("staging_early_adopters", UUID_S, {"status": "active"})
        assert rate_limiter._resolve_uuid_tier(UUID_P) == "scholar"
        assert rate_limiter._resolve_uuid_tier(UUID_S) == "pioneer"
        assert set(rdb.touched) == {"staging_early_adopters"}

    def test_standalone_feedback_writes_only_the_staging_collection(self, staging_env, rdb):
        # fecc67c: wrote production "feedback" (T S157 probe:
        # collections_written: feedback).
        result = asyncio.run(registration.submit_feedback(
            registration.FeedbackRequest(content=FEEDBACK_TEXT, feedback_type="general")
        ))
        assert result.feedback_id in rdb.docs("staging_feedback")
        assert "feedback" not in rdb.data
        assert set(rdb.touched) == {"staging_feedback"}

    def test_registration_feedback_writes_only_the_staging_collection(self, staging_env, rdb):
        # fecc67c: the account went to staging_early_adopters but its feedback
        # went to production "feedback".
        result = asyncio.run(registration.register_early_adopter(
            registration.EarlyAdopterRegistration(
                email="new@example.com", tc_accepted=True, privacy_acknowledged=True,
                feedback=FEEDBACK_TEXT, feedback_type="new_user",
            )
        ))
        assert result.feedback_received is True
        assert len(rdb.docs("staging_feedback")) == 1
        assert len(rdb.docs("staging_early_adopters")) == 1
        assert not any(name in rdb.data for name in ("feedback", "early_adopters"))
        assert set(rdb.touched) == {"staging_early_adopters", "staging_feedback"}

    def test_account_status_reads_only_staging(self, staging_env, rdb):
        # pin: account reads were already namespaced; the resolver change
        # must not move them.
        rdb.seed("early_adopters", UUID_P, {
            "uuid": UUID_P, "status": "active", "registered_at": "2026-01-01T00:00:00+00:00",
        })
        assert asyncio.run(registration.get_ea_status(UUID_P)) is None
        assert rdb.touched == ["staging_early_adopters"]

    def test_trinity_history_read_and_write_use_only_staging(self, staging_env):
        # fecc67c: raw "trinity_history" in both directions.
        sync_db = HistoryFirestore()
        sync_db.records[("trinity_history", UUID_S)] = [{"tool": "production-only"}]
        sync_db.records[("staging_trinity_history", UUID_S)] = [{"tool": "staging-only"}]
        with patch("verifimind_mcp.registration._get_firestore", return_value=sync_db):
            tools = [r["tool"] for r in trinity_history.read_trinity_history(UUID_S)]
        assert tools == ["staging-only"]
        assert sync_db.touched == ["staging_trinity_history"]
        async_db = AsyncRecordingFirestore()
        with patch("verifimind_mcp.utils.trinity_history._get_firestore_async",
                   return_value=async_db):
            asyncio.run(trinity_history._write_to_firestore(
                UUID_S, {"validation_id": "v1", "tool": "run_full_trinity"},
            ))
        assert async_db.touched == ["staging_trinity_history"]
        assert async_db.writes[0][0] == ("staging_trinity_history", UUID_S, "validations", "v1")


# ── WP-B · production semantics preserved ───────────────────────────────────

class TestProductionSemanticsPreserved:
    """T required regression 6 (WP-B)."""

    def test_bare_collection_names_in_production_and_development(self, monkeypatch):
        # pin: no migration — production and local keep the historical names;
        # only a declared staging is prefixed.
        monkeypatch.delenv("K_SERVICE", raising=False)
        for name, origin in (("production", PROD_ORIGIN), ("development", "http://localhost:8080")):
            monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", name)
            monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", origin)
            for base in ("early_adopters", "ea_registrations", "feedback", "trinity_history"):
                assert registration.account_collection(base) == base
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
        monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", STAGE_ORIGIN)
        for base in ("early_adopters", "ea_registrations", "feedback", "trinity_history"):
            assert registration.account_collection(base) == f"staging_{base}"

    def test_production_callers_use_bare_names(self, monkeypatch, rdb):
        # pin (Lens C F4): every namespaced CALLER must still hit the bare
        # production collections — a caller that prefixed production would
        # pass every staging test and silently migrate live data.
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "production")
        monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", PROD_ORIGIN)
        monkeypatch.delenv("K_SERVICE", raising=False)
        monkeypatch.delenv("PILOT_INVITE_CODE", raising=False)
        rdb.seed("early_adopters", UUID_P, {
            "uuid": UUID_P, "status": "active", "tier": "early_adopter",
            "registered_at": "2026-01-01T00:00:00+00:00",
        })
        assert registration_lookup.resolve_registration(UUID_P).source == "early_adopters"
        assert rate_limiter._resolve_uuid_tier(UUID_P) == "pioneer"
        assert asyncio.run(registration.get_ea_status(UUID_P)).uuid == UUID_P
        result = asyncio.run(registration.register_early_adopter(
            registration.EarlyAdopterRegistration(
                email="prod@example.com", tc_accepted=True, privacy_acknowledged=True,
                feedback=FEEDBACK_TEXT, feedback_type="new_user",
            )
        ))
        assert result.feedback_received is True
        assert set(rdb.touched) == {"early_adopters", "feedback"}
        assert set(rdb.data) == {"early_adopters", "feedback"}
        sync_db = HistoryFirestore()
        sync_db.records[("trinity_history", UUID_P)] = [{"tool": "run_full_trinity"}]
        with patch("verifimind_mcp.registration._get_firestore", side_effect=sync_db.handed_out):
            assert trinity_history.read_trinity_history(UUID_P) == [{"tool": "run_full_trinity"}]
        assert sync_db.touched == ["trinity_history"]
        async_db = AsyncRecordingFirestore()
        with patch("verifimind_mcp.utils.trinity_history._get_firestore_async",
                   return_value=async_db):
            asyncio.run(trinity_history._write_to_firestore(
                UUID_P, {"validation_id": "v1", "tool": "run_full_trinity"},
            ))
        assert async_db.touched == ["trinity_history"]

    def test_anonymous_feedback_admitted_while_issuance_is_dark(self, production_dark, rdb, http):
        # pin: T D-157-5 — feedback is not an issuance path. It stays open
        # while both gates are dark, writes only the bare production feedback
        # collection, and mutates no account, credential, or mail state.
        assert config.issuance_enabled() is False
        with patch("verifimind_mcp.oauth.mailer.send_verification_email") as mail:
            response = http.post(
                "/early-adopters/feedback",
                json={"content": FEEDBACK_TEXT, "feedback_type": "general"},
            )
        assert response.status_code == 201
        assert rdb.touched == ["feedback"]
        assert set(rdb.data) == {"feedback"} and len(rdb.docs("feedback")) == 1
        assert not mail.called

    def test_feedback_stays_under_the_outer_rate_limiter(self):
        # pin: the anonymous IP bucket applies — feedback is not an exempt path.
        assert "/early-adopters/feedback" not in rate_limiter.EXEMPT_PATHS
        assert rate_limiter._is_rate_limit_exempt("/early-adopters/feedback", "POST") is False
