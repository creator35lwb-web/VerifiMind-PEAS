"""Framework-free OAuth 2.1 primitives — stdlib crypto only.

Token wire format: ``vm{kind}.{token_id}.{secret}`` where kind is one of
``at`` (access), ``rt`` (refresh), ``pat`` (personal access token). The
``token_id`` locates the store document; the ``secret`` never exists at
rest — only its SHA-256 digest is stored and comparison is constant-time.
A leaked database therefore yields no usable credential.

PKCE: S256 only (OAuth 2.1 posture for public clients); ``plain`` is
rejected.
"""

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional

ACCESS = "at"
REFRESH = "rt"
PAT = "pat"

_KIND_PREFIXES = {ACCESS: "vmat", REFRESH: "vmrt", PAT: "vmpat"}
_PREFIX_KINDS = {v: k for k, v in _KIND_PREFIXES.items()}

# Lifetimes (seconds). Access tokens are short-lived by design; refresh
# tokens rotate on every use; PATs are long-lived but individually
# revocable and rotatable.
ACCESS_TOKEN_TTL = 3600
REFRESH_TOKEN_TTL = 30 * 24 * 3600
PAT_TTL = 180 * 24 * 3600
AUTHORIZATION_CODE_TTL = 60


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def verify_pkce_s256(code_verifier: str, code_challenge: str) -> bool:
    """RFC 7636 S256: BASE64URL(SHA256(verifier)) == challenge."""
    if not (43 <= len(code_verifier) <= 128):
        return False
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return hmac.compare_digest(_b64url(digest).encode(), code_challenge.encode())


@dataclass(frozen=True)
class MintedToken:
    """A freshly minted credential. ``token`` exists only in this object
    and the response that carries it to the client — never at rest."""

    token: str
    token_id: str
    secret_hash: str
    kind: str


def mint_token(kind: str) -> MintedToken:
    token_id = secrets.token_urlsafe(12)
    secret = secrets.token_urlsafe(32)
    token = f"{_KIND_PREFIXES[kind]}.{token_id}.{secret}"
    return MintedToken(
        token=token,
        token_id=token_id,
        secret_hash=sha256_hex(secret),
        kind=kind,
    )


@dataclass(frozen=True)
class ParsedToken:
    kind: str
    token_id: str
    secret: str


def parse_token(presented: str) -> Optional[ParsedToken]:
    """Parse the wire format without touching any store. Returns None for
    anything malformed — the caller treats that as an invalid credential."""
    if not isinstance(presented, str) or len(presented) > 256:
        return None
    parts = presented.strip().split(".")
    if len(parts) != 3:
        return None
    prefix, token_id, secret = parts
    kind = _PREFIX_KINDS.get(prefix)
    if kind is None or not token_id or not secret:
        return None
    return ParsedToken(kind=kind, token_id=token_id, secret=secret)


def mint_authorization_code() -> MintedToken:
    """Authorization codes use the same id+hashed-secret shape (prefix
    ``vmac``) so the store never holds a usable code."""
    token_id = secrets.token_urlsafe(9)
    secret = secrets.token_urlsafe(24)
    return MintedToken(
        token=f"vmac.{token_id}.{secret}",
        token_id=token_id,
        secret_hash=sha256_hex(secret),
        kind="code",
    )


def parse_authorization_code(presented: str) -> Optional[ParsedToken]:
    if not isinstance(presented, str) or len(presented) > 128:
        return None
    parts = presented.strip().split(".")
    if len(parts) != 3 or parts[0] != "vmac":
        return None
    return ParsedToken(kind="code", token_id=parts[1], secret=parts[2])


def mint_verification_code() -> str:
    """8-digit numeric mailbox verification code (usability over entropy;
    brute force is bounded by the attempt counter and issuance limits)."""
    return f"{secrets.randbelow(100_000_000):08d}"
