"""Firestore-backed OAuth state — hashes at rest, fail-closed everywhere.

Collections:
  oauth_clients               registered clients (bounded DCR / pre-registered)
  oauth_codes                 authorization codes (hashed, single-use, 60s TTL)
  oauth_tokens                access / refresh / PAT records (hashed secrets)
  oauth_email_verifications   mailbox codes (email stored as SHA-256 hash only)
  oauth_authorize_sessions    short-lived authorize-page flow state

Every read path raises ``StoreUnavailable`` when the backend cannot be
consulted — an outage is never an open gate (S111; T D-152-4). Token
validation caches POSITIVE results for at most ``VALIDATION_CACHE_TTL``
seconds; revocation is honored within one TTL (T P0 #7 bounded-revocation
contract) and local revokes purge the cache immediately.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

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
    mint_authorization_code,
    mint_token,
    parse_authorization_code,
    parse_token,
    sha256_hex,
)

VALIDATION_CACHE_TTL = 60
VERIFICATION_CODE_TTL = 15 * 60
VERIFICATION_MAX_ATTEMPTS = 5
AUTHORIZE_SESSION_TTL = 15 * 60

_C_CLIENTS = "oauth_clients"
_C_CODES = "oauth_codes"
_C_TOKENS = "oauth_tokens"
_C_VERIFICATIONS = "oauth_email_verifications"
_C_SESSIONS = "oauth_authorize_sessions"


class StoreUnavailable(Exception):
    """The OAuth store cannot be consulted; callers must fail closed."""


def _db():
    from verifimind_mcp.registration import _get_firestore

    db = _get_firestore()
    if db is None:
        raise StoreUnavailable("firestore unavailable")
    return db


def _now() -> float:
    return time.time()


# ── validation cache (positive results only) ────────────────────────────────

_validation_cache: Dict[str, tuple] = {}


def _cache_get(token_id: str) -> Optional["TokenRecord"]:
    entry = _validation_cache.get(token_id)
    if entry and _now() < entry[0]:
        return entry[1]
    return None


def _cache_put(token_id: str, record: "TokenRecord") -> None:
    _validation_cache[token_id] = (_now() + VALIDATION_CACHE_TTL, record)


def _cache_drop(token_id: str) -> None:
    _validation_cache.pop(token_id, None)


def clear_caches() -> None:
    """Test seam."""
    _validation_cache.clear()


# ── clients ─────────────────────────────────────────────────────────────────

def register_client(
    *, client_name: str, redirect_uris: list, registration_path: str
) -> str:
    import secrets as _secrets

    client_id = f"vmc_{_secrets.token_urlsafe(12)}"
    _db().collection(_C_CLIENTS).document(client_id).set({
        "client_id": client_id,
        "client_name": str(client_name)[:120],
        "redirect_uris": [str(u)[:512] for u in redirect_uris][:8],
        "registration_path": registration_path,
        "token_endpoint_auth_method": "none",
        "created_at": _now(),
    })
    return client_id


def get_client(client_id: str) -> Optional[dict]:
    doc = _db().collection(_C_CLIENTS).document(str(client_id)[:64]).get()
    return (doc.to_dict() or {}) if doc.exists else None


# ── authorization codes ─────────────────────────────────────────────────────

def issue_code(
    *, client_id: str, subject_uuid: str, redirect_uri: str,
    code_challenge: str, scope: str,
) -> str:
    minted = mint_authorization_code()
    _db().collection(_C_CODES).document(minted.token_id).set({
        "secret_hash": minted.secret_hash,
        "client_id": client_id,
        "subject_uuid": subject_uuid,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "scope": scope,
        "created_at": _now(),
        "expires_at": _now() + AUTHORIZATION_CODE_TTL,
        "used": False,
    })
    return minted.token


def consume_code(presented: str) -> Optional[dict]:
    """Single-use exchange. Returns the code record or None (invalid /
    expired / already used). The used flag is set before returning; the
    residual check-then-set window is microseconds, additionally bounded
    by PKCE (a replayer still needs the verifier) and the 60s TTL —
    explicitly in CS review scope."""
    parsed = parse_authorization_code(presented)
    if parsed is None:
        return None
    ref = _db().collection(_C_CODES).document(parsed.token_id)
    doc = ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    if data.get("used") or _now() > float(data.get("expires_at", 0)):
        return None
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return None
    ref.update({"used": True, "used_at": _now()})
    return data


# ── tokens ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TokenRecord:
    token_id: str
    kind: str
    subject_uuid: str
    client_id: Optional[str]
    scope: str
    actor_class: str
    expires_at: float


_TTL_BY_KIND = {ACCESS: ACCESS_TOKEN_TTL, REFRESH: REFRESH_TOKEN_TTL, PAT: PAT_TTL}


def issue_token(
    *, kind: str, subject_uuid: str, client_id: Optional[str],
    scope: str = "mcp", actor_class: str = "external",
    parent_id: Optional[str] = None,
) -> MintedToken:
    minted = mint_token(kind)
    _db().collection(_C_TOKENS).document(minted.token_id).set({
        "token_id": minted.token_id,
        "secret_hash": minted.secret_hash,
        "kind": kind,
        "subject_uuid": subject_uuid,
        "client_id": client_id,
        "scope": scope,
        "actor_class": actor_class,
        "issued_at": _now(),
        "expires_at": _now() + _TTL_BY_KIND[kind],
        "revoked": False,
        "rotated_to": None,
        "parent_id": parent_id,
    })
    return minted


def validate_token(presented: str, *, expected_kind: str = ACCESS) -> Optional[TokenRecord]:
    """Full validation: parse → store lookup → constant-time verifier →
    kind / revoked / expiry. Positive results cached ≤60s; None results
    are never cached. Raises StoreUnavailable on backend failure."""
    parsed = parse_token(presented)
    if parsed is None or parsed.kind != expected_kind:
        return None
    cached = _cache_get(parsed.token_id)
    if cached is not None:
        return cached if cached.kind == expected_kind else None
    doc = _db().collection(_C_TOKENS).document(parsed.token_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    if data.get("revoked") or data.get("rotated_to"):
        return None
    if _now() > float(data.get("expires_at", 0)):
        return None
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return None
    record = TokenRecord(
        token_id=parsed.token_id,
        kind=data.get("kind", ""),
        subject_uuid=data.get("subject_uuid", ""),
        client_id=data.get("client_id"),
        scope=data.get("scope", ""),
        actor_class=data.get("actor_class", "external"),
        expires_at=float(data.get("expires_at", 0)),
    )
    if record.kind != expected_kind:
        return None
    _cache_put(parsed.token_id, record)
    return record


def rotate_refresh_token(presented: str) -> Optional[dict]:
    """OAuth 2.1 refresh rotation with reuse detection: a rotated refresh
    token presented again revokes the whole subject/client grant lineage."""
    parsed = parse_token(presented)
    if parsed is None or parsed.kind != REFRESH:
        return None
    ref = _db().collection(_C_TOKENS).document(parsed.token_id)
    doc = ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return None
    if data.get("revoked"):
        return None
    if data.get("rotated_to"):
        # Reuse of a rotated token = theft signal: revoke the lineage.
        revoke_all_for_subject(
            data.get("subject_uuid", ""), client_id=data.get("client_id")
        )
        return None
    if _now() > float(data.get("expires_at", 0)):
        return None
    new_access = issue_token(
        kind=ACCESS,
        subject_uuid=data["subject_uuid"],
        client_id=data.get("client_id"),
        scope=data.get("scope", "mcp"),
        actor_class=data.get("actor_class", "external"),
        parent_id=parsed.token_id,
    )
    new_refresh = issue_token(
        kind=REFRESH,
        subject_uuid=data["subject_uuid"],
        client_id=data.get("client_id"),
        scope=data.get("scope", "mcp"),
        actor_class=data.get("actor_class", "external"),
        parent_id=parsed.token_id,
    )
    ref.update({"rotated_to": new_refresh.token_id, "rotated_at": _now()})
    _cache_drop(parsed.token_id)
    return {
        "access": new_access,
        "refresh": new_refresh,
        "subject_uuid": data["subject_uuid"],
        "scope": data.get("scope", "mcp"),
    }


def revoke_token(presented: str) -> bool:
    """RFC 7009: revoke one presented credential (access, refresh, or PAT).
    Returns True when a matching live record was revoked."""
    parsed = parse_token(presented)
    if parsed is None:
        return False
    ref = _db().collection(_C_TOKENS).document(parsed.token_id)
    doc = ref.get()
    if not doc.exists:
        return False
    data = doc.to_dict() or {}
    if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
        return False
    ref.update({"revoked": True, "revoked_at": _now()})
    _cache_drop(parsed.token_id)
    return True


def revoke_all_for_subject(subject_uuid: str, *, client_id: Optional[str] = None) -> int:
    """Union revocation support: tombstone every live credential for a
    subject (optionally scoped to one client grant). Used by opt-out and
    refresh-reuse containment."""
    query = (
        _db().collection(_C_TOKENS)
        .where("subject_uuid", "==", subject_uuid)
        .where("revoked", "==", False)
    )
    revoked = 0
    for doc in query.get():
        data = doc.to_dict() or {}
        if client_id is not None and data.get("client_id") != client_id:
            continue
        doc.reference.update({"revoked": True, "revoked_at": _now()})
        _cache_drop(data.get("token_id", ""))
        revoked += 1
    return revoked


# ── email verification ──────────────────────────────────────────────────────

def put_verification(*, email: str, code: str, purpose: str) -> None:
    email_hash = sha256_hex(email.strip().lower())
    _db().collection(_C_VERIFICATIONS).document(email_hash).set({
        "email_hash": email_hash,
        "code_hash": sha256_hex(code),
        "purpose": purpose,
        "created_at": _now(),
        "expires_at": _now() + VERIFICATION_CODE_TTL,
        "attempts": 0,
    })


def check_verification(*, email: str, code: str) -> bool:
    """Constant-time code check with a hard attempt cap. The record is
    consumed on success."""
    email_hash = sha256_hex(email.strip().lower())
    ref = _db().collection(_C_VERIFICATIONS).document(email_hash)
    doc = ref.get()
    if not doc.exists:
        return False
    data = doc.to_dict() or {}
    if _now() > float(data.get("expires_at", 0)):
        return False
    attempts = int(data.get("attempts", 0))
    if attempts >= VERIFICATION_MAX_ATTEMPTS:
        return False
    ok = constant_time_equals(sha256_hex(code), data.get("code_hash", ""))
    if ok:
        ref.delete()
        return True
    ref.update({"attempts": attempts + 1})
    return False


# ── authorize-page sessions ─────────────────────────────────────────────────

def put_authorize_session(session_id: str, payload: Dict[str, Any]) -> None:
    _db().collection(_C_SESSIONS).document(sha256_hex(session_id)).set({
        **payload,
        "expires_at": _now() + AUTHORIZE_SESSION_TTL,
    })


def get_authorize_session(session_id: str) -> Optional[dict]:
    doc = _db().collection(_C_SESSIONS).document(sha256_hex(session_id)).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    if _now() > float(data.get("expires_at", 0)):
        return None
    return data


def update_authorize_session(session_id: str, fields: Dict[str, Any]) -> None:
    _db().collection(_C_SESSIONS).document(sha256_hex(session_id)).update(fields)


def drop_authorize_session(session_id: str) -> None:
    _db().collection(_C_SESSIONS).document(sha256_hex(session_id)).delete()
