"""Authlib protocol core behind a thin adapter (D-ALTON-AUTHLIB, WP-B).

Authlib owns standards parsing, grant/error validation, redirect/client
binding, PKCE handling, bearer validation structure, and revocation
primitives. VerifiMind owns the Firestore state via stores.py: minting is
bound INTO the transactional code-claim (save_token), so PKCE failure never
consumes a code and two concurrent valid exchanges yield exactly one token
pair (T P0-3). Only public clients (auth method "none"), response type
"code", grants authorization_code/refresh_token, PKCE S256-only.
"""

from typing import List, Optional

from authlib.oauth2.rfc6749 import (
    AuthorizationServer as _BaseAuthorizationServer,
)
from authlib.oauth2.rfc6749 import (
    ClientMixin,
    InvalidClientError,
    InvalidGrantError,
    OAuth2Request,
)
from authlib.oauth2.rfc6749.requests import OAuth2Payload
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant,
    RefreshTokenGrant,
)
from authlib.oauth2.rfc6750 import BearerTokenValidator
from authlib.oauth2.rfc6750.errors import (
    InsufficientScopeError,
    InvalidTokenError,
)
from authlib.oauth2.rfc7636 import CodeChallenge

from verifimind_mcp.oauth import config, stores
from verifimind_mcp.oauth.core import (
    ACCESS,
    REFRESH,
    MintedToken,
    mint_token,
)

SUPPORTED_SCOPE = "mcp"


# ── S256-only PKCE (T WP-B.3: stock CodeChallenge permits plain) ────────────

class S256OnlyCodeChallenge(CodeChallenge):
    SUPPORTED_CODE_CHALLENGE_METHOD = ["S256"]
    DEFAULT_CODE_CHALLENGE_METHOD = "S256"


# ── client / code models (ClientMixin, PKCE-attr code object) ───────────────

class VerifiMindClient(ClientMixin):
    def __init__(self, data: dict):
        self._d = data

    def get_client_id(self):
        return self._d["client_id"]

    def get_default_redirect_uri(self):
        uris = self._d.get("redirect_uris") or []
        return uris[0] if uris else None

    def get_allowed_scope(self, scope):
        if not scope:
            return ""
        allowed = {SUPPORTED_SCOPE}
        return " ".join(s for s in scope.split() if s in allowed)

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in (self._d.get("redirect_uris") or [])

    def check_client_secret(self, client_secret):
        return False  # public clients hold no secret

    def check_endpoint_auth_method(self, method, endpoint):
        return method == "none"

    def check_response_type(self, response_type):
        return response_type == "code"

    def check_grant_type(self, grant_type):
        return grant_type in ("authorization_code", "refresh_token")


class VerifiMindAuthorizationCode:
    """Minimal AuthorizationCodeMixin surface + PKCE attributes."""

    def __init__(self, data: dict):
        self._d = data
        self.code_challenge = data.get("code_challenge")
        self.code_challenge_method = "S256"

    def get_redirect_uri(self):
        return self._d.get("redirect_uri")

    def get_scope(self):
        return self._d.get("scope", SUPPORTED_SCOPE)

    @property
    def subject_uuid(self):
        return self._d.get("subject_uuid")

    @property
    def code_id(self):
        return self._d.get("code_id")

    @property
    def client_id(self):
        return self._d.get("client_id")


# ── grants: mint bound into the transactional claim ─────────────────────────

def _new_grant_id() -> str:
    import secrets as _secrets

    return f"grant_{_secrets.token_urlsafe(9)}"


class VMAuthorizationCodeGrant(AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["none"]

    def generate_authorization_code(self):
        from verifimind_mcp.oauth.core import mint_authorization_code

        minted = mint_authorization_code()
        self._vm_code_minted = minted
        return minted.token

    def save_authorization_code(self, code, request):
        from verifimind_mcp.oauth.core import parse_authorization_code

        minted = getattr(self, "_vm_code_minted", None)
        parsed = parse_authorization_code(code)
        challenge = request.payload.data.get("code_challenge", "")
        # Persist the RESOLVED scope (client.get_allowed_scope), never the raw
        # client-supplied payload scope — Authlib warns that storing caller
        # input here becomes privilege escalation the moment a second scope
        # exists.
        granted = request.client.get_allowed_scope(
            request.payload.scope or SUPPORTED_SCOPE
        ) or SUPPORTED_SCOPE
        stores.persist_code(
            code_id=parsed.token_id,
            code_secret_hash=minted.secret_hash,
            client_id=request.client.get_client_id(),
            subject_uuid=request.user,
            redirect_uri=request.payload.redirect_uri or request.client.get_default_redirect_uri(),
            code_challenge=challenge,
            scope=granted,
        )
        return code

    def query_authorization_code(self, code, client):
        from verifimind_mcp.oauth.core import (
            constant_time_equals,
            parse_authorization_code,
            sha256_hex,
        )

        parsed = parse_authorization_code(code)
        if parsed is None:
            return None
        data = stores.read_code(parsed.token_id)
        if data is None or data.get("client_id") != client.get_client_id():
            return None
        if not constant_time_equals(sha256_hex(parsed.secret), data.get("secret_hash", "")):
            return None
        return VerifiMindAuthorizationCode(data)

    def delete_authorization_code(self, authorization_code):
        # Consumption already happened atomically in save_token.
        return None

    def authenticate_user(self, authorization_code):
        return authorization_code.subject_uuid


class _RefreshCredential:
    """TokenMixin-ish wrapper Authlib's RefreshTokenGrant expects."""

    def __init__(self, data: dict):
        self._d = data

    def check_client(self, client):
        return self._d.get("client_id") == client.get_client_id()

    def get_client_id(self):
        return self._d.get("client_id")

    def get_scope(self):
        return self._d.get("scope", SUPPORTED_SCOPE)

    def is_expired(self):
        import time

        return time.time() > float(self._d.get("expires_at", 0))

    def is_revoked(self):
        return bool(self._d.get("revoked") or self._d.get("rotated_to"))

    @property
    def subject_uuid(self):
        return self._d.get("subject_uuid")


class VMRefreshTokenGrant(RefreshTokenGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["none"]
    INCLUDE_NEW_REFRESH_TOKEN = True

    def authenticate_refresh_token(self, refresh_token):
        data = stores.validate_refresh(refresh_token)
        if data is None:
            # A secret-valid but already-rotated token = automatic-reuse:
            # revoke the family, still deny (Authlib → invalid_grant).
            stores.contain_refresh_reuse(refresh_token)
            return None
        return _RefreshCredential(data)

    def authenticate_user(self, credential):
        return credential.subject_uuid

    def revoke_old_credential(self, refresh_token):
        return None  # rotation done atomically in save_token


# ── the server: query_client + transactional save_token ─────────────────────

class VMPayload(OAuth2Payload):
    """Payload preserving duplicate parameters so Authlib's multi-param
    rejection (e.g. two code_challenge values) actually fires (T P0-9)."""

    def __init__(self, data: dict, datalist: dict):
        self._data = data
        self._datalist = datalist

    @property
    def data(self):
        return self._data

    @property
    def datalist(self):
        from collections import defaultdict

        out = defaultdict(list)
        for key, values in self._datalist.items():
            out[key] = list(values)
        return out


class VMOAuth2Request(OAuth2Request):
    """Starlette-fed OAuth2Request. form/args expose the parsed params;
    payload carries duplicate-aware data for standards validation."""

    def __init__(self, method, uri, *, form, query, headers,
                 form_list, query_list):
        super().__init__(method, uri, headers=headers)
        merged = {**query, **form}
        merged_list = {}
        for source in (query_list, form_list):
            for key, values in source.items():
                merged_list.setdefault(key, [])
                merged_list[key].extend(values)
        self.payload = VMPayload(merged, merged_list)
        self._form = dict(form)
        self._args = dict(query)

    @property
    def form(self):
        return self._form

    @property
    def args(self):
        return self._args


class VerifiMindAuthorizationServer(_BaseAuthorizationServer):
    def create_oauth2_request(self, request):
        return request  # endpoints already build a VMOAuth2Request

    def create_json_request(self, request):
        return request

    def handle_response(self, status, body, headers):
        return (status, body, headers)

    def send_signal(self, name, *args, **kwargs):
        return None  # no framework signal bus

    def query_client(self, client_id):
        data = stores.get_client(client_id)
        return VerifiMindClient(data) if data else None

    def save_token(self, token, request):
        grant_type = request.payload.grant_type
        minted = getattr(request, "_vm_minted", None)
        if minted is None:
            raise InvalidGrantError()
        access: MintedToken = minted["access"]
        refresh: Optional[MintedToken] = minted["refresh"]
        grant_id: str = minted["grant_id"]
        scope = token.get("scope") or SUPPORTED_SCOPE

        if grant_type == "authorization_code":
            code = request.authorization_code
            stores.claim_code_and_mint_tokens(
                code_id=code.code_id,
                access=access,
                refresh=refresh,
                subject_uuid=code.subject_uuid,
                client_id=code.client_id,
                scope=scope,
                actor_class="external",
                grant_id=grant_id,
            )
        elif grant_type == "refresh_token":
            presented = request.form.get("refresh_token")
            record = stores.validate_refresh(presented) if presented else None
            if record is None:
                raise InvalidGrantError()
            try:
                stores.rotate_refresh_tokens(
                    presented_refresh=presented,
                    access=access,
                    refresh=refresh,
                    subject_uuid=record.get("subject_uuid", ""),
                    client_id=record.get("client_id"),
                    scope=scope,
                    actor_class=record.get("actor_class", "external"),
                    grant_id=record.get("grant_id", grant_id),
                )
            except stores.RefreshRejected:
                # The rotation transaction denied (revoked/tombstoned between
                # validation and commit, identity mismatch): a standards
                # invalid_grant, never a retryable outage (T S157 Finding 1).
                raise InvalidGrantError()
        else:
            raise InvalidGrantError()


def _make_generate_token(grant):
    """Bind a generate_token that mints opaque tokens and stashes them on the
    request for the transactional save_token."""

    def generate_token(user=None, scope=None, grant_type=None,
                       expires_in=None, include_refresh_token=True):
        from verifimind_mcp.oauth.core import ACCESS_TOKEN_TTL

        access = mint_token(ACCESS)
        refresh = mint_token(REFRESH) if include_refresh_token else None
        grant.request._vm_minted = {
            "access": access,
            "refresh": refresh,
            "grant_id": _new_grant_id(),
        }
        token = {
            "token_type": "Bearer",
            "access_token": access.token,
            "expires_in": ACCESS_TOKEN_TTL,
            "scope": scope or SUPPORTED_SCOPE,
        }
        if refresh is not None:
            token["refresh_token"] = refresh.token
        return token

    return generate_token


# ── bearer validation: Authlib structure + issuer/audience/resource ─────────

class _TokenLike:
    def __init__(self, record: stores.TokenRecord):
        self.record = record

    def is_expired(self):
        import time
        return time.time() > self.record.expires_at

    def is_revoked(self):
        return False  # revoked tokens are not returned by validate_bearer

    def get_scope(self):
        return self.record.scope


class VMBearerValidator(BearerTokenValidator):
    """Accepts ACCESS + PAT, rejects REFRESH (stores.validate_bearer), then
    enforces issuer/audience/resource + Authlib expiry/scope (T P0-4/P0-5)."""

    def authenticate_token(self, token_string):
        record = stores.validate_bearer(token_string, allow_pat=True)
        return _TokenLike(record) if record else None

    def validate_token(self, token, scopes, request=None, **kwargs):
        if token is None:
            raise InvalidTokenError()
        if token.is_expired():
            raise InvalidTokenError()
        env = config.current_environment()
        # Absence DENIES. A truthy guard here would let a token with a missing
        # issuer/audience (partial write, backfill, schema migration) satisfy
        # every environment — binding must be positively proven, not skipped.
        if token.record.issuer != env.issuer:
            raise InvalidTokenError()
        if token.record.audience != env.resource:
            raise InvalidTokenError()
        required = set(scopes or [SUPPORTED_SCOPE])
        held = set((token.get_scope() or "").split())
        if not required.issubset(held):
            raise InsufficientScopeError()
        return token


_bearer_validator = VMBearerValidator()


def authenticate_bearer(token_string: str, required_scopes=("mcp",)):
    """Run Authlib bearer validation (issuer/audience/scope/expiry) over a
    presented credential. Returns (TokenRecord|None, error_code|None):
    error_code is "insufficient_scope" (→403) or "invalid_token" (→401).
    Propagates StoreUnavailable so the caller fails closed with 503."""
    token = _bearer_validator.authenticate_token(token_string)
    try:
        _bearer_validator.validate_token(token, list(required_scopes))
    except InsufficientScopeError:
        return None, "insufficient_scope"
    except InvalidTokenError:
        return None, "invalid_token"
    return token.record, None


def build_authorization_server() -> VerifiMindAuthorizationServer:
    server = VerifiMindAuthorizationServer(scopes_supported=[SUPPORTED_SCOPE])
    server.register_grant(
        VMAuthorizationCodeGrant, [S256OnlyCodeChallenge(required=True)]
    )
    server.register_grant(VMRefreshTokenGrant)
    # Bind generate_token per grant instance at creation.
    _orig_get_token_grant = server.get_token_grant

    def get_token_grant(request):
        grant = _orig_get_token_grant(request)
        grant.generate_token = _make_generate_token(grant)
        return grant

    server.get_token_grant = get_token_grant
    return server


# ── Starlette ⇄ Authlib adapter (preserves duplicate params) ────────────────

def build_request(*, method: str, uri: str, form_pairs, query_pairs, headers) -> VMOAuth2Request:
    """Build a VMOAuth2Request from (key, value) pair lists so duplicate
    parameters survive into datalist (T P0-9)."""
    def _single(pairs):
        out = {}
        for key, value in pairs:
            out.setdefault(key, value)  # first wins for single-value access
        return out

    def _multi(pairs):
        out = {}
        for key, value in pairs:
            out.setdefault(key, []).append(value)
        return out

    return VMOAuth2Request(
        method, uri,
        form=_single(form_pairs), query=_single(query_pairs),
        headers=headers or {},
        form_list=_multi(form_pairs), query_list=_multi(query_pairs),
    )
