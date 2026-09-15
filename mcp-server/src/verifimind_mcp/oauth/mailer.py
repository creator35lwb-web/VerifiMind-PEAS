"""Outbound verification mail — vendor-agnostic, fail-closed in production.

The ceremony requires actually sending mail. Backends:

- ``smtp``    — any transactional provider via SMTP + STARTTLS. Host/port/
                user/from come from env; the password arrives through the
                deploy-time secret facility (Secret Manager reference), the
                S149 pattern. Vendor choice stays with Alton — nothing here
                names a provider.
- ``console`` — development only: prints the code to stderr. REFUSED when
                running on Cloud Run (K_SERVICE set) so a misconfigured
                production revision can never leak verification codes into
                logs; production without SMTP config fails closed with
                MAILER_UNAVAILABLE and the ceremony reports an honest 503.
"""

import os
import smtplib
import ssl
import sys
from email.message import EmailMessage


class MailerUnavailable(Exception):
    """No usable mail backend; the registration ceremony must fail closed."""


def _backend() -> str:
    configured = os.getenv("MAILER_BACKEND", "").strip().lower()
    if configured:
        return configured
    return "smtp" if os.getenv("SMTP_HOST") else "unconfigured"


def mailer_ready() -> bool:
    backend = _backend()
    if backend == "smtp":
        return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))
    if backend == "console":
        return not os.getenv("K_SERVICE")
    return False


def is_single_address(value: str) -> bool:
    """Exactly one plain address, no list smuggling.

    ``To:`` accepts a comma-separated list, and an allowlist that inspects
    only the last @-segment would pass "attacker@evil.com, ok@allowed.org"
    while smtplib derives BOTH envelope recipients from the header — one
    request delivering the one-time code to an off-allowlist address.
    """
    candidate = (value or "").strip()
    if not candidate or len(candidate) > 254:
        return False
    if any(ch in candidate for ch in ",;<>\"\\\r\n\t "):
        return False
    local, sep, domain = candidate.partition("@")
    return bool(sep) and bool(local) and "@" not in domain and "." in domain


def send_verification_email(*, to_email: str, code: str, purpose: str) -> None:
    """Send one verification/recovery code. Raises MailerUnavailable when
    no backend can safely send — callers surface an honest, retryable
    failure and never pretend the mail went out."""
    # Single-recipient enforcement runs BEFORE any backend, so neither the
    # console nor the SMTP path can be handed a list.
    if not is_single_address(to_email):
        raise MailerUnavailable("recipient must be exactly one plain address")
    backend = _backend()
    if backend == "console":
        if os.getenv("K_SERVICE"):
            raise MailerUnavailable("console mailer refused in production")
        print(
            f"[dev-mailer] verification code for {purpose}: {code}",
            file=sys.stderr,
            flush=True,
        )
        return
    if backend != "smtp" or not mailer_ready():
        raise MailerUnavailable("no mail backend configured")

    # Staging/dev recipient containment (T P0-8): never mail arbitrary people
    # from a non-production instance.
    from verifimind_mcp.oauth import config as _cfg

    if not _cfg.mail_recipient_allowed(to_email):
        raise MailerUnavailable("recipient not permitted on this instance")

    message = EmailMessage()
    message["From"] = os.getenv("SMTP_FROM", "")
    message["To"] = to_email
    message["Subject"] = "Your VerifiMind verification code"
    message.set_content(
        "Your VerifiMind verification code is: "
        f"{code}\n\n"
        "It expires in 15 minutes. If you did not request this, you can "
        "ignore this email — no account change happens without the code.\n\n"
        "— VerifiMind-PEAS · verifimind.ysenseai.org"
    )
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    # T P0-6: STARTTLS MUST validate the server certificate and hostname, or a
    # network attacker can intercept SMTP credentials and one-time codes.
    tls_context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.starttls(context=tls_context)
            if username:
                client.login(username, password)
            client.send_message(message)
    except Exception as exc:  # noqa: BLE001 — every send failure fails closed
        raise MailerUnavailable(f"send failed: {type(exc).__name__}") from exc
