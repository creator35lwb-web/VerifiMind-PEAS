"""OAuth 2.1 HTTP surface: metadata, authorize ceremony, token, revoke, DCR.

Spec anchors: RFC 6749/8252 (code flow), RFC 7636 (PKCE, S256 only),
RFC 8414 (AS metadata), RFC 9728 (protected-resource metadata), RFC 7009
(revocation), RFC 7591 (bounded dynamic client registration).

Ceremony properties (T S152 P0 #1/#3): registration and sign-in happen
inside the authorization flow behind mailbox verification; duplicate-email
answers are uniform ("code sent") so account existence is never disclosed
and no existing credential is ever returned through lookup. Open-redirect
guard: an unregistered client or unlisted redirect_uri renders a 400 page
and never redirects.
"""

import os
import secrets as _secrets
import time
from html import escape
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, urlsplit

from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from verifimind_mcp.oauth import stores
from verifimind_mcp.oauth.core import ACCESS, PAT, REFRESH, verify_pkce_s256
from verifimind_mcp.oauth.mailer import MailerUnavailable, send_verification_email
from verifimind_mcp.oauth.stores import StoreUnavailable

_ORIGIN = "https://verifimind.ysenseai.org"
SCOPES_SUPPORTED = ["mcp"]


# ── issuance limits (mint limiting independent of caller identity, P0 #4) ───

class IssuanceLimiter:
    """Per-IP sliding windows for identity/credential minting endpoints."""

    LIMITS = {
        "send_code": (5, 3600),      # verification emails per IP per hour
        "dcr": (10, 86400),          # client registrations per IP per day
        "token": (30, 60),           # token-endpoint calls per IP per minute
    }

    def __init__(self):
        self._events: Dict[str, list] = {}

    def allow(self, action: str, ip: str) -> bool:
        limit, window = self.LIMITS[action]
        key = f"{action}:{ip}"
        now = time.time()
        events = [t for t in self._events.get(key, []) if now - t < window]
        if len(events) >= limit:
            self._events[key] = events
            return False
        events.append(now)
        self._events[key] = events
        return True

    def reset(self) -> None:
        self._events.clear()


issuance_limiter = IssuanceLimiter()


def _client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── discovery metadata ──────────────────────────────────────────────────────

async def protected_resource_metadata_handler(request):
    """RFC 9728 — tells MCP clients where the authorization server lives."""
    return JSONResponse({
        "resource": f"{_ORIGIN}/mcp",
        "authorization_servers": [_ORIGIN],
        "bearer_methods_supported": ["header"],
        "scopes_supported": SCOPES_SUPPORTED,
        "resource_documentation": f"{_ORIGIN}/setup",
    })


async def authorization_server_metadata_handler(request):
    """RFC 8414 — authorization-server metadata."""
    return JSONResponse({
        "issuer": _ORIGIN,
        "authorization_endpoint": f"{_ORIGIN}/oauth/authorize",
        "token_endpoint": f"{_ORIGIN}/oauth/token",
        "revocation_endpoint": f"{_ORIGIN}/oauth/revoke",
        "registration_endpoint": f"{_ORIGIN}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": SCOPES_SUPPORTED,
        "service_documentation": f"{_ORIGIN}/setup",
    })


# ── bounded dynamic client registration (RFC 7591) ──────────────────────────

def _redirect_uri_acceptable(uri: str) -> bool:
    try:
        parsed = urlsplit(uri)
    except ValueError:
        return False
    if parsed.scheme == "https" and parsed.hostname:
        return True
    # RFC 8252 loopback redirect for native/CLI clients.
    if parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1"):
        return True
    # Private-use scheme for desktop clients (reverse-DNS style).
    if parsed.scheme and "." in parsed.scheme and parsed.scheme != "http":
        return True
    return False


async def oauth_register_handler(request):
    if not issuance_limiter.allow("dcr", _client_ip(request)):
        return JSONResponse({"error": "too_many_requests"}, status_code=429)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid_client_metadata"}, status_code=400)
    redirect_uris = body.get("redirect_uris") or []
    if not isinstance(redirect_uris, list) or not redirect_uris:
        return JSONResponse({"error": "invalid_redirect_uri"}, status_code=400)
    if not all(
        isinstance(u, str) and _redirect_uri_acceptable(u) for u in redirect_uris
    ):
        return JSONResponse({"error": "invalid_redirect_uri"}, status_code=400)
    client_name = str(body.get("client_name") or "Unnamed MCP client")
    try:
        client_id = stores.register_client(
            client_name=client_name,
            redirect_uris=redirect_uris,
            registration_path="dcr",
        )
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    return JSONResponse({
        "client_id": client_id,
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
    }, status_code=201)


# ── authorize ceremony ──────────────────────────────────────────────────────

_PAGE_STYLE = (
    "<style>body{font-family:system-ui,sans-serif;max-width:26rem;"
    "margin:8vh auto;padding:0 1rem;color:#1c2733}h1{font-size:1.2rem}"
    "input,button{font-size:1rem;padding:.55rem;width:100%;margin:.3rem 0;"
    "box-sizing:border-box}button{background:#1a6b54;color:#fff;border:0;"
    "border-radius:6px;cursor:pointer}.muted{color:#5b6b7a;font-size:.85rem}"
    ".err{color:#a33}</style>"
)


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{escape(title)}</title>{_PAGE_STYLE}</head>"
        f"<body><h1>{escape(title)}</h1>{body}"
        f"<p class='muted'>VerifiMind-PEAS · free registration · "
        f"<a href='/terms'>Terms</a> · <a href='/privacy'>Privacy</a></p>"
        f"</body></html>"
    )


def _email_step(sid: str, notice: str = "") -> HTMLResponse:
    note = f"<p class='err'>{escape(notice)}</p>" if notice else ""
    return _page(
        "Connect to VerifiMind",
        f"{note}<p>Enter your email. We send a one-time code — this signs "
        "you in, or creates your free account if you are new. We never "
        "reveal whether an email is already registered.</p>"
        f"<form method='post'><input type='hidden' name='sid' value='{escape(sid)}'>"
        "<input type='hidden' name='action' value='send_code'>"
        "<input type='email' name='email' placeholder='you@example.com' required>"
        "<button type='submit'>Send code</button></form>",
    )


def _code_step(sid: str, email: str, notice: str = "") -> HTMLResponse:
    note = f"<p class='err'>{escape(notice)}</p>" if notice else ""
    return _page(
        "Enter your code",
        f"{note}<p>If the address is valid, a code is on its way to "
        f"<strong>{escape(email)}</strong>. It expires in 15 minutes.</p>"
        f"<form method='post'><input type='hidden' name='sid' value='{escape(sid)}'>"
        f"<input type='hidden' name='action' value='verify_code'>"
        f"<input type='hidden' name='email' value='{escape(email)}'>"
        "<input name='code' placeholder='8-digit code' required "
        "pattern='[0-9]{8}' inputmode='numeric'>"
        "<button type='submit'>Verify</button></form>",
    )


def _consent_step(sid: str, client_name: str) -> HTMLResponse:
    return _page(
        "Authorize access",
        f"<p><strong>{escape(client_name)}</strong> is asking to run "
        "VerifiMind validation tools (X, Z, CS, Trinity) as your account. "
        "Tools are free. Structured run records are kept as described in "
        "the <a href='/privacy'>Privacy Policy</a>.</p>"
        f"<form method='post'><input type='hidden' name='sid' value='{escape(sid)}'>"
        "<input type='hidden' name='action' value='consent'>"
        "<label><input type='checkbox' name='agree' required "
        "style='width:auto;margin-right:.4rem'>I accept the "
        "<a href='/terms'>Terms</a> and acknowledge the "
        "<a href='/privacy'>Privacy Policy</a></label>"
        "<button type='submit' name='decision' value='allow'>Allow</button>"
        "<button type='submit' name='decision' value='deny' "
        "style='background:#5b6b7a'>Deny</button></form>",
    )


def _redirect_error(redirect_uri: str, state: str, error: str) -> RedirectResponse:
    query = urlencode({"error": error, "state": state})
    return RedirectResponse(f"{redirect_uri}?{query}", status_code=302)


async def oauth_authorize_get_handler(request):
    params = request.query_params
    client_id = params.get("client_id", "")
    redirect_uri = params.get("redirect_uri", "")
    try:
        client = stores.get_client(client_id) if client_id else None
    except StoreUnavailable:
        return _page("Temporarily unavailable",
                     "<p>The sign-in service is briefly unavailable. "
                     "Please retry in a few minutes.</p>")
    # Open-redirect guard: never redirect for an unknown client/URI.
    if client is None or redirect_uri not in client.get("redirect_uris", []):
        return HTMLResponse(
            _page("Invalid authorization request",
                  "<p>The requesting client or its redirect address is not "
                  "registered.</p>").body,
            status_code=400,
        )
    state = params.get("state", "")
    if params.get("response_type") != "code":
        return _redirect_error(redirect_uri, state, "unsupported_response_type")
    code_challenge = params.get("code_challenge", "")
    if not code_challenge or params.get("code_challenge_method") != "S256":
        return _redirect_error(redirect_uri, state, "invalid_request")
    scope = params.get("scope", "mcp") or "mcp"
    sid = _secrets.token_urlsafe(24)
    try:
        stores.put_authorize_session(sid, {
            "client_id": client_id,
            "client_name": client.get("client_name", "MCP client"),
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "scope": scope,
            "email_verified": False,
            "email": "",
        })
    except StoreUnavailable:
        return _page("Temporarily unavailable",
                     "<p>The sign-in service is briefly unavailable. "
                     "Please retry in a few minutes.</p>")
    return _email_step(sid)


def _resolve_or_create_subject(email: str) -> Optional[str]:
    """Verified-mailbox subject resolution across BOTH account stores;
    creates a lightweight account when the email is new. Returns the
    stable UUID, or None when the backend is unavailable."""
    from verifimind_mcp.registration import (
        COLLECTION_EA,
        COLLECTION_REGISTRATIONS,
        _get_firestore,
        _now_iso,
    )
    from verifimind_mcp.utils.uuid_helper import generate_ea_uuid

    db = _get_firestore()
    if db is None:
        return None
    normalized = email.strip().lower()
    for collection in (COLLECTION_EA, COLLECTION_REGISTRATIONS):
        found = (
            db.collection(collection)
            .where("email", "==", normalized)
            .limit(1)
            .get()
        )
        if found:
            data = found[0].to_dict() or {}
            if data.get("status", "active") == "active":
                return data.get("uuid")
            return None  # revoked/deletion-requested accounts never resolve
    new_uuid = generate_ea_uuid()
    from verifimind_mcp.policies import PRIVACY_POLICY_VERSION, TERMS_VERSION
    db.collection(COLLECTION_REGISTRATIONS).document(new_uuid).set({
        "uuid": new_uuid,
        "email": normalized,
        "display_name": None,
        "tier": "ea",
        "registered_at": _now_iso(),
        "consent": True,
        "consent_ts": _now_iso(),
        "privacy_version": PRIVACY_POLICY_VERSION,
        "tc_version": TERMS_VERSION,
        "status": "active",
        "registration_path": "oauth_ceremony_v2",
        "email_verified": True,
    })
    return new_uuid


async def oauth_authorize_post_handler(request):
    form = await request.form()
    sid = str(form.get("sid", ""))
    action = str(form.get("action", ""))
    try:
        session = stores.get_authorize_session(sid) if sid else None
    except StoreUnavailable:
        session = None
    if session is None:
        return HTMLResponse(
            _page("Session expired",
                  "<p>This sign-in attempt expired. Return to your client "
                  "and connect again.</p>").body,
            status_code=400,
        )

    if action == "send_code":
        email = str(form.get("email", "")).strip()
        if "@" not in email or len(email) > 254:
            return _email_step(sid, "Please enter a valid email address.")
        if not issuance_limiter.allow("send_code", _client_ip(request)):
            return _email_step(
                sid, "Too many codes requested from this network — wait a "
                "little and try again.",
            )
        from verifimind_mcp.oauth.core import mint_verification_code
        code = mint_verification_code()
        try:
            stores.put_verification(email=email, code=code, purpose="authorize")
            send_verification_email(to_email=email, code=code, purpose="authorize")
        except (StoreUnavailable, MailerUnavailable):
            return HTMLResponse(
                _page("Verification unavailable",
                      "<p>Verification email cannot be sent right now — "
                      "this is a temporary server-side condition. Please "
                      "retry in a few minutes.</p>").body,
                status_code=503,
            )
        # Uniform answer whether or not the email already has an account.
        return _code_step(sid, email)

    if action == "verify_code":
        email = str(form.get("email", "")).strip()
        code = str(form.get("code", "")).strip()
        try:
            ok = stores.check_verification(email=email, code=code)
        except StoreUnavailable:
            ok = False
        if not ok:
            return _code_step(sid, email, "That code is not valid (or expired).")
        stores.update_authorize_session(sid, {
            "email_verified": True, "email": email.lower(),
        })
        return _consent_step(sid, session.get("client_name", "MCP client"))

    if action == "consent":
        redirect_uri = session["redirect_uri"]
        state = session.get("state", "")
        if str(form.get("decision", "")) != "allow":
            stores.drop_authorize_session(sid)
            return _redirect_error(redirect_uri, state, "access_denied")
        # Re-read: consent is only valid after mailbox verification.
        fresh = stores.get_authorize_session(sid) or {}
        if not fresh.get("email_verified"):
            return _email_step(sid, "Verify your email first.")
        subject = _resolve_or_create_subject(fresh.get("email", ""))
        if subject is None:
            return HTMLResponse(
                _page("Temporarily unavailable",
                      "<p>Account service is briefly unavailable — please "
                      "retry in a few minutes.</p>").body,
                status_code=503,
            )
        try:
            code = stores.issue_code(
                client_id=session["client_id"],
                subject_uuid=subject,
                redirect_uri=redirect_uri,
                code_challenge=session["code_challenge"],
                scope=session.get("scope", "mcp"),
            )
        except StoreUnavailable:
            return HTMLResponse(
                _page("Temporarily unavailable",
                      "<p>Please retry in a few minutes.</p>").body,
                status_code=503,
            )
        stores.drop_authorize_session(sid)
        query = urlencode({"code": code, "state": state})
        return RedirectResponse(f"{redirect_uri}?{query}", status_code=302)

    return HTMLResponse(_page("Invalid request", "<p>Unknown action.</p>").body,
                        status_code=400)


# ── token endpoint ──────────────────────────────────────────────────────────

def _token_response(access, refresh, scope: str) -> JSONResponse:
    from verifimind_mcp.oauth.core import ACCESS_TOKEN_TTL
    return JSONResponse({
        "access_token": access.token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL,
        "refresh_token": refresh.token,
        "scope": scope,
    }, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})


async def oauth_token_handler(request):
    if not issuance_limiter.allow("token", _client_ip(request)):
        return JSONResponse({"error": "too_many_requests"}, status_code=429)
    form = await request.form()
    grant_type = str(form.get("grant_type", ""))
    try:
        if grant_type == "authorization_code":
            code_record = stores.consume_code(str(form.get("code", "")))
            if code_record is None:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            if str(form.get("client_id", "")) != code_record.get("client_id"):
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            if str(form.get("redirect_uri", "")) != code_record.get("redirect_uri"):
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            if not verify_pkce_s256(
                str(form.get("code_verifier", "")),
                code_record.get("code_challenge", ""),
            ):
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            scope = code_record.get("scope", "mcp")
            subject = code_record["subject_uuid"]
            client_id = code_record.get("client_id")
            access = stores.issue_token(
                kind=ACCESS, subject_uuid=subject, client_id=client_id, scope=scope,
            )
            refresh = stores.issue_token(
                kind=REFRESH, subject_uuid=subject, client_id=client_id, scope=scope,
            )
            return _token_response(access, refresh, scope)

        if grant_type == "refresh_token":
            rotated = stores.rotate_refresh_token(str(form.get("refresh_token", "")))
            if rotated is None:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            return _token_response(
                rotated["access"], rotated["refresh"], rotated["scope"],
            )

        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)


async def oauth_revoke_handler(request):
    form = await request.form()
    try:
        stores.revoke_token(str(form.get("token", "")))
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    # RFC 7009: 200 regardless of whether the token matched.
    return JSONResponse({})


# ── personal access tokens (explicit local/legacy lane, D-153-4) ────────────

async def oauth_pat_handler(request):
    """POST /oauth/pat — mint a PAT for the subject authenticated by the
    presented OAuth access token. The PAT is the local-client credential;
    the UUID never is."""
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return JSONResponse(
            {"error": "invalid_token"}, status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        record = stores.validate_token(authorization[7:].strip(), expected_kind=ACCESS)
        if record is None:
            return JSONResponse(
                {"error": "invalid_token"}, status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        pat = stores.issue_token(
            kind=PAT,
            subject_uuid=record.subject_uuid,
            client_id=record.client_id,
            scope=record.scope,
            actor_class=record.actor_class,
        )
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    from verifimind_mcp.oauth.core import PAT_TTL
    return JSONResponse({
        "personal_access_token": pat.token,
        "expires_in": PAT_TTL,
        "usage": (
            "Send as 'Authorization: Bearer <token>' from local clients. "
            "Store it in an environment variable or secret store — never "
            "in a committed config, URL, or your UUID field."
        ),
    }, headers={"Cache-Control": "no-store"})
