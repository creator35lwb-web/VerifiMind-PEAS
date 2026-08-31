"""HTTP OAuth boundary for the /mcp lane — dark by default (Design v2).

D-153-5: an in-band tool denial cannot initiate interoperable MCP OAuth.
When the registration gate is enabled, this pure-ASGI middleware answers
unauthenticated protected requests with **HTTP 401 + WWW-Authenticate**
carrying the RFC 9728 protected-resource-metadata pointer, so OAuth-capable
clients can discover the authorization server and start the flow.

Modes (`AUTH_BOUNDARY_MODE`):
- ``connection`` (default) — every non-OPTIONS/HEAD /mcp request requires a
  valid Bearer token. Spec-safe for all clients; web pages, health, and
  /.well-known discovery remain anonymous elsewhere.
- ``execution`` — anonymous initialize/tools/list; only ``tools/call`` of
  the four gated tools requires Bearer. The request body is buffered
  (bounded) and replayed, never consumed. The dark client matrix decides
  whether this mode is proven per client (T addendum control 8).

Fail-closed: a token-store outage answers 503 (+Retry-After), never an
open gate. The validated subject and actor class travel to the tool layer
via contextvars; the legacy ``X-VerifiMind-UUID`` header confers nothing.
"""

import json
import os

from verifimind_mcp.middleware.registration_gate import (
    AUTH_ACTOR_CLASS,
    AUTH_SUBJECT_UUID,
    GATED_TOOL_NAMES,
    registration_gate_enabled,
)

_PRM_URL = "https://verifimind.ysenseai.org/.well-known/oauth-protected-resource"
_MAX_PEEK_BODY = 1024 * 1024  # execution-mode inspection cap


def boundary_mode() -> str:
    mode = os.getenv("AUTH_BOUNDARY_MODE", "connection").strip().lower()
    return mode if mode in ("connection", "execution") else "connection"


def _challenge_response(status: int, error: str, description: str):
    body = json.dumps({"error": error, "error_description": description}).encode()
    headers = [
        (b"content-type", b"application/json"),
        (
            b"www-authenticate",
            f'Bearer resource_metadata="{_PRM_URL}", error="{error}"'.encode(),
        ),
        (b"cache-control", b"no-store"),
    ]
    if status == 503:
        headers.append((b"retry-after", b"120"))
    return status, headers, body


class McpAuthBoundary:
    """Pure ASGI middleware — must wrap INSIDE the rate limiter."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or not registration_gate_enabled():
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if not (path == "/mcp" or path.startswith("/mcp/")):
            return await self.app(scope, receive, send)
        method = scope.get("method", "GET").upper()
        if method in ("OPTIONS", "HEAD"):
            return await self.app(scope, receive, send)

        replay_receive = receive
        if boundary_mode() == "execution":
            needs_auth, replay_receive = await self._gated_call_peek(receive)
            if not needs_auth:
                return await self.app(scope, replay_receive, send)

        token = self._bearer(scope)
        if not token:
            return await self._reject(
                send, *_challenge_response(
                    401, "invalid_token",
                    "This request requires OAuth authentication. Register "
                    "free and connect via the authorization server in the "
                    "resource metadata.",
                )
            )
        try:
            from verifimind_mcp.oauth.stores import StoreUnavailable, validate_token
            try:
                record = validate_token(token)
            except StoreUnavailable:
                return await self._reject(
                    send, *_challenge_response(
                        503, "temporarily_unavailable",
                        "Token verification is temporarily unavailable; "
                        "retry shortly.",
                    )
                )
        except Exception:
            record = None
        if record is None:
            return await self._reject(
                send, *_challenge_response(
                    401, "invalid_token",
                    "The presented token is invalid, expired, or revoked.",
                )
            )
        subject_token = AUTH_SUBJECT_UUID.set(record.subject_uuid)
        actor_token = AUTH_ACTOR_CLASS.set(record.actor_class)
        try:
            return await self.app(scope, replay_receive, send)
        finally:
            AUTH_SUBJECT_UUID.reset(subject_token)
            AUTH_ACTOR_CLASS.reset(actor_token)

    @staticmethod
    def _bearer(scope) -> str:
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                text = value.decode("latin-1", "replace").strip()
                if text.lower().startswith("bearer "):
                    return text[7:].strip()
        return ""

    @staticmethod
    async def _gated_call_peek(receive):
        """Buffer the request body (bounded) to decide whether this is a
        tools/call of a gated tool; return (needs_auth, replay_receive).
        Anything unparseable or oversized is treated as protected — the
        boundary fails toward authentication, never around it."""
        chunks = []
        total = 0
        more = True
        while more:
            message = await receive()
            if message["type"] != "http.request":
                # Disconnect mid-read: treat as protected; replay verbatim.
                chunks.append(message)
                break
            body = message.get("body", b"")
            total += len(body)
            chunks.append(message)
            more = message.get("more_body", False)
            if total > _MAX_PEEK_BODY:
                break

        async def replay():
            for message in chunks:
                yield message

        iterator = replay()

        async def replay_receive():
            try:
                return await iterator.__anext__()
            except StopAsyncIteration:
                return {"type": "http.request", "body": b"", "more_body": False}

        if total > _MAX_PEEK_BODY:
            return True, replay_receive
        raw = b"".join(
            m.get("body", b"") for m in chunks if m.get("type") == "http.request"
        )
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            return True, replay_receive
        requests = payload if isinstance(payload, list) else [payload]
        for item in requests:
            if not isinstance(item, dict):
                return True, replay_receive
            if item.get("method") == "tools/call":
                name = (item.get("params") or {}).get("name")
                if name in GATED_TOOL_NAMES:
                    return True, replay_receive
        return False, replay_receive

    @staticmethod
    async def _reject(send, status, headers, body):
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        })
        await send({"type": "http.response.body", "body": body})
