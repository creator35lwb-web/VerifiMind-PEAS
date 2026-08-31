"""HMAC-pseudonymous subjects for value telemetry (T P0 #6, D-152-4).

Raw UUIDs never enter value-telemetry events. Events carry
``s{version}_{base64url(HMAC-SHA256(key, uuid))[:22]}`` derived with a
versioned key from the secret facility. With the key unset the derivation
returns None and emitters simply omit the subject field — the privacy-safe
default is silence, never a raw identifier.
"""

import base64
import hashlib
import hmac
import os
from typing import Optional


def derive_subject(uuid: str) -> Optional[str]:
    key = os.getenv("VALUE_SUBJECT_HMAC_KEY", "")
    if not key or not uuid:
        return None
    version = os.getenv("VALUE_SUBJECT_HMAC_KEY_VERSION", "1").strip() or "1"
    digest = hmac.new(
        key.encode("utf-8"), uuid.encode("utf-8"), hashlib.sha256
    ).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"s{version}_{encoded[:22]}"
