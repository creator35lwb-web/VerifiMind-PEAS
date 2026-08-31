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


def send_verification_email(*, to_email: str, code: str, purpose: str) -> None:
    """Send one verification/recovery code. Raises MailerUnavailable when
    no backend can safely send — callers surface an honest, retryable
    failure and never pretend the mail went out."""
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
    try:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.starttls()
            if username:
                client.login(username, password)
            client.send_message(message)
    except Exception as exc:  # noqa: BLE001 — every send failure fails closed
        raise MailerUnavailable(f"send failed: {type(exc).__name__}") from exc
