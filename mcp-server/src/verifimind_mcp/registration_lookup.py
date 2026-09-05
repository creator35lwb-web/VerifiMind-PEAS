"""Server-side registration verification shared by every reader.

One primitive answers "is this UUID a registered, active identity?" across
BOTH registration collections:

- ``early_adopters``    — EA/pilot cohort (email + consent, slot-capped)
- ``ea_registrations``  — lightweight POST /register lane (consent-only)

Before this module every reader consulted only ``early_adopters``, so a
lightweight registrant was permanently invisible to tier resolution, /whoami,
and any authorization check (the "broken bridge").

Contract:
- ``status == "active"`` is REQUIRED. ``doc.exists`` alone would keep
  deletion-requested accounts authorized, contradicting the opt-out rights
  lane; revocation must actually revoke.
- Verification FAILS CLOSED: a Firestore outage or lookup error yields
  UNAVAILABLE, never a silent pass. Callers that authorize on this result
  must deny (retryable) on UNAVAILABLE.
- Positive results are cached for ``REGISTRATION_CACHE_TTL`` seconds so a
  brief backend blip does not cut an active session. Negative and
  unavailable results are NEVER cached: revocation takes effect on the next
  check and outages retry immediately.
- Collections resolve through the environment seam
  (``registration.account_collection``) BEFORE any read: a declared staging
  service consults only staging membership, and a misdeclared staging
  service reads nothing and resolves UNAVAILABLE (T S157 Finding 3).
  ``source`` reports the LOGICAL store name, whichever namespace was read.
"""

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

REGISTERED = "registered"
NOT_REGISTERED = "not_registered"
UNAVAILABLE = "unavailable"

# Positive-result cache TTL. Bounded revocation contract (T S152 P0 #7):
# any revocation/opt-out is honored within one TTL, so this stays ≤60s.
REGISTRATION_CACHE_TTL = 60


@dataclass(frozen=True)
class RegistrationState:
    """Outcome of a server-side registration lookup."""

    state: str
    source: Optional[str] = None  # collection the record was found in
    tier: Optional[str] = None    # stored tier field, informational only

    @property
    def is_registered(self) -> bool:
        return self.state == REGISTERED


_positive_cache: Dict[str, Tuple[float, RegistrationState]] = {}


def _clear_cache() -> None:
    """Test seam: drop all cached positive results."""
    _positive_cache.clear()


def resolve_registration(uuid: str) -> RegistrationState:
    """Resolve a (format-valid) UUID against both registration collections.

    The caller is responsible for format validation; this function only
    answers membership. First matching document wins; a matching document
    whose status is not "active" resolves NOT_REGISTERED without consulting
    the other collection (an opted-out identity stays revoked).
    """
    now = time.time()
    cached = _positive_cache.get(uuid)
    if cached and now < cached[0]:
        return cached[1]
    try:
        from verifimind_mcp.registration import (
            COLLECTION_EA,
            COLLECTION_REGISTRATIONS,
            _get_firestore,
            account_collection,
        )

        # Environment identity resolves BEFORE the client or any read (T S157
        # Finding 3). An unresolvable identity raises here, is caught below,
        # and answers UNAVAILABLE having consulted nothing.
        lookups = [
            (base, account_collection(base))
            for base in (COLLECTION_EA, COLLECTION_REGISTRATIONS)
        ]
        db = _get_firestore()
        if db is None:
            return RegistrationState(UNAVAILABLE)
        for base, collection in lookups:
            doc = db.collection(collection).document(uuid).get()
            if doc.exists:
                data = doc.to_dict() or {}
                if data.get("status", "active") == "active":
                    state = RegistrationState(
                        REGISTERED, source=base, tier=data.get("tier")
                    )
                    _positive_cache[uuid] = (now + REGISTRATION_CACHE_TTL, state)
                    return state
                return RegistrationState(NOT_REGISTERED, source=base)
        return RegistrationState(NOT_REGISTERED)
    except Exception:
        return RegistrationState(UNAVAILABLE)
