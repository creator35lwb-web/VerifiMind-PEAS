"""OAuth HTTP surface — thin Starlette adapter over the Authlib core.

Authlib owns token/authorize/PKCE/error validation (authlib_server); this
module translates async Starlette I/O, runs the human email-verification
ceremony, and enforces the VerifiMind policy Authlib cannot: the default-off
issuance gate (T P0-7), mail-recipient containment + verified STARTTLS
(T P0-6/P0-8), the open-redirect pre-guard and consent-checkbox (T P0-9),
and env-bound metadata (T P0-8).
"""

import secrets as _secrets
import time
from html import escape
from typing import List, Tuple
from urllib.parse import urlencode, urlsplit

from authlib.oauth2.base import OAuth2Error
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from verifimind_mcp.oauth import config, stores
from verifimind_mcp.oauth.authlib_server import build_authorization_server, build_request
from verifimind_mcp.oauth.core import ACCESS, mint_verification_code
from verifimind_mcp.oauth.mailer import MailerUnavailable, send_verification_email
from verifimind_mcp.oauth.stores import StoreUnavailable

SCOPES_SUPPORTED = ["mcp"]
_server = None


def _authorization_server():
    global _server
    if _server is None:
        _server = build_authorization_server()
    return _server


# ── async Starlette → Authlib request (duplicate-preserving) ────────────────

async def _oauth_request(request, path: str):
    form_pairs: List[Tuple[str, str]] = []
    if request.method == "POST":
        form = await request.form()
        form_pairs = [(k, str(v)) for k, v in form.multi_items()]
    query_pairs = [(k, v) for k, v in request.query_params.multi_items()]
    env = config.current_environment()
    return build_request(
        method=request.method,
        uri=f"{env.origin}{path}",
        form_pairs=form_pairs,
        query_pairs=query_pairs,
        headers={k: v for k, v in request.headers.items()},
    )


def _client_ip(request) -> str:
    """Trusted-proxy client IP: Cloud Run appends the real client as the LAST
    XFF hop (T P0-9 — never trust the leftmost caller-supplied element)."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"


# ── issuance limits (persistent per-process; global + per-action) ───────────

class IssuanceLimiter:
    LIMITS = {
        "send_code": (5, 3600),
        "dcr": (10, 86400),
        "token": (30, 60),
        "pat": (5, 3600),
    }
    GLOBAL = (2000, 3600)

    def __init__(self):
        self._events = {}
        self._global = []

    def allow(self, action: str, ip: str) -> bool:
        now = time.time()
        gl, gw = self.GLOBAL
        self._global = [t for t in self._global if now - t < gw]
        if len(self._global) >= gl:
            return False
        limit, window = self.LIMITS[action]
        key = f"{action}:{ip}"
        events = [t for t in self._events.get(key, []) if now - t < window]
        if len(events) >= limit:
            self._events[key] = events
            return False
        events.append(now)
        self._events[key] = events
        self._global.append(now)
        return True

    def reset(self):
        self._events.clear()
        self._global.clear()


issuance_limiter = IssuanceLimiter()


def _issuance_blocked() -> bool:
    """T P0-7: while issuance is dark, NO credential/account mutation or mail."""
    return not config.issuance_enabled()


def _dark_json():
    return JSONResponse(
        {"error": "temporarily_unavailable",
         "error_description": "Credential issuance is not currently enabled."},
        status_code=503, headers={"Retry-After": "3600"},
    )


# ── discovery metadata (readable while dark; env-bound) ─────────────────────

async def protected_resource_metadata_handler(request):
    env = config.current_environment()
    return JSONResponse({
        "resource": env.resource,
        "authorization_servers": [env.issuer],
        "bearer_methods_supported": ["header"],
        "scopes_supported": SCOPES_SUPPORTED,
        "resource_documentation": f"{env.origin}/setup",
    })


async def authorization_server_metadata_handler(request):
    env = config.current_environment()
    return JSONResponse({
        "issuer": env.issuer,
        "authorization_endpoint": f"{env.origin}/oauth/authorize",
        "token_endpoint": f"{env.origin}/oauth/token",
        "revocation_endpoint": f"{env.origin}/oauth/revoke",
        "registration_endpoint": f"{env.origin}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": SCOPES_SUPPORTED,
        "service_documentation": f"{env.origin}/setup",
    })


# ── bounded DCR (RFC 7591) ──────────────────────────────────────────────────

def _redirect_uri_acceptable(uri: str) -> bool:
    try:
        parsed = urlsplit(uri)
    except ValueError:
        return False
    if parsed.fragment or parsed.username or parsed.password:
        return False  # no fragment/userinfo (T P0-9)
    if parsed.scheme == "https" and parsed.hostname:
        return True
    if parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1"):
        return True
    if parsed.scheme and "." in parsed.scheme and parsed.scheme != "http":
        return True  # private-use reverse-DNS scheme for desktop clients
    return False


async def oauth_register_handler(request):
    if _issuance_blocked():
        return _dark_json()
    if not issuance_limiter.allow("dcr", _client_ip(request)):
        return JSONResponse({"error": "too_many_requests"}, status_code=429)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid_client_metadata"}, status_code=400)
    redirect_uris = body.get("redirect_uris") or []
    if not isinstance(redirect_uris, list) or not redirect_uris:
        return JSONResponse({"error": "invalid_redirect_uri"}, status_code=400)
    if not all(isinstance(u, str) and _redirect_uri_acceptable(u) for u in redirect_uris):
        return JSONResponse({"error": "invalid_redirect_uri"}, status_code=400)
    client_name = str(body.get("client_name") or "Unnamed MCP client")
    try:
        client_id = stores.register_client(
            client_name=client_name, redirect_uris=redirect_uris,
            registration_path="dcr",
        )
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    return JSONResponse({
        "client_id": client_id, "client_name": client_name,
        "redirect_uris": redirect_uris, "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
    }, status_code=201)


# ── authorize ceremony ──────────────────────────────────────────────────────

_STYLE = (
    "<style>body{font-family:system-ui,sans-serif;max-width:26rem;margin:8vh "
    "auto;padding:0 1rem;color:#1c2733}input,button{font-size:1rem;padding:"
    ".55rem;width:100%;margin:.3rem 0;box-sizing:border-box}button{background:"
    "#1a6b54;color:#fff;border:0;border-radius:6px;cursor:pointer}.muted{color:"
    "#5b6b7a;font-size:.85rem}.err{color:#a33}</style>"
)


def _page(title: str, body: str, status: int = 200) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' "
        f"content='width=device-width,initial-scale=1'><title>{escape(title)}</title>"
        f"{_STYLE}</head><body><h1>{escape(title)}</h1>{body}"
        f"<p class='muted'>VerifiMind-PEAS · free registration · "
        f"<a href='/terms'>Terms</a> · <a href='/privacy'>Privacy</a></p></body></html>",
        status_code=status,
        # Consent is a security decision, so the page may not be framed
        # (UI-redress/clickjacking would let an overlay drive Allow), and it
        # carries session state, so it may not be cached by a shared proxy.
        headers={
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "frame-ancestors 'none'",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "no-store",
        },
    )


def _email_step(sid, notice=""):
    n = f"<p class='err'>{escape(notice)}</p>" if notice else ""
    return _page("Connect to VerifiMind",
        f"{n}<p>Enter your email. We send a one-time code — this signs you in, "
        "or creates your free account if you are new. We never reveal whether "
        "an email is already registered.</p>"
        f"<form method='post'><input type='hidden' name='sid' value='{escape(sid)}'>"
        "<input type='hidden' name='action' value='send_code'>"
        "<input type='email' name='email' placeholder='you@example.com' required>"
        "<button type='submit'>Send code</button></form>")


def _code_step(sid, email, notice=""):
    n = f"<p class='err'>{escape(notice)}</p>" if notice else ""
    return _page("Enter your code",
        f"{n}<p>If the address is valid, a code is on its way to "
        f"<strong>{escape(email)}</strong>. It expires in 15 minutes.</p>"
        f"<form method='post'><input type='hidden' name='sid' value='{escape(sid)}'>"
        "<input type='hidden' name='action' value='verify_code'>"
        f"<input type='hidden' name='email' value='{escape(email)}'>"
        "<input name='code' placeholder='8-digit code' required pattern='[0-9]{8}' "
        "inputmode='numeric'><button type='submit'>Verify</button></form>")


def _consent_step(sid, client_name):
    return _page("Authorize access",
        f"<p><strong>{escape(client_name)}</strong> is asking to run VerifiMind "
        "validation tools (X, Z, CS, Trinity) as your account. Tools are free. "
        "Structured run records are kept as described in the "
        "<a href='/privacy'>Privacy Policy</a>.</p>"
        f"<form method='post'><input type='hidden' name='sid' value='{escape(sid)}'>"
        "<input type='hidden' name='action' value='consent'>"
        "<label><input type='checkbox' name='agree' required style='width:auto;"
        "margin-right:.4rem'>I accept the <a href='/terms'>Terms</a> and "
        "acknowledge the <a href='/privacy'>Privacy Policy</a></label>"
        "<button type='submit' name='decision' value='allow'>Allow</button>"
        "<button type='submit' name='decision' value='deny' style='background:"
        "#5b6b7a'>Deny</button></form>")


async def oauth_authorize_get_handler(request):
    if _issuance_blocked():
        return _page("Sign-in unavailable",
            "<p>Account sign-in is not currently enabled.</p>", status=503)
    params = request.query_params
    client_id = params.get("client_id", "")
    redirect_uri = params.get("redirect_uri", "")
    try:
        client = stores.get_client(client_id) if client_id else None
    except StoreUnavailable:
        return _page("Temporarily unavailable",
            "<p>The sign-in service is briefly unavailable. Retry shortly.</p>",
            status=503)
    # Open-redirect pre-guard (T P0-9): never redirect for an unknown
    # client/redirect; render 400 instead.
    if client is None or redirect_uri not in client.get("redirect_uris", []):
        return _page("Invalid authorization request",
            "<p>The requesting client or its redirect address is not registered.</p>",
            status=400)
    state = params.get("state", "")
    # Authlib validates response_type / scope / PKCE presence + method.
    try:
        _authorization_server().get_consent_grant(await _oauth_request(request, "/oauth/authorize"))
    except OAuth2Error as error:
        return _redirect_error(redirect_uri, state, error.error)
    sid = _secrets.token_urlsafe(24)
    try:
        stores.put_authorize_session(sid, {
            "client_id": client_id, "client_name": client.get("client_name", "MCP client"),
            "redirect_uri": redirect_uri, "state": state,
            "code_challenge": params.get("code_challenge", ""),
            "scope": params.get("scope", "mcp") or "mcp",
            "email_verified": False, "email": "",
        })
    except StoreUnavailable:
        return _page("Temporarily unavailable", "<p>Retry shortly.</p>", status=503)
    return _email_step(sid)


def _redirect_error(redirect_uri, state, error):
    return RedirectResponse(
        f"{redirect_uri}?{urlencode({'error': error, 'state': state})}", status_code=302)


async def oauth_authorize_post_handler(request):
    if _issuance_blocked():
        return _page("Sign-in unavailable",
            "<p>Account sign-in is not currently enabled.</p>", status=503)
    form = await request.form()
    sid = str(form.get("sid", ""))
    action = str(form.get("action", ""))
    try:
        session = stores.get_authorize_session(sid) if sid else None
    except StoreUnavailable:
        session = None
    if session is None:
        return _page("Session expired",
            "<p>This sign-in attempt expired. Return to your client and connect "
            "again.</p>", status=400)

    if action == "send_code":
        email = str(form.get("email", "")).strip()
        if "@" not in email or len(email) > 254:
            return _email_step(sid, "Please enter a valid email address.")
        if not config.mail_recipient_allowed(email):
            return _email_step(sid, "This address cannot be used on this service instance.")
        if not issuance_limiter.allow("send_code", _client_ip(request)):
            return _email_step(sid, "Too many codes requested from this network — wait and retry.")
        code = mint_verification_code()
        try:
            stores.put_verification(email=email, code=code, purpose="authorize", session_id=sid)
            send_verification_email(to_email=email, code=code, purpose="authorize")
        except (StoreUnavailable, MailerUnavailable):
            return _page("Verification unavailable",
                "<p>Verification email cannot be sent right now — a temporary "
                "server-side condition. Retry shortly.</p>", status=503)
        return _code_step(sid, email)

    if action == "verify_code":
        email = str(form.get("email", "")).strip()
        code = str(form.get("code", "")).strip()
        try:
            ok = stores.claim_verification(email=email, code=code, purpose="authorize", session_id=sid)
        except StoreUnavailable:
            ok = False
        if not ok:
            return _code_step(sid, email, "That code is not valid (or expired).")
        stores.update_authorize_session(sid, {"email_verified": True, "email": email.lower()})
        return _consent_step(sid, session.get("client_name", "MCP client"))

    if action == "consent":
        redirect_uri = session["redirect_uri"]
        state = session.get("state", "")
        if str(form.get("decision", "")) != "allow" or not form.get("agree"):
            stores.drop_authorize_session(sid)
            return _redirect_error(redirect_uri, state, "access_denied")
        fresh = stores.get_authorize_session(sid) or {}
        if not fresh.get("email_verified"):
            return _email_step(sid, "Verify your email first.")
        subject = _resolve_or_create_subject(fresh.get("email", ""))
        if subject is None:
            return _page("Temporarily unavailable",
                "<p>Account service is briefly unavailable — retry shortly.</p>", status=503)
        # Rebuild the validated authorize request and let Authlib issue the code.
        authorize_req = build_request(
            method="GET",
            uri=f"{config.current_environment().origin}/oauth/authorize",
            form_pairs=[],
            query_pairs=[
                ("response_type", "code"), ("client_id", session["client_id"]),
                ("redirect_uri", redirect_uri), ("state", state),
                ("scope", session.get("scope", "mcp")),
                ("code_challenge", session.get("code_challenge", "")),
                ("code_challenge_method", "S256"),
            ],
            headers={},
        )
        try:
            status, body, headers = _authorization_server().create_authorization_response(
                authorize_req, grant_user=subject)
        except (OAuth2Error, StoreUnavailable):
            return _page("Temporarily unavailable", "<p>Retry shortly.</p>", status=503)
        stores.drop_authorize_session(sid)
        location = dict(headers).get("Location", redirect_uri)
        return RedirectResponse(location, status_code=302)

    return _page("Invalid request", "<p>Unknown action.</p>", status=400)


def _resolve_or_create_subject(email):
    """Verified-mailbox subject resolution. Only reachable AFTER the mailbox
    proof (T P0-2/P0-10).

    An account record is adopted as the OAuth subject ONLY when the mailbox
    has been proven for it. A record written by the unverified legacy
    register path is upgraded here — at the moment the mailbox is proven —
    rather than being adopted on sight: otherwise anyone could pre-register
    a victim's address and choose the identifier the victim's future
    verified sign-in would bind to (pre-registration subject hijack).
    """
    from verifimind_mcp.registration import (
        COLLECTION_EA, COLLECTION_REGISTRATIONS, _get_firestore, _now_iso,
        account_collection, normalize_email,
    )
    from verifimind_mcp.utils.uuid_helper import generate_ea_uuid

    db = _get_firestore()
    if db is None:
        return None
    normalized = normalize_email(email)
    for base in (COLLECTION_EA, COLLECTION_REGISTRATIONS):
        collection = account_collection(base)
        found = db.collection(collection).where("email", "==", normalized).limit(1).get()
        if found:
            snapshot = found[0]
            data = snapshot.to_dict() or {}
            if data.get("status", "active") != "active":
                return None
            if not data.get("email_verified"):
                # Mailbox proven now: bind verification to the record AND wipe
                # every caller-injectable profile field. CS Finding 3: an
                # unverified record could have been planted by an attacker with
                # the victim's email and a chosen display_name/feedback; adopting
                # it verbatim would bind attacker-chosen data to the victim's
                # verified subject. The UUID is adopted for cohort continuity
                # (it is non-secret and was never disclosed), but nothing the
                # caller could set survives the verification boundary.
                snapshot.reference.update({
                    "email_verified": True,
                    "email_verified_at": _now_iso(),
                    "display_name": None,
                    "name": None,
                    "registration_feedback": None,
                    "feedback_type": None,
                })
            return data.get("uuid")
    new_uuid = generate_ea_uuid()
    from verifimind_mcp.policies import PRIVACY_POLICY_VERSION, TERMS_VERSION
    db.collection(account_collection(COLLECTION_REGISTRATIONS)).document(new_uuid).set({
        "uuid": new_uuid, "email": normalized, "display_name": None, "tier": "ea",
        "registered_at": _now_iso(), "consent": True, "consent_ts": _now_iso(),
        "privacy_version": PRIVACY_POLICY_VERSION, "tc_version": TERMS_VERSION,
        "status": "active", "registration_path": "oauth_ceremony_v2",
        "email_verified": True, "email_verified_at": _now_iso(),
    })
    return new_uuid


# ── token + revoke ──────────────────────────────────────────────────────────

async def oauth_token_handler(request):
    if _issuance_blocked():
        return _dark_json()
    if not issuance_limiter.allow("token", _client_ip(request)):
        return JSONResponse({"error": "too_many_requests"}, status_code=429)
    try:
        oauth_req = await _oauth_request(request, "/oauth/token")
        status, body, headers = _authorization_server().create_token_response(oauth_req)
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    merged = {"Cache-Control": "no-store", "Pragma": "no-cache"}
    merged.update(dict(headers or {}))
    return JSONResponse(body, status_code=status, headers=merged)


async def oauth_revoke_handler(request):
    if _issuance_blocked():
        return _dark_json()
    form = await request.form()
    try:
        stores.revoke_credential(str(form.get("token", "")))
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    return JSONResponse({})  # RFC 7009: 200 regardless of match


# ── personal access tokens (local lane) ─────────────────────────────────────

async def oauth_pat_handler(request):
    if _issuance_blocked():
        return _dark_json()
    if not issuance_limiter.allow("pat", _client_ip(request)):
        return JSONResponse({"error": "too_many_requests"}, status_code=429)
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return JSONResponse({"error": "invalid_token"}, status_code=401,
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        # Full validation, not a bare store lookup: this endpoint mints a
        # 180-day credential, so it must run the SAME issuer/audience/scope
        # checks as the MCP boundary. A direct stores.validate_bearer call
        # skipped them and let a token bound to another deployment's
        # issuer/audience be exchanged for one stamped with this one's.
        from verifimind_mcp.oauth.authlib_server import authenticate_bearer

        record, error_code = authenticate_bearer(
            authorization[7:].strip(), ("mcp",)
        )
        if error_code == "insufficient_scope":
            return JSONResponse(
                {"error": "insufficient_scope"}, status_code=403,
                headers={"WWW-Authenticate": 'Bearer error="insufficient_scope", scope="mcp"'},
            )
        # PAT chaining is refused: a PAT may not mint another PAT.
        if record is None or record.kind != ACCESS:
            return JSONResponse({"error": "invalid_token"}, status_code=401,
                                headers={"WWW-Authenticate": "Bearer"})
        pat = stores.issue_pat(
            subject_uuid=record.subject_uuid,
            actor_class=record.actor_class,
            parent_grant_id=record.grant_id,
            scope=record.scope or "mcp",
        )
    except StoreUnavailable:
        return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)
    from verifimind_mcp.oauth.core import PAT_TTL
    return JSONResponse({
        "personal_access_token": pat.token, "expires_in": PAT_TTL,
        "usage": ("Send as 'Authorization: Bearer <token>' from local clients. "
                  "Store it in an environment variable or secret store — never in a "
                  "committed config, URL, or your UUID field."),
    }, headers={"Cache-Control": "no-store"})
