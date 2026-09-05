"""Firestore-backed OAuth state — transactional, hash-only, env-isolated.

This is the state layer Authlib cannot supply (D-ALTON-AUTHLIB, WP-C). It
owns: credential-digest validation caching (T P0-1), transactional
authorization-code claim / refresh rotation / OTP consume (T P0-3),
issuer/audience/scope binding on every token (T P0-4), one bearer path that
accepts ACCESS + PAT and rejects REFRESH with grant-family revocation
(T P0-5), and environment-namespaced collections (T P0-8).

Every read path raises ``StoreUnavailable`` when the backend cannot be
consulted — an outage is never an open gate (S111; boundary maps it to a
retryable 503, never invalid_token/invalid_grant).
"""

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from verifimind_mcp.oauth import config
from verifimind_mcp.oauth.core import (
    ACCESS,
    ACCESS_TOKEN_TTL,
    AUTHORIZATION_CODE_TTL,
    PAT,
    PAT_TTL,
    REFRESH,
    REFRESH_TOKEN_TTL,
    MintedToken,
    constant_time_equals,
    credential_digest,
    parse_token,
    sha256_hex,
)

VALIDATION_CACHE_TTL = 60
VERIFICATION_CODE_TTL = 15 * 60
VERIFICATION_MAX_ATTEMPTS = 5
AUTHORIZE_SESSION_TTL = 15 * 60
CLIENT_UNUSED_TTL = 30 * 24 * 3600
_TXN_MAX_ATTEMPTS = 8

_BASE_CLIENTS = "oauth_clients"
_BASE_CODES = "oauth_codes"
_BASE_TOKENS = "oauth_tokens"
_BASE_VERIFICATIONS = "oauth_email_verifications"
_BASE_SESSIONS = "oauth_authorize_sessions"
_BASE_TOMBSTONES = "oauth_revocations"


class StoreUnavailable(Exception):
    """The OAuth store cannot be consulted; callers must fail closed."""


class TransactionConflict(Exception):
    """Optimistic-concurrency conflict: a read document changed before commit.
    Defined here (production) so the test fake imports it, never the reverse."""


class _RefreshReuseDetected(Exception):
    """Internal: a rotated refresh token was replayed; carries the grant id
    so the family is revoked post-transaction (queries can't run in a txn)."""

    def __init__(self, grant_id: str):
        super().__init__("refresh token reuse detected")
        self.grant_id = grant_id


class RefreshRejected(Exception):
    """The presented refresh token cannot be rotated: it is unknown, expired,
    revoked, tombstoned, of the wrong kind, or its persisted identity does not
    match what the caller claimed for it. A DENIAL, never an outage — Authlib
    normalizes it to ``invalid_grant`` (CS round 3 F1 / T S157 Finding 1)."""


def _db():
    from verifimind_mcp.registration import _get_firestore

    db = _get_firestore()
    if db is None:
        raise StoreUnavailable("firestore unavailable")
    return db


def _backend_failure(exc: BaseException) -> bool:
    """True for a mid-life Firestore RPC failure. The client is memoized, so
    _db() only catches CONSTRUCTION failure; without this, a ServiceUnavailable
    during .get() escaped as a generic exception and the boundary reported
    401 invalid_token instead of a retryable 503 — telling healthy clients
    their credentials were bad during an outage."""
    module = type(exc).__module__ or ""
    # grpc.* is defence in depth: GAPIC wraps every Firestore RPC, so a raw
    # transport error is not a reachable production shape — but it IS a
    # backend failure if it ever surfaces (S159 F3 lens, scenario D4).
    return (
        module.startswith("google.api_core")
        or module.startswith("google.auth")
        or module == "grpc"
        or module.startswith("grpc.")
    )


def is_backend_failure(exc: BaseException) -> bool:
    """True when ``exc`` — or any exception it was raised *from* or *during*
    (``__cause__`` first, then ``__context__`` unless suppressed; bounded) —
    is a backend RPC failure.

    CS round 2, F3: the Firestore transactional wrapper retries ``Aborted``
    and then raises a plain ``ValueError`` *from* the last one; and when the
    very first ``BeginTransaction`` RPC fails, its rollback path raises
    ``ValueError('...cannot be rolled back')`` whose only link to the failed
    RPC is ``__context__``. Looking at the outer exception alone — or at
    ``__cause__`` alone — lets both escape as a generic 500.
    """
    node: Optional[BaseException] = exc
    for _ in range(8):
        if node is None:
            return False
        if _backend_failure(node):
            return True
        following = node.__cause__
        if following is None and not node.__suppress_context__:
            following = node.__context__
        node = following
    return False


def _guarded(operation: str):
    """Every raw Firestore call maps a backend failure to ``StoreUnavailable``
    so the OAuth layer fails CLOSED (retryable 503), never generic (500).
    ``StoreUnavailable`` and application signals raised inside the guarded
    call pass through unchanged; so do genuine programming errors."""

    def decorate(fn):
        def run(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (StoreUnavailable, _RefreshReuseDetected, RefreshRejected):
                raise
            except Exception as exc:  # noqa: BLE001
                if is_backend_failure(exc):
                    raise StoreUnavailable(
                        f"{operation} failed: {type(exc).__name__}"
                    ) from exc
                raise

        run.__name__ = fn.__name__
        run.__doc__ = fn.__doc__
        run.__wrapped__ = fn
        return run

    return decorate


def _now() -> float:
    return time.time()


# ── env-namespaced collection names (resolved per call, T P0-8) ─────────────

def _c(base: str) -> str:
    return config.current_environment().collection(base)


def c_clients() -> str:
    return _c(_BASE_CLIENTS)


def c_tokens() -> str:
    return _c(_BASE_TOKENS)


@_guarded("read")
def _read(collection: str, doc_id: str) -> Optional[dict]:
    doc = _db().collection(collection).document(doc_id).get()
    return (doc.to_dict() or {}) if doc.exists else None


# ── transaction runner (real Firestore + fake, uniform interface) ───────────

class _RealTxn:
    def __init__(self, db, transaction):
        self._db, self._t = db, transaction

    def get_dict(self, collection: str, doc_id: str) -> Optional[dict]:
        snap = self._db.collection(collection).document(doc_id).get(transaction=self._t)
        return (snap.to_dict() or {}) if snap.exists else None

    def set(self, collection: str, doc_id: str, data: dict) -> None:
        self._t.set(self._db.collection(collection).document(doc_id), data)

    def update(self, collection: str, doc_id: str, fields: dict) -> None:
        self._t.update(self._db.collection(collection).document(doc_id), fields)

    def delete(self, collection: str, doc_id: str) -> None:
        self._t.delete(self._db.collection(collection).document(doc_id))


@_guarded("transaction")
def run_transaction(func: Callable[[Any], Any]) -> Any:
    """Run func(txn) atomically. func may read then write via the txn; on
    optimistic-concurrency conflict it is retried with fresh reads.

    Backend failures anywhere in the real path — BeginTransaction, reads,
    commit, the exhausted-retries wrapper, rollback — surface as
    ``StoreUnavailable`` through ``_guarded`` (CS round 2, F3)."""
    db = _db()
    if getattr(db, "is_fake", False):
        for _ in range(_TXN_MAX_ATTEMPTS):
            txn = db.new_transaction()
            result = func(txn)
            try:
                txn._commit()
                return result
            except TransactionConflict:
                continue
        raise StoreUnavailable("transaction contention")
    from google.cloud import firestore

    @firestore.transactional
    def wrapped(transaction):
        return func(_RealTxn(db, transaction))

    return wrapped(db.transaction())


# ── validation cache keyed by FULL-credential digest (T P0-1) ───────────────

_validation_cache: Dict[str, tuple] = {}


def _cache_get(digest: str) -> Optional["TokenRecord"]:
    entry = _validation_cache.get(digest)
    if entry and _now() < entry[0]:
        return entry[1]
    if entry:
        _validation_cache.pop(digest, None)
    return None


def _cache_put(digest: str, record: "TokenRecord") -> None:
    horizon = min(_now() + VALIDATION_CACHE_TTL, record.expires_at)
    if horizon > _now():
        _validation_cache[digest] = (horizon, record)


def clear_caches() -> None:
    """Any revocation clears the positive cache: local revocation is
    immediate; cross-instance is bounded by VALIDATION_CACHE_TTL."""
    _validation_cache.clear()


# ── clients (bounded DCR + pre-registration) ────────────────────────────────

@_guarded("register_client")
def register_client(
    *, client_name: str, redirect_uris: List[str], registration_path: str
) -> str:
    import secrets as _secrets

    client_id = f"vmc_{_secrets.token_urlsafe(12)}"
    _db().collection(c_clients()).document(client_id).set({
        "client_id": client_id,
        "client_name": str(client_name)[:120],
        "redirect_uris": [str(u)[:512] for u in redirect_uris][:8],
        "registration_path": registration_path,
        "token_endpoint_auth_method": "none",
        "created_at": _now(),
        "last_used_at": _now(),
    })
    return client_id


def get_client(client_id: str) -> Optional[dict]:
    data = _read(c_clients(), str(client_id)[:64])
    if data is None:
        return None
    # Unused-client expiry (T P0-9): an untouched DCR client ages out.
    if _now() - float(data.get("last_used_at", data.get("created_at", 0))) > CLIENT_UNUSED_TTL:
        return None
    return data


# ── authorization codes (non-consuming read; claim happens in save_token) ───

@_guarded("persist_code")
def persist_code(
    *, code_id: str, code_secret_hash: str, client_id: str, subject_uuid: str,
    redirect_uri: str, code_challenge: str, scope: str,
) -> None:
    _db().collection(_c(_BASE_CODES)).document(code_id).set({
        "code_id": code_id,
        "secret_hash": code_secret_hash,
        "client_id": client_id,
        "subject_uuid": subject_uuid,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "scope": scope,
        "created_at": _now(),
        "expires_at": _now() + AUTHORIZATION_CODE_TTL,
        "used": False,
    })


def read_code(code_id: str) -> Optional[dict]:
    """Non-consuming read for Authlib query_authorization_code. Expiry/used
    filtered here; the atomic claim happens later in save_token."""
    data = _read(_c(_BASE_CODES), code_id)
    if data is None or data.get("used"):
        return None
    if _now() > float(data.get("expires_at", 0)):
        return None
    return data


# ── token records ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TokenRecord:
    token_id: str
    kind: str
    subject_uuid: str
    client_id: Optional[str]
    scope: str
    actor_class: str
    issuer: str
    audience: str
    grant_id: str
    parent_grant_id: str
    expires_at: float


def _token_doc(
    minted: MintedToken, *, subject_uuid: str, client_id: Optional[str],
    scope: str, actor_class: str, grant_id: str, ttl: float,
) -> dict:
    env = config.current_environment()
    return {
        "token_id": minted.token_id,
        "secret_hash": minted.secret_hash,
        "kind": minted.kind,
        "subject_uuid": subject_uuid,
        "client_id": client_id,
        "scope": scope,
        "actor_class": actor_class,
        "issuer": env.issuer,
        "audience": env.resource,
        "grant_id": grant_id,
        "issued_at": _now(),
        "expires_at": _now() + ttl,
        "revoked": False,
        "rotated_to": None,
    }


def _record_from(data: dict) -> TokenRecord:
    return TokenRecord(
        token_id=data.get("token_id", ""),
        kind=data.get("kind", ""),
        subject_uuid=data.get("subject_uuid", ""),
        client_id=data.get("client_id"),
        scope=data.get("scope", ""),
        actor_class=data.get("actor_class", "external"),
        issuer=data.get("issuer", ""),
        audience=data.get("audience", ""),
        grant_id=data.get("grant_id", ""),
        parent_grant_id=data.get("parent_grant_id", ""),
        expires_at=float(data.get("expires_at", 0)),
    )


# ── atomic code claim + token mint (T P0-3) ─────────────────────────────────

def claim_code_and_mint_tokens(
    *, code_id: str, access: MintedToken, refresh: Optional[MintedToken],
    subject_uuid: str, client_id: str, scope: str, actor_class: str,
    grant_id: str,
) -> None:
    """Transactionally consume the authorization code and write the token(s).

    Two concurrent valid exchanges both reach here; optimistic concurrency
    admits exactly one — the loser retries, sees the code used, and raises
    (T P0-3: exactly one token pair)."""
    codes, tokens = _c(_BASE_CODES), c_tokens()

    def _txn(txn):
        code = txn.get_dict(codes, code_id)
        if code is None or code.get("used"):
            raise StoreUnavailable("authorization code already consumed")
        txn.update(codes, code_id, {"used": True, "used_at": _now()})
        txn.set(tokens, access.token_id, _token_doc(
            access, subject_uuid=subject_uuid, client_id=client_id,
            scope=scope, actor_class=actor_class, grant_id=grant_id,
            ttl=ACCESS_TOKEN_TTL,
        ))
        if refresh is not None:
            txn.set(tokens, refresh.token_id, _token_doc(
                refresh, subject_uuid=subject_uuid, client_id=client_id,
                scope=scope, actor_class=actor_class, grant_id=grant_id,
                ttl=REFRESH_TOKEN_TTL,
            ))

    run_transaction(_txn)


# ── bearer validation: ACCESS + PAT, never REFRESH (T P0-5) ─────────────────

def validate_bearer(presented: str, *, allow_pat: bool = True) -> Optional[TokenRecord]:
    """Validate a bearer credential. Digest-keyed positive cache (T P0-1):
    a hit proves the exact secret; a miss verifies the secret hash and
    re-checks expiry/revocation. Raises StoreUnavailable on backend failure."""
    parsed = parse_token(presented)
    accepted = {ACCESS, PAT} if allow_pat else {ACCESS}
    if parsed is None or parsed.kind not in accepted:
        return None
    digest = credential_digest(presented)
    cached = _cache_get(digest)
    if cached is not None:
        if cached.kind not in accepted or _now() > cached.expires_at:
            return None
        # The cache holds a validated record, NOT an authorization decision:
        # revocation is re-checked on every hit via the tombstone, so a warm
        # entry on another instance cannot outlive a revoke.
        if _is_tombstoned(
            grant_id=cached.grant_id, parent_grant_id=cached.parent_grant_id,
            subject_uuid=cached.subject_uuid,
        ):
            _validation_cache.pop(digest, None)
            return None
        return cached
    data = _read(c_tokens(), parsed.token_id)
    if data is None:
        return None
    if data.get("revoked") or data.get("rotated_to"):
        return None
    if _now() > float(data.get("expires_at", 0)):
        return None
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return None
    record = _record_from(data)
    if record.kind not in accepted:
        return None
    if _is_tombstoned(
        grant_id=record.grant_id, parent_grant_id=record.parent_grant_id,
        subject_uuid=record.subject_uuid,
    ):
        return None
    _cache_put(digest, record)
    return record


def validate_refresh(presented: str) -> Optional[dict]:
    """Read (non-consuming) a refresh token record for Authlib's grant.

    Tombstone-complete (CS round 3 F1 / T S157 Finding 1): after the secret
    is verified, a grant, parent-grant, or subject tombstone denies exactly
    as it does for bearer validation. Before this, a refresh descendant the
    revocation sweep never saw — created by a rotation that committed after
    the sweep's query snapshot — validated on its own ``revoked`` flag alone
    and could rotate forever after the family was revoked.
    """
    parsed = parse_token(presented)
    if parsed is None or parsed.kind != REFRESH:
        return None
    data = _read(c_tokens(), parsed.token_id)
    if data is None or data.get("revoked") or data.get("rotated_to"):
        return None
    if data.get("kind") != REFRESH:
        # The wire prefix is caller-controlled; the PERSISTED kind is not.
        # All kinds share one collection and one id/secret scheme, so an
        # access or personal token re-prefixed `vmrt.` resolved to its own
        # record — same id, same secret — and rotated into a long-lived
        # refresh family (S160 lens finding, HIGH at fecc67c). Same check as
        # bearer validation's kind gate, mirrored here.
        return None
    if _now() > float(data.get("expires_at", 0)):
        return None
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return None
    if _is_tombstoned(
        grant_id=data.get("grant_id", ""),
        parent_grant_id=data.get("parent_grant_id", ""),
        subject_uuid=data.get("subject_uuid", ""),
    ):
        return None
    return data


def contain_refresh_reuse(presented: str) -> bool:
    """If a REAL (secret-valid) refresh token that has already been rotated is
    replayed, revoke its whole grant family — automatic-reuse detection
    (RFC 9700 §4.14.2, T P0-3/P0-5). Returns True when a family was revoked."""
    parsed = parse_token(presented)
    if parsed is None or parsed.kind != REFRESH:
        return False
    data = _read(c_tokens(), parsed.token_id)
    if data is None or data.get("kind") != REFRESH:
        return False  # persisted kind, never the wire prefix (see validate_refresh)
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return False
    if data.get("rotated_to") or data.get("revoked"):
        grant_id = data.get("grant_id")
        if grant_id:
            revoke_grant_family(grant_id)
            return True
    return False


# ── refresh rotation with reuse detection (T P0-3, P0-5) ────────────────────

def rotate_refresh_tokens(
    *, presented_refresh: str, access: MintedToken, refresh: MintedToken,
    subject_uuid: str, client_id: Optional[str], scope: str, actor_class: str,
    grant_id: str,
) -> None:
    """Atomically retire the presented refresh token and write its descendants.

    Tombstone-complete at COMMIT (CS round 3 F1 / T S157 Finding 1). The old
    token's PERSISTED record — read through the transaction, secret
    re-verified — names the grant, parent grant, and subject whose tombstone
    documents are read through that same transaction before the old token
    is marked or any descendant is written; a caller-supplied identity that
    disagrees with the record is refused. Because the tombstone keys are in
    the transaction's read set, a revocation that lands between these reads
    and the commit either conflicts this commit (the retry re-reads, sees
    the tombstone, and denies) or — under the server's pessimistic read
    locks — waits until this commit has happened. In that second case, as
    whenever the rotation commits first, the descendants inherit the
    tombstoned grant id and every validation path (bearer AND refresh)
    refuses them. Either way nothing a revocation could miss stays usable.

    Denials raise ``RefreshRejected`` (→ ``invalid_grant``) — including a
    replayed already-rotated token, which first revokes the whole family
    (RFC 9700 §4.14.2) and is then denied, never reported as an outage.
    Descendants keep the record's ``parent_grant_id`` so a parent-grant
    revocation reaches them too, whichever side of the commit it lands on.
    """
    parsed = parse_token(presented_refresh)
    if parsed is None or parsed.kind != REFRESH:
        raise RefreshRejected("not a refresh token")
    tokens, tombstones = c_tokens(), _c(_BASE_TOMBSTONES)
    old_id = parsed.token_id
    presented_hash = sha256_hex(parsed.secret)

    def _txn(txn):
        old = txn.get_dict(tokens, old_id)
        if old is None:
            raise RefreshRejected("refresh token unknown")
        if not constant_time_equals(presented_hash, old.get("secret_hash", "")):
            raise RefreshRejected("refresh token secret mismatch")
        if old.get("kind") != REFRESH:
            raise RefreshRejected("not a refresh token")
        persisted_grant = old.get("grant_id", "")
        persisted_parent = old.get("parent_grant_id", "")
        persisted_subject = old.get("subject_uuid", "")
        if not persisted_grant or not persisted_subject:
            # Absence denies: a record with no grant or subject would mint
            # descendants that no revocation could ever reach (S160 lens).
            raise RefreshRejected("refresh token record incomplete")
        if (
            persisted_grant != grant_id
            or persisted_subject != subject_uuid
            or (old.get("client_id") or None) != (client_id or None)
        ):
            raise RefreshRejected("refresh token identity mismatch")
        if old.get("rotated_to"):
            # Reuse of a rotated token = theft. Family revocation is a query,
            # which cannot run inside a transaction — signal out and revoke
            # the family post-commit.
            raise _RefreshReuseDetected(persisted_grant)
        if old.get("revoked"):
            raise RefreshRejected("refresh token revoked")
        if _now() > float(old.get("expires_at", 0)):
            raise RefreshRejected("refresh token expired")
        # Tombstones read THROUGH the transaction — the read set is what makes
        # a concurrent revocation conflict with this commit.
        for kind, key in (
            ("grant", persisted_grant),
            ("grant", persisted_parent),
            ("subject", persisted_subject),
        ):
            if key and txn.get_dict(tombstones, f"{kind}_{key}") is not None:
                raise RefreshRejected(f"{kind} revoked")
        txn.update(tokens, old_id, {"rotated_to": access.token_id, "rotated_at": _now()})
        access_doc = _token_doc(
            access, subject_uuid=persisted_subject, client_id=client_id, scope=scope,
            actor_class=actor_class, grant_id=persisted_grant, ttl=ACCESS_TOKEN_TTL,
        )
        refresh_doc = _token_doc(
            refresh, subject_uuid=persisted_subject, client_id=client_id, scope=scope,
            actor_class=actor_class, grant_id=persisted_grant, ttl=REFRESH_TOKEN_TTL,
        )
        if persisted_parent:
            # Descendants keep the parent link, so a parent-grant tombstone
            # that lands AFTER this commit — and the parent's sweep — still
            # reach them (S160 lens: they used to be written without it).
            access_doc["parent_grant_id"] = persisted_parent
            refresh_doc["parent_grant_id"] = persisted_parent
        txn.set(tokens, access.token_id, access_doc)
        txn.set(tokens, refresh.token_id, refresh_doc)

    try:
        run_transaction(_txn)
    except _RefreshReuseDetected as reuse:
        # Automatic reuse detection (RFC 9700 §4.14.2): the server cannot tell
        # attacker from victim, so the whole family is revoked — and the replay
        # is then DENIED (invalid_grant), not reported as an outage. Before:
        # the concurrent double-refresh race surfaced as a retryable 503 that
        # invited retries against a dead family (S160 lens).
        revoke_grant_family(reuse.grant_id)
        raise RefreshRejected("refresh token reuse detected") from reuse
    clear_caches()


# ── revocation (T P0-5): family-scoped, one presented credential ────────────

@_guarded("write_tombstone")
def _write_tombstone(kind: str, key: str) -> None:
    """Record a permanent revocation marker consulted at validation time.

    Query-then-update revocation has an unavoidable window: a rotation or PAT
    mint that commits after the sweep's snapshot produces a document the
    sweep never saw. A tombstone is consulted on every validation, so any
    credential belonging to a revoked grant or subject is refused even if its
    own document was written after the sweep.
    """
    if not key:
        return
    _db().collection(_c(_BASE_TOMBSTONES)).document(f"{kind}_{key}").set({
        "kind": kind, "key": key, "revoked_at": _now(),
    })


def _is_tombstoned(*, grant_id: str, parent_grant_id: str, subject_uuid: str) -> bool:
    for kind, key in (
        ("grant", grant_id), ("grant", parent_grant_id), ("subject", subject_uuid),
    ):
        if key and _read(_c(_BASE_TOMBSTONES), f"{kind}_{key}") is not None:
            return True
    return False


def _grant_id_for(presented: str) -> Optional[str]:
    parsed = parse_token(presented)
    if parsed is None:
        return None
    data = _read(c_tokens(), parsed.token_id)
    if data is None:
        return None
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return None
    return data.get("grant_id")


def revoke_credential(presented: str) -> bool:
    """RFC 7009: revoking ANY credential (access/refresh/PAT) tombstones its
    entire grant family and every descendant."""
    grant_id = _grant_id_for(presented)
    if not grant_id:
        return False
    revoked = revoke_grant_family(grant_id)
    return revoked > 0


@_guarded("revoke_grant_family")
def revoke_grant_family(grant_id: str) -> int:
    """Tombstone the grant AND every descendant (PATs minted from it).

    A grant-level tombstone is written FIRST so a credential created by a
    concurrent rotation/PAT-mint after the sweep snapshot is still refused at
    validation time — the query-then-update window cannot leave a live
    descendant behind. That guarantee is only as complete as the validation
    paths that consult the tombstone: bearer validation always did, and since
    T S157 Finding 1 refresh validation and the rotation commit do too.
    """
    db = _db()
    _write_tombstone("grant", grant_id)
    count = 0
    for field in ("grant_id", "parent_grant_id"):
        query = (
            db.collection(c_tokens())
            .where(field, "==", grant_id)
            .where("revoked", "==", False)
        )
        for doc in query.get():
            doc.reference.update({"revoked": True, "revoked_at": _now()})
            count += 1
    clear_caches()
    return count


@_guarded("revoke_all_for_subject")
def revoke_all_for_subject(subject_uuid: str) -> int:
    db = _db()
    _write_tombstone("subject", subject_uuid)
    query = (
        db.collection(c_tokens())
        .where("subject_uuid", "==", subject_uuid)
        .where("revoked", "==", False)
    )
    count = 0
    for doc in query.get():
        doc.reference.update({"revoked": True, "revoked_at": _now()})
        count += 1
    clear_caches()
    return count


# ── personal access tokens (explicit local lane, own family) ────────────────

@_guarded("issue_pat")
def issue_pat(
    *, subject_uuid: str, actor_class: str, parent_grant_id: str, scope: str = "mcp",
) -> MintedToken:
    """Mint a PAT as a DESCENDANT of the grant that authorized it.

    A PAT used to receive a brand-new family, so revoking the OAuth grant it
    came from could not reach it: a stolen 1-hour access token could be
    upgraded into a silent 180-day credential that survived the victim's
    revocation. It now carries `parent_grant_id`, and `revoke_grant_family`
    sweeps descendants (T P0-5: revoking any credential kills the family
    *and every descendant*).
    """
    from verifimind_mcp.oauth.core import mint_token
    import secrets as _secrets

    minted = mint_token(PAT)
    doc = _token_doc(
        minted, subject_uuid=subject_uuid, client_id=None, scope=scope,
        actor_class=actor_class, grant_id=f"pat_{_secrets.token_urlsafe(9)}",
        ttl=PAT_TTL,
    )
    doc["parent_grant_id"] = parent_grant_id
    _db().collection(c_tokens()).document(minted.token_id).set(doc)
    return minted


# ── email verification: transactional attempt cap + purpose binding ─────────

@_guarded("put_verification")
def put_verification(*, email: str, code: str, purpose: str, session_id: str) -> None:
    key = _verification_key(email, session_id)
    _db().collection(_c(_BASE_VERIFICATIONS)).document(key).set({
        "email_hash": _peppered(email.strip().lower()),
        "code_hash": _peppered(code),
        "purpose": purpose,
        "session_id_hash": _peppered(session_id),
        "created_at": _now(),
        "expires_at": _now() + VERIFICATION_CODE_TTL,
        "attempts": 0,
    })


def claim_verification(*, email: str, code: str, purpose: str, session_id: str) -> bool:
    """Transactional attempt-cap + purpose/session binding; consumed on
    success (T P0-3, P0-10)."""
    verifications = _c(_BASE_VERIFICATIONS)
    key = _verification_key(email, session_id)

    def _txn(txn) -> bool:
        data = txn.get_dict(verifications, key)
        if data is None:
            return False
        if _now() > float(data.get("expires_at", 0)):
            return False
        if data.get("purpose") != purpose:
            return False
        if data.get("session_id_hash") != _peppered(session_id):
            return False
        attempts = int(data.get("attempts", 0))
        if attempts >= VERIFICATION_MAX_ATTEMPTS:
            return False
        if constant_time_equals(_peppered(code), data.get("code_hash", "")):
            txn.delete(verifications, key)
            return True
        txn.update(verifications, key, {"attempts": attempts + 1})
        return False

    return run_transaction(_txn)


def _verification_key(email: str, session_id: str) -> str:
    return sha256_hex(f"{email.strip().lower()}|{session_id}")


def _peppered(value: str) -> str:
    import os

    pepper = os.getenv("OAUTH_HASH_PEPPER", "")
    return sha256_hex(f"{pepper}|{value}") if pepper else sha256_hex(value)


# ── authorize-page sessions ─────────────────────────────────────────────────

@_guarded("put_authorize_session")
def put_authorize_session(session_id: str, payload: Dict[str, Any]) -> None:
    _db().collection(_c(_BASE_SESSIONS)).document(sha256_hex(session_id)).set({
        **payload, "expires_at": _now() + AUTHORIZE_SESSION_TTL,
    })


def get_authorize_session(session_id: str) -> Optional[dict]:
    data = _read(_c(_BASE_SESSIONS), sha256_hex(session_id))
    if data is None or _now() > float(data.get("expires_at", 0)):
        return None
    return data


@_guarded("update_authorize_session")
def update_authorize_session(session_id: str, fields: Dict[str, Any]) -> None:
    _db().collection(_c(_BASE_SESSIONS)).document(sha256_hex(session_id)).update(fields)


@_guarded("drop_authorize_session")
def drop_authorize_session(session_id: str) -> None:
    _db().collection(_c(_BASE_SESSIONS)).document(sha256_hex(session_id)).delete()
