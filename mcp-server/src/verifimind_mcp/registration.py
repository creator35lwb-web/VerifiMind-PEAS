"""
VerifiMind-PEAS Registration — v0.5.13 Fortify
Z-Protocol v1.1 compliant: consent-first, data minimization, explicit opt-out.

Two registration paths:
  1. POST /register           — Lightweight (v0.5.13): email optional, UUIDv7 identity spine
  2. POST /early-adopters/register — Full EA (v0.5.6): email required, feedback, invite codes

Storage: Google Cloud Firestore (free tier, GCP project)
UUID format: UUIDv7-compatible (timestamp-ordered per AI Council recommendation)
"""
import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .utils.uuid_helper import generate_ea_uuid, generate_feedback_id
from .policies import PRIVACY_POLICY_VERSION, TERMS_VERSION
from .oauth.config import EnvironmentMisconfigured, current_environment

try:  # google-api-core ships with the Firestore client; keep the module importable without it
    from google.api_core.exceptions import AlreadyExists as _AlreadyExists
except Exception:  # noqa: BLE001 — pragma: no cover (client library absent)
    class _AlreadyExists(Exception):  # type: ignore[no-redef]
        """Stand-in when google-api-core is unavailable; never raised by a real client."""

logger = logging.getLogger(__name__)

# ── Tier constants ─────────────────────────────────────────────────────────────
# Pilot tier: active MCP users invited via SYSTEM_NOTICE
PILOT_MAX_SLOTS = 50

# Early Adopter tier: public open registration
EA_MAX_SLOTS = 100

CURRENT_AVAILABILITY_NOTICE = (
    "Registration is free and does not create a time-limited access "
    "entitlement. 8 tools are active; 3 coordination and 2 custom-template "
    "mutation tools are temporarily unavailable during security maintenance."
)

# Pilot invite code (set via GCP env var — never hardcoded)
PILOT_INVITE_CODE = os.environ.get("PILOT_INVITE_CODE", "")

# Firestore collection names
COLLECTION_EA = "early_adopters"
COLLECTION_FEEDBACK = "feedback"
# One canonical owner per email across BOTH registration lanes (T S158
# Finding 1): a hash-keyed claim document created atomically with
# ``DocumentReference.create()`` — exactly one caller can ever create it.
COLLECTION_EMAIL_OWNERS = "email_owners"

# The ONE external contract every email-bearing registration returns, whether
# the address is new or already registered (T S158 Finding 3): no message,
# flag, tier, URL, or availability text may depend on account existence.
_UNIFORM_EMAIL_MESSAGE = (
    "Thanks — your interest is recorded. Finish sign-in through your "
    "MCP client's Connect flow, which verifies your email and issues "
    "your credentials. Account details are never disclosed here. "
    f"{CURRENT_AVAILABILITY_NOTICE}"
)

# The ONE honest receipt an email-bearing registration returns when storage
# fails mid-request (T S159 F-04): identical for a new and an existing address
# — both perform the same class of write, so both fail alike — and it never
# claims persistence that did not occur (F-RES-1, v0.5.50). Rendered by the
# handlers as a retryable 503.
_UNSAVED_EMAIL_MESSAGE = (
    "Registration storage is temporarily unavailable, so this request could "
    "not be completed and no account was created. Please try again in a few "
    "minutes."
)


class RegistrationStoreUnavailable(Exception):
    """A registration lane hit a storage backend failure mid-request. Carries
    the lane's uniform not-saved receipt; the HTTP handler renders it as one
    retryable 503 (``Retry-After``, ``no-store``) for new and existing
    addresses alike — never a generic 500 (an existence oracle) and never a
    success screen (a persistence lie)."""

    def __init__(self, receipt):
        super().__init__("registration storage unavailable")
        self.receipt = receipt

# Feedback attribution grades (T S158 Finding 2): the ``uuid`` field carries a
# subject ONLY when it was derived from a validated bearer credential.
ATTRIBUTION_VERIFIED_BEARER = "verified_bearer"
ATTRIBUTION_ANONYMOUS = "anonymous"
ATTRIBUTION_REGISTRATION_UNVERIFIED = "registration_unverified"
ATTRIBUTION_DETACHED = "detached_on_verification"


# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────

class EarlyAdopterRegistration(BaseModel):
    """Input model for EA registration.

    Consent fields (tc_accepted, privacy_acknowledged) are required.
    All other fields except email are optional.
    """
    email: EmailStr = Field(..., description="Your email address — used to identify your EA account")
    name: Optional[str] = Field(None, max_length=100, description="Your name (optional — display only)")
    feedback: Optional[str] = Field(
        None,
        max_length=1000,
        description=(
            "Tell us about yourself (optional). Are you a new user curious about "
            "VerifiMind? Or a returning user wanting to share recommendations? "
            "We'd love to hear from you either way."
        )
    )
    feedback_type: Optional[str] = Field(
        None,
        description="new_user | returning_user | issue | recommendation | general"
    )
    tc_accepted: bool = Field(
        ...,
        description="You have read and accept the Terms & Conditions v1.0"
    )
    privacy_acknowledged: bool = Field(
        ...,
        description="You have read and acknowledge the Privacy Policy v1.0"
    )
    updates_consent: bool = Field(
        False,
        description="Optional: receive product updates by email"
    )
    invite_code: Optional[str] = Field(
        None,
        max_length=64,
        description="Pilot invite code from SYSTEM_NOTICE (optional — upgrades tier to pilot if valid)"
    )

    @field_validator("tc_accepted")
    @classmethod
    def tc_must_be_accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "You must accept the Terms & Conditions to register as an Early Adopter."
            )
        return v

    @field_validator("privacy_acknowledged")
    @classmethod
    def privacy_must_be_acknowledged(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "You must acknowledge the Privacy Policy to register as an Early Adopter."
            )
        return v

    @field_validator("feedback_type")
    @classmethod
    def validate_feedback_type(cls, v: Optional[str]) -> Optional[str]:
        valid = {None, "new_user", "returning_user", "issue", "recommendation", "general"}
        if v not in valid:
            raise ValueError(f"feedback_type must be one of: {', '.join(str(x) for x in valid if x)}")
        return v


class RegistrationResponse(BaseModel):
    """Response returned after successful EA registration."""
    uuid: str
    email_masked: str  # e.g. "a***@example.com" — never echo full email in response
    tier: str = "early_adopter"
    tier_label: str = "Early Adopter"
    # Compatibility fields retained as null so existing clients do not fail
    # schema decoding. They no longer describe an access entitlement.
    free_months: Optional[int] = None
    registered_at: str
    benefits_free_until: Optional[str] = None
    availability_notice: str = CURRENT_AVAILABILITY_NOTICE
    tc_version: str
    privacy_version: str
    message: str
    benefit_summary: str = ""
    opt_out_url: str
    feedback_received: bool
    persisted: bool = True  # v0.5.50 (F-RES-1): False when storage was down and the record was NOT saved


class FeedbackRequest(BaseModel):
    """Input model for standalone feedback submission (registered or anonymous)."""
    content: str = Field(..., min_length=1, max_length=2000, description="Your feedback or issue")
    feedback_type: str = Field(
        "general",
        description="feedback | issue | recommendation | general"
    )
    uuid: Optional[str] = Field(
        None,
        description=(
            "Your EA UUID if registered (optional). Stored only as an UNVERIFIED "
            "claim; attribution is derived from a Bearer credential, never from "
            "this field."
        ),
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Your email if you'd like a follow-up (optional)"
    )
    connection_context: Optional[str] = Field(
        None,
        max_length=200,
        description="Which tool or flow you were using when you encountered this (optional)"
    )

    @field_validator("feedback_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid = {"feedback", "issue", "recommendation", "general"}
        if v not in valid:
            raise ValueError(f"feedback_type must be one of: {', '.join(valid)}")
        return v


class FeedbackResponse(BaseModel):
    """Response after feedback submission."""
    feedback_id: str
    received_at: str
    message: str


class EAStatusResponse(BaseModel):
    """EA account status response."""
    uuid: str
    tier: str
    registered_at: str
    benefits_free_until: Optional[str] = None
    availability_notice: str = CURRENT_AVAILABILITY_NOTICE
    status: str
    updates_consent: bool


class OptOutResponse(BaseModel):
    """Response after opt-out request."""
    processed: bool
    message: str
    deletion_scheduled_within: Optional[str] = None


_OPTOUT_STORAGE_UNAVAILABLE_MESSAGE = (
    "Deletion could not be confirmed because account storage is temporarily "
    "unavailable. No deletion action is confirmed. Please retry or email "
    "alton@ysenseai.org privately."
)


def build_optout_unavailable_response() -> OptOutResponse:
    """Return the non-enumerating retry contract for persistence failures."""
    return OptOutResponse(
        processed=False,
        message=_OPTOUT_STORAGE_UNAVAILABLE_MESSAGE,
    )


# ─────────────────────────────────────────────
# Firestore Client (lazy init)
# ─────────────────────────────────────────────

_firestore_client = None


def _get_firestore():
    """Lazy-initialize Firestore client. Returns None if Firestore unavailable."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    project_id = os.environ.get("FIRESTORE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logger.info("No FIRESTORE_PROJECT_ID configured — EA registration running without persistent storage")
        return None

    try:
        from google.cloud import firestore  # type: ignore
        _firestore_client = firestore.Client(project=project_id)
        logger.info("Firestore client initialized")
        return _firestore_client
    except Exception as e:
        logger.warning(f"Firestore unavailable: {e} — EA registration will use fallback storage")
        return None


def firestore_health() -> str:
    """Firestore connectivity signal for /health (v0.5.50, F-RES-1).

    'connected'    — client available (registrations persist)
    'unconfigured' — no FIRESTORE_PROJECT_ID / GOOGLE_CLOUD_PROJECT set
    'error'        — project configured but the client could not be constructed
    """
    project_id = os.environ.get("FIRESTORE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        return "unconfigured"
    return "connected" if _get_firestore() is not None else "error"


# ─────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────

class SlotCapReachedError(Exception):
    """Raised when a tier's slot cap is full."""
    def __init__(self, tier: str, max_slots: int):
        self.tier = tier
        self.max_slots = max_slots
        super().__init__(f"{tier} slots full ({max_slots}/{max_slots})")


def _build_benefit_summary(
    tier: str,
    tier_label: str,
    benefits_until: Optional[str] = None,
) -> str:
    """Build a clear human-readable benefit summary for the registration response."""
    if tier == "pilot":
        return (
            f"{tier_label}: member of the 50-slot Pilot feedback cohort. "
            f"{CURRENT_AVAILABILITY_NOTICE}"
        )
    return (
        f"{tier_label}: member of the 100-slot Early Adopter feedback cohort. "
        f"{CURRENT_AVAILABILITY_NOTICE}"
    )


def _mask_email(email: str) -> str:
    """Return a masked email for safe display: a***@example.com"""
    parts = email.split("@")
    if len(parts) != 2:
        return "***@***"
    local, domain = parts
    masked_local = local[0] + "***" if len(local) > 1 else "***"
    return f"{masked_local}@{domain}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_tier_slots(db, tier: str) -> int:
    """Count registered slots for a given tier. Returns 0 if Firestore unavailable."""
    try:
        docs = db.collection(account_collection(COLLECTION_EA)).where("tier", "==", tier).where("status", "==", "active").count().get()
        return int(docs[0][0].value)
    except Exception as e:
        logger.warning(f"Slot count query failed for tier={tier}: {e}")
        return 0


async def register_early_adopter(data: EarlyAdopterRegistration) -> RegistrationResponse:
    """Register a new Early Adopter or Pilot, or return existing record for duplicate email.

    Tier assignment:
    - Pilot (50-slot feedback cohort): valid invite_code matching PILOT_INVITE_CODE
    - Early Adopter (100-slot feedback cohort): everyone else

    One canonical owner per email across BOTH lanes (T S158 Finding 1); one
    external response for new AND existing addresses (T S158 Finding 3).
    Slot cap: returns 410 Gone (raises ValueError with code) if tier is full.
    """
    # Environment identity resolves BEFORE the client or any I/O: a
    # misdeclared staging service stops here (T S157 Finding 3).
    lanes = _lane_collections()
    ea_collection = lanes[COLLECTION_EA]
    feedback_collection = account_collection(COLLECTION_FEEDBACK)
    owners_collection = account_collection(COLLECTION_EMAIL_OWNERS)
    db = _get_firestore()
    now = _now_iso()
    normalized = normalize_email(data.email)

    # ── Determine tier ──────────────────────────────────────────────────────────
    is_pilot = (
        bool(data.invite_code)
        and bool(PILOT_INVITE_CODE)
        and data.invite_code.strip() == PILOT_INVITE_CODE
    )
    tier = "pilot" if is_pilot else "early_adopter"
    tier_label = "Pilot Member" if is_pilot else "Early Adopter"
    max_slots = PILOT_MAX_SLOTS if is_pilot else EA_MAX_SLOTS

    if db is not None:
        # ── Slot cap check ──────────────────────────────────────────────────────
        current_slots = _count_tier_slots(db, tier)
        if current_slots >= max_slots:
            logger.info(f"Slot cap reached for tier={tier}: {current_slots}/{max_slots}")
            raise SlotCapReachedError(tier, max_slots)

        # ── Canonical email ownership (T S158 Finding 1) ────────────────────────
        # An email is owned by a legacy record in EITHER lane's collection, or
        # by the atomic claim document created here; two callers racing for
        # the same address can never both win the claim. Whoever did not win
        # gets exactly the same receipt as the winner (T P0-2: never disclose
        # an existing UUID or its opt-out URL from a bare email lookup —
        # recovery goes through the verified-mailbox OAuth ceremony).
        try:
            new_uuid = generate_ea_uuid()
            legacy = _legacy_owner(db, lanes, normalized)
            if legacy is not None:
                # Existing address: perform the SAME class of write a new
                # address performs (T S159 F-04), so a storage outage cannot
                # tell the two apart — see _reassert_owner_claim.
                _reassert_owner_claim(
                    db, owners_collection, normalized,
                    legacy_base=legacy[0], legacy_uuid=legacy[1], now=now,
                )
                owned = True
            else:
                owned = not claim_email(
                    db, owners_collection, normalized, uuid=new_uuid,
                    collection_base=COLLECTION_EA, lane="early_adopters_v1", now=now,
                )
            if owned:
                logger.info(
                    "Duplicate registration for masked email %s — disclosure withheld",
                    _mask_email(str(data.email)),
                )
                record_uuid = None
            else:
                record = {
                    "uuid": new_uuid,
                    "email": normalized,  # canonical form; never logged
                    "name": data.name,
                    "registered_at": now,
                    "tier": tier,
                    "tc_accepted": True,
                    "tc_version": TERMS_VERSION,
                    "tc_accepted_at": now,
                    "privacy_acknowledged": True,
                    "privacy_version": PRIVACY_POLICY_VERSION,
                    "privacy_acknowledged_at": now,
                    "updates_consent": data.updates_consent,
                    "registration_feedback": data.feedback,
                    "feedback_type": data.feedback_type or ("new_user" if not data.feedback else "general"),
                    "status": "active",
                }
                # The mailbox is NOT proven on this path, so the record is
                # marked unverified and its identifier is never returned. The
                # OAuth ceremony upgrades it once the mailbox is actually
                # proven — and neutralizes every caller-chosen field above at
                # that moment (resolve_verified_subject).
                record["email_verified"] = False
                if is_pilot:
                    record["pilot_source"] = "system_notice_invite"
                if _create_account_record(db, ea_collection, new_uuid, record):
                    logger.info(f"New {tier} cohort record created (identifier withheld)")
                    record_uuid = new_uuid
                else:
                    record_uuid = None

            # ── Feedback: stored as explicitly UNVERIFIED registration content ─
            # Recorded for new and existing addresses alike so the receipt below
            # is truthful for both; it never carries an authoritative subject
            # (T S158 Findings 1/2). Environment-namespaced like the account it
            # accompanies (T S157 Finding 2).
            if data.feedback:
                db.collection(feedback_collection).add(
                    _registration_feedback_record(data, now, record_uuid)
                )
        except Exception as exc:  # noqa: BLE001
            from .oauth.stores import is_backend_failure

            if is_backend_failure(exc):
                # Storage outage mid-request (T S159 F-04). Every email-bearing
                # submission performs one owners-collection write (new: create;
                # existing: backfill or re-assert), so an outage fails a new and
                # an existing address identically. The receipt is the lane's
                # HONEST not-saved contract (F-RES-1: never a success screen for
                # an unsaved registration), rendered by the handler as one
                # retryable 503 — a persistent quota or permission failure is
                # loud, never a silent success.
                logger.warning(
                    "EA registration storage unavailable (error_type=%s)", type(exc).__name__,
                )
                raise RegistrationStoreUnavailable(
                    _unsaved_ea_response(now, _mask_email(str(data.email)))
                ) from exc
            raise

    else:
        # F-RES-1 (v0.5.50): Firestore unavailable — the registration CANNOT be
        # persisted, so say so instead of promising a UUID that will never resolve.
        logger.warning("Firestore unavailable — registration cannot be persisted")
        return RegistrationResponse(
            uuid=generate_ea_uuid(),
            email_masked=_mask_email(str(data.email)),
            tier=tier,
            tier_label=tier_label,
            registered_at=now,
            tc_version=TERMS_VERSION,
            privacy_version=PRIVACY_POLICY_VERSION,
            persisted=False,
            message=(
                "Registration storage is temporarily unavailable — your registration "
                "was NOT saved. No data was stored. Please try again in a few minutes."
            ),
            benefit_summary="",
            opt_out_url="/register",
            feedback_received=False,
        )

    # UNIFORM response (T P0-2 + adversarial B-3/B-6; byte-equal for new AND
    # existing addresses per T S158 Finding 3, and for a partial write outage
    # per T S159 F-04): this endpoint is not an account-existence oracle, and
    # it never hands out a subject identifier the mailbox owner has not proven.
    # The identifier is delivered only through the verified Connect ceremony.
    return _uniform_ea_response(now, _mask_email(str(data.email)), bool(data.feedback))


def _uniform_ea_response(now: str, email_masked: str, feedback_received: bool) -> "RegistrationResponse":
    """The ONE external contract an email-bearing EA registration returns —
    for a new address, an existing address, AND a reads-up/writes-down
    claim-store outage (T S158 Finding 3 / T S159 F-04). It never branches on
    account existence and never discloses a subject identifier."""
    return RegistrationResponse(
        uuid="",
        email_masked=email_masked,
        tier="",
        tier_label="",
        registered_at=now,
        tc_version=TERMS_VERSION,
        privacy_version=PRIVACY_POLICY_VERSION,
        message=_UNIFORM_EMAIL_MESSAGE,
        benefit_summary="",
        opt_out_url="",
        feedback_received=feedback_received,
    )


def _unsaved_ea_response(now: str, email_masked: str) -> "RegistrationResponse":
    """The honest not-saved receipt for a mid-request storage outage — the
    same bytes for a new and an existing address (T S159 F-04), no phantom
    identifier, ``persisted`` False, and ``feedback_received`` False because
    nothing was stored (F-RES-1)."""
    return RegistrationResponse(
        uuid="",
        email_masked=email_masked,
        tier="",
        tier_label="",
        registered_at=now,
        tc_version=TERMS_VERSION,
        privacy_version=PRIVACY_POLICY_VERSION,
        persisted=False,
        message=_UNSAVED_EMAIL_MESSAGE,
        benefit_summary="",
        opt_out_url="",
        feedback_received=False,
    )


def _registration_feedback_record(data, now: str, record_uuid: Optional[str]) -> dict:
    """Feedback typed at registration: content from an UNVERIFIED caller.

    ``uuid`` (the authoritative subject field) is always None here; the
    generated registration identifier, if any, is kept only as an explicitly
    unverified link so mailbox proof never turns it into attribution
    (T S158 Finding 1)."""
    return {
        "feedback_id": generate_feedback_id(),
        "submitted_at": now,
        "type": data.feedback_type or "general",
        "content": data.feedback,
        "uuid": None,
        "attribution": ATTRIBUTION_REGISTRATION_UNVERIFIED,
        "registration_uuid_unverified": record_uuid,
        "email": None,  # never store email in feedback collection
        "connection_context": "registration",
    }


def account_collection(base: str) -> str:
    """Environment-namespaced name for a USER-DATA collection — accounts
    (``early_adopters`` / ``ea_registrations``), ``feedback``, and
    ``trinity_history`` all resolve through this one seam.

    Production and local development keep the bare historical names; a
    declared staging environment is prefixed, so it can never read, create,
    or tombstone a production record. ``EnvironmentMisconfigured``
    PROPAGATES: a staging service whose identity cannot be resolved stops
    here, before any read or write — it must never fall back to the
    production name (CS round 3 / T S157 Finding 3: the previous broad
    ``except`` returned exactly that). Every caller resolves its collection
    before it opens the client.
    """
    return current_environment().account_collection(base)


def normalize_email(value) -> str:
    """Canonical email form used for EVERY store and lookup.

    Pydantic's EmailStr lowercases only the domain, so `Bob@x.com` and
    `bob@x.com` previously produced two accounts and defeated both dedup
    checks — and made a verified-mailbox sign-in fork a second subject.
    """
    return str(value or "").strip().lower()


# ── Canonical email ownership across both registration lanes (T S158) ───────

def email_owner_key(email) -> str:
    """Deterministic claim-document id for an email: SHA-256 of the canonical
    form. The account record already stores the address in clear, so the hash
    is an index key, not a secret; it keeps the raw address out of document
    paths and logs."""
    return hashlib.sha256(normalize_email(email).encode("utf-8")).hexdigest()


def _lane_collections() -> dict:
    """Both registration lanes' account collections, environment-resolved
    BEFORE any client is opened (T S157 Finding 3)."""
    return {
        COLLECTION_EA: account_collection(COLLECTION_EA),
        COLLECTION_REGISTRATIONS: account_collection(COLLECTION_REGISTRATIONS),
    }


def _legacy_owner(db, lanes: dict, normalized_email: str):
    """The account record that already owns the address in EITHER lane, as
    ``(collection_base, uuid)`` — or None when no record carries it. A read
    only; the write that must accompany it lives in ``_reassert_owner_claim``."""
    for base, collection in lanes.items():
        found = db.collection(collection).where("email", "==", normalized_email).limit(1).get()
        if found:
            data = found[0].to_dict() or {}
            return base, str(data.get("uuid") or getattr(found[0], "id", "") or "")
    return None


def _email_already_owned(db, lanes: dict, normalized_email: str) -> bool:
    """A legacy (pre-claim) record in EITHER lane already owns the address."""
    return _legacy_owner(db, lanes, normalized_email) is not None


def _reassert_owner_claim(
    db, owners_collection: str, normalized_email: str, *,
    legacy_base: str, legacy_uuid: str, now: str,
) -> None:
    """The existing-address path's ONE owners-collection write (T S159 F-04).

    A new address creates its claim; an existing address used to perform no
    write at all, so under a reads-up/writes-down outage the new address failed
    (500) while the existing one succeeded — an existence oracle. Now every
    email-bearing submission performs the same class of write: a record whose
    claim is missing (a legacy, pre-claim account) gets its claim backfilled —
    the verified resolver's own rule, applied one step earlier — and a record
    whose claim exists gets an invariant field re-asserted (``email_hash`` is
    always the document id, so nothing new is stored). A write outage therefore
    fails a new and an existing address identically. A legacy record whose
    subject is already tombstoned (an interrupted pre-repair opt-out) is never
    named by a new claim; the resolver refuses it and opt-out cleans it."""
    key = email_owner_key(normalized_email)
    claim_ref = db.collection(owners_collection).document(key)
    if claim_ref.get().exists:
        claim_ref.update({"email_hash": key})
        return
    if not legacy_uuid or _subject_revoked(legacy_uuid):
        return
    claim_email(
        db, owners_collection, normalized_email, uuid=legacy_uuid,
        collection_base=legacy_base, lane="backfill", now=now,
    )


def claim_email(
    db, owners_collection: str, normalized_email: str, *,
    uuid: str, collection_base: str, lane: str, now: str,
) -> bool:
    """Atomically claim canonical ownership of an email for ``uuid``.

    ``DocumentReference.create()`` succeeds for exactly ONE caller per
    document id and raises ``AlreadyExists`` for everyone else, so two
    concurrent registrations (in the same lane or across lanes) can never
    both create an account for one address. Returns True when this call
    won the claim, False when the address is already owned."""
    key = email_owner_key(normalized_email)
    try:
        db.collection(owners_collection).document(key).create({
            "email_hash": key,
            "uuid": uuid,
            "collection": collection_base,
            "lane": lane,
            "claimed_at": now,
            "verified": False,
        })
    except _AlreadyExists:
        return False
    return True


def _create_account_record(db, collection: str, uuid: str, record: dict) -> bool:
    """Write a NEW account record with create-if-absent semantics.

    A plain ``set()`` could overwrite a record the verified ceremony healed
    under the same identifier between this lane's claim and its write —
    replacing verified state with the unverified preregistration. With
    ``create()`` the later writer loses and the verified record stands.
    Returns False when the record already existed (nothing overwritten)."""
    try:
        db.collection(collection).document(uuid).create(record)
    except _AlreadyExists:
        logger.info("Account record already existed at write time — left untouched")
        return False
    return True


def _release_owner_claim(owners_collection: str, key: str, *, expected_uuid: str) -> bool:
    """Delete an email-owner claim IFF it still names ``expected_uuid``.

    ABA-safe (T S159 F-02): a bare ``delete()`` erases whatever claim is
    present — including a replacement a concurrent re-registration installed
    for a DIFFERENT subject. Reading and deleting inside one transaction makes
    a competing writer conflict (or, under the server's read locks, wait), and
    the identity check leaves a re-pointed claim for its new owner. An
    already-absent claim, or one now owned by someone else, counts as released
    for THIS subject — nothing of ours remains. A backend failure propagates as
    ``StoreUnavailable`` through ``run_transaction`` so the caller fails closed
    and retryable, never a false success. The transaction runs on the process
    client (``run_transaction`` resolves it), the same client every caller
    here holds — there is deliberately no ``db`` parameter to suggest otherwise."""
    from .oauth.stores import run_transaction

    def _txn(txn):
        current = txn.get_dict(owners_collection, key)
        if current is None or current.get("uuid") != expected_uuid:
            return True
        txn.delete(owners_collection, key)
        return True

    return bool(run_transaction(_txn))


def _release_claims_naming(db, owners_collection: str, uuid: str) -> int:
    """Release EVERY email-owner claim that names ``uuid`` — the subject's own
    durable cleanup identity (T S159 F-03). The lookup is the claim's ``uuid``
    field, never the account record's email, so it still works after PII has
    been scrubbed, and it also cleans a claim left behind by an interrupted
    pre-repair opt-out (claim present, email already ``[deletion_requested]``).
    Each delete is conditional (ABA-safe) because a claim could be re-pointed
    between the query and the delete. Returns the number released; a backend
    failure propagates so the caller fails closed."""
    released = 0
    for snapshot in db.collection(owners_collection).where("uuid", "==", uuid).get():
        key = getattr(snapshot, "id", None) or (snapshot.to_dict() or {}).get("email_hash", "")
        if key and _release_owner_claim(owners_collection, key, expected_uuid=uuid):
            released += 1
    return released


def _reclaim_tombstoned_owner(
    owners_collection: str, key: str, *,
    expected_uuid: str, fresh_uuid: str, collection_base: str, lane: str, now: str,
) -> bool:
    """Atomically replace a claim that names a tombstoned subject with a fresh
    one (T S159 F-02).

    Returns True when THIS call installed ``fresh_uuid``; False when the claim
    changed under us — a concurrent resolver already released or re-pointed it,
    so the caller re-reads and adopts the winner instead of forking a second
    verified subject for one mailbox. The read-and-set happen in ONE
    transaction, so an unconditional delete can never erase a replacement
    claim; a competing writer conflicts (fake) or waits (server read locks).
    The fresh claim is minted ``verified: False`` exactly as ``claim_email``
    mints it; only the account write that follows marks it verified."""
    from .oauth.stores import run_transaction

    def _txn(txn):
        current = txn.get_dict(owners_collection, key)
        if current is None or current.get("uuid") != expected_uuid:
            return False
        txn.set(owners_collection, key, {
            "email_hash": key, "uuid": fresh_uuid, "collection": collection_base,
            "lane": lane, "claimed_at": now, "verified": False,
        })
        return True

    return bool(run_transaction(_txn))


def _subject_revoked(uuid: str) -> bool:
    """True when the subject carries a revocation tombstone (opt-out ran).
    A revoked identifier must never be adopted, healed, or re-issued."""
    from .oauth.stores import _is_tombstoned

    return bool(uuid) and _is_tombstoned(grant_id="", parent_grant_id="", subject_uuid=uuid)


def _lane_default_tier(collection_base: str) -> str:
    return "early_adopter" if collection_base == COLLECTION_EA else "ea"


def _verified_record(uuid: str, normalized_email: str, now: str, tier: str = "ea") -> dict:
    return {
        "uuid": uuid, "email": normalized_email, "display_name": None, "tier": tier,
        "registered_at": now, "consent": True, "consent_ts": now,
        "consent_source": "oauth_ceremony_v2",
        "privacy_version": PRIVACY_POLICY_VERSION, "tc_version": TERMS_VERSION,
        "updates_consent": False,
        "status": "active", "registration_path": "oauth_ceremony_v2",
        "email_verified": True, "email_verified_at": now,
        "verification_path": "oauth_ceremony_v2",
    }


# Every field an unverified caller could have chosen on a preregistration.
# Mailbox proof is a STATE-TRANSITION SANITIZER, not retroactive authorship
# (T S158 Finding 1): none of these may become the verified subject's state.
_PREREGISTRATION_NEUTRALIZED = (
    "name", "display_name", "registration_feedback", "feedback_type",
    "updates_consent", "tier", "pilot_source",
)


def _adopt_verified(reference, data: dict, collection_base: str, now: str) -> Optional[str]:
    """Bind mailbox proof to an existing record and neutralize everything an
    unverified caller could have chosen. Returns the subject UUID, or None
    when the record is not an active account."""
    if data.get("status", "active") != "active":
        return None
    uuid = data.get("uuid", "")
    if not uuid:
        return None
    if data.get("email_verified"):
        return uuid  # already a verified subject; nothing to sanitize
    reference.update({
        "email_verified": True,
        "email_verified_at": now,
        "verification_path": "oauth_ceremony_v2",
        # Profile and content chosen before proof: gone.
        "display_name": None,
        "name": None,
        "registration_feedback": None,
        "feedback_type": None,
        # Consent provenance: the verified actor's OWN ceremony supplies
        # Terms/Privacy acceptance now; marketing consent defaults OFF until
        # that actor explicitly opts in (T S158 contract 2).
        "tc_accepted": True,
        "tc_version": TERMS_VERSION,
        "tc_accepted_at": now,
        "privacy_acknowledged": True,
        "privacy_version": PRIVACY_POLICY_VERSION,
        "privacy_acknowledged_at": now,
        "consent": True,
        "consent_ts": now,
        "consent_source": "oauth_ceremony_v2",
        "updates_consent": False,
        # Cohort privilege chosen before proof: back to the lane default.
        "tier": _lane_default_tier(collection_base),
        "pilot_source": None,
        # The account's registration moment is the verified actor's, not the
        # unverified caller's; the earlier timestamp is kept as provenance.
        "registered_at": now,
        "preregistration": {
            "created_at": data.get("registered_at"),
            "adopted_at": now,
            "neutralized": list(_PREREGISTRATION_NEUTRALIZED) + ["registered_at"],
        },
    })
    return uuid


def _detach_unverified_feedback(db, feedback_collection: str, uuid: str) -> int:
    """Feedback linked to ``uuid`` before mailbox proof was written by an
    unverified caller: it stays, but loses the authoritative subject field
    (legacy records written before attribution grades existed)."""
    detached = 0
    for snapshot in db.collection(feedback_collection).where("uuid", "==", uuid).get():
        record = snapshot.to_dict() or {}
        if record.get("attribution") == ATTRIBUTION_VERIFIED_BEARER:
            continue
        snapshot.reference.update({
            "uuid": None,
            "claimed_uuid_unverified": uuid,
            "attribution": ATTRIBUTION_DETACHED,
        })
        detached += 1
    return detached


def resolve_verified_subject(email) -> Optional[str]:
    """Verified-mailbox subject resolution. Only reachable AFTER the mailbox
    proof (T P0-2/P0-10).

    One mailbox proof binds ONE deterministic subject across both
    registration lanes and races (T S158 contract 1): the claim document is
    the canonical owner; a legacy record without a claim is backfilled into
    one; a brand-new address gets its claim BEFORE its record; a claim whose
    record write failed is healed under the claimed identifier. Every
    adoption passes through ``_adopt_verified`` so nothing an unverified
    caller chose survives the proof. Returns None when the store is
    unavailable or the owning record is not an active account.
    """
    # Environment identity resolves BEFORE the client (T S157 Finding 3;
    # closes the ordering seam the round-4 review noted).
    owners_collection = account_collection(COLLECTION_EMAIL_OWNERS)
    feedback_collection = account_collection(COLLECTION_FEEDBACK)
    lanes = _lane_collections()
    db = _get_firestore()
    if db is None:
        return None
    normalized = normalize_email(email)
    key = email_owner_key(normalized)
    now = _now_iso()
    claim_ref = db.collection(owners_collection).document(key)

    for _attempt in range(3):  # a lost race or a released stale claim is resolved by re-reading
        claim = claim_ref.get()
        if claim.exists:
            claimed = claim.to_dict() or {}
            base = claimed.get("collection")
            owner_uuid = claimed.get("uuid", "")
            if base not in lanes or not owner_uuid:
                # A claim that names no lane or no identifier is corrupt state:
                # fail closed rather than guess a collection (never fall open).
                logger.error("Email-owner claim is malformed; refusing to resolve a subject")
                return None
            if _subject_revoked(owner_uuid):
                # The owner opted out (subject tombstoned) but its claim was
                # not released: a revoked identifier is never adopted, healed,
                # or re-issued. Replace the stale claim with a FRESH subject in
                # ONE transaction (T S159 F-02): a bare delete-then-recreate
                # here could erase a replacement a concurrent resolver already
                # installed, forking one mailbox into two verified subjects.
                # A False return means the claim changed under us — re-read and
                # adopt the concurrent winner instead of minting a rival.
                fresh_uuid = generate_ea_uuid()
                if _reclaim_tombstoned_owner(
                    owners_collection, key, expected_uuid=owner_uuid,
                    fresh_uuid=fresh_uuid, collection_base=COLLECTION_REGISTRATIONS,
                    lane="oauth_ceremony_v2", now=now,
                ):
                    if not _create_account_record(
                        db, lanes[COLLECTION_REGISTRATIONS], fresh_uuid,
                        _verified_record(fresh_uuid, normalized, now),
                    ):
                        continue  # a concurrent writer healed it — re-read and adopt
                    claim_ref.update({"verified": True, "verified_at": now})
                    return fresh_uuid
                continue
            reference = db.collection(lanes[base]).document(owner_uuid)
            snapshot = reference.get()
            if snapshot.exists:
                subject = _adopt_verified(reference, snapshot.to_dict() or {}, base, now)
            else:
                # The claim won but its record write never landed: heal under
                # the claimed identifier so the address keeps ONE owner. A
                # concurrent writer that lands first wins (create-if-absent);
                # re-read and adopt through it.
                healed = _verified_record(owner_uuid, normalized, now, tier=_lane_default_tier(base))
                if not _create_account_record(db, lanes[base], owner_uuid, healed):
                    continue
                subject = owner_uuid
            if subject is not None:
                _detach_unverified_feedback(db, feedback_collection, subject)
                claim_ref.update({"verified": True, "verified_at": now})
            return subject

        # No claim: a legacy record (written before claims existed) in either
        # lane owns the address — backfill its claim, then adopt through it.
        for base, collection in lanes.items():
            found = db.collection(collection).where("email", "==", normalized).limit(1).get()
            if found:
                data = found[0].to_dict() or {}
                legacy_uuid = data.get("uuid") or getattr(found[0], "id", "")
                if not legacy_uuid or _subject_revoked(legacy_uuid):
                    # No usable identifier, or a revoked identity still
                    # carrying the address (an interrupted opt-out): fail
                    # closed — creating a second account would fork the
                    # mailbox; this needs the rights channel, not a guess.
                    logger.error("Legacy account record cannot be adopted; refusing to resolve a subject")
                    return None
                if claim_email(db, owners_collection, normalized, uuid=legacy_uuid,
                               collection_base=base, lane="backfill", now=now):
                    subject = _adopt_verified(found[0].reference, data, base, now)
                    if subject is not None:
                        _detach_unverified_feedback(db, feedback_collection, subject)
                        claim_ref.update({"verified": True, "verified_at": now})
                    return subject
                break  # lost the race to a concurrent claimant: re-read the claim

        else:
            # Nothing anywhere: claim FIRST (atomic), then write the verified
            # record; a lost race re-reads and adopts the winner's subject.
            new_uuid = generate_ea_uuid()
            if claim_email(db, owners_collection, normalized, uuid=new_uuid,
                           collection_base=COLLECTION_REGISTRATIONS,
                           lane="oauth_ceremony_v2", now=now):
                if not _create_account_record(db, lanes[COLLECTION_REGISTRATIONS], new_uuid,
                                              _verified_record(new_uuid, normalized, now)):
                    continue
                claim_ref.update({"verified": True, "verified_at": now})
                return new_uuid
    return None


async def get_ea_status(uuid: str) -> Optional[EAStatusResponse]:
    """Return EA status for a given UUID. Returns None if not found."""
    collection = account_collection(COLLECTION_EA)  # resolves BEFORE any read
    db = _get_firestore()
    if db is None:
        return None

    doc = db.collection(collection).document(uuid).get()
    if not doc.exists:
        return None

    data = doc.to_dict()
    return EAStatusResponse(
        uuid=data["uuid"],
        tier=data.get("tier", "early_adopter"),
        registered_at=data["registered_at"],
        status=data.get("status", "active"),
        updates_consent=data.get("updates_consent", False),
    )


async def submit_feedback(
    data: FeedbackRequest, verified_subject: Optional[str] = None,
) -> FeedbackResponse:
    """Submit feedback, issue, or recommendation (registered or anonymous).

    Attribution (T S158 Finding 2): the authoritative ``uuid`` field carries a
    subject ONLY when the caller supplied ``verified_subject`` — derived from
    a validated Bearer credential, never from the request body. A body
    ``uuid`` is a public, non-secret identifier anyone can type; it is kept
    only as ``claimed_uuid_unverified``. Anonymous feedback stays admitted."""
    # Environment identity resolves BEFORE the client or any write: staging
    # feedback lands in staging's collection and a misdeclared staging service
    # writes nothing (T S157 Findings 2/3). Production keeps the bare name and
    # its anonymous-feedback semantics exactly as they were.
    collection = account_collection(COLLECTION_FEEDBACK)
    db = _get_firestore()
    now = _now_iso()
    feedback_id = generate_feedback_id()

    claimed = data.uuid if data.uuid and data.uuid != verified_subject else None
    record = {
        "feedback_id": feedback_id,
        "submitted_at": now,
        "type": data.feedback_type,
        "content": data.content,
        "uuid": verified_subject,
        "attribution": ATTRIBUTION_VERIFIED_BEARER if verified_subject else ATTRIBUTION_ANONYMOUS,
        "claimed_uuid_unverified": claimed,
        "email": None,  # never store email in feedback collection
        "connection_context": data.connection_context,
    }

    if db is not None:
        db.collection(collection).document(feedback_id).set(record)
        logger.info(f"Feedback received: id={feedback_id}, type={data.feedback_type}")
    else:
        logger.warning(f"Firestore unavailable — feedback {feedback_id} not persisted")

    return FeedbackResponse(
        feedback_id=feedback_id,
        received_at=now,
        message=(
            "Thank you for your feedback! It goes directly to the VerifiMind-PEAS "
            "development team and helps shape future releases. "
            "You can track product updates at "
            "github.com/creator35lwb-web/VerifiMind-PEAS/discussions."
        ),
    )


async def process_optout(uuid: str) -> OptOutResponse:
    """De-identify account PII and mark remaining data for bounded deletion."""
    # Environment identity resolves BEFORE the client or any read/write; an
    # unresolvable staging identity is reported as unavailable — never as a
    # success receipt, never against production's stores (T S157 Finding 3).
    try:
        ea_collection = account_collection(COLLECTION_EA)
        light_collection = account_collection(COLLECTION_REGISTRATIONS)
        owners_collection = account_collection(COLLECTION_EMAIL_OWNERS)
    except EnvironmentMisconfigured as exc:
        logger.error(
            "Opt-out refused: environment identity unresolved (error_type=%s)",
            type(exc).__name__,
        )
        return build_optout_unavailable_response()

    db = _get_firestore()

    if db is None:
        logger.warning("Opt-out not processed: Firestore unavailable")
        return build_optout_unavailable_response()

    try:
        # UNION revocation (T S152 P0 #2): a rights request must revoke the
        # identity in EVERY registration store and kill every live credential.
        # The order is monotonic and resumable (T S159 F-03), ordered by
        # reversibility: de-identify PII, release every ownership claim that
        # names this subject (found by the claim's OWN uuid field — a durable
        # cleanup identity that survives the scrub), and tombstone + revoke the
        # subject LAST, because that step kills the caller's bearer. Every step
        # is idempotent, so a retry after any failure before the tombstone
        # completes the sequence with the same credential; after the tombstone
        # nothing that matters is left undone. Scrubbing before releasing also
        # closes a window: a verified ceremony that runs between the release and
        # the tombstone finds no email to backfill and mints a FRESH subject, so
        # no claim naming this subject can be re-created behind the release.
        ea_ref = db.collection(ea_collection).document(uuid)
        ea_doc = ea_ref.get()
        light_ref = db.collection(light_collection).document(uuid)
        light_doc = light_ref.get()
        matched = ea_doc.exists or light_doc.exists

        if matched:
            # 1. De-identify account PII in both lanes (idempotent on retry).
            if ea_doc.exists:
                ea_ref.update({
                    "status": "deletion_requested",
                    "deletion_requested_at": _now_iso(),
                    # Immediately nullify PII fields
                    "email": "[deletion_requested]",
                    "name": None,
                    "registration_feedback": None,
                })
            if light_doc.exists:
                light_ref.update({
                    "status": "deletion_requested",
                    "deletion_requested_at": _now_iso(),
                    "email": "[deletion_requested]",
                    "display_name": None,
                })
            # 2. Release every mailbox claim that names THIS subject, each
            #    conditionally (T S159 F-02: a re-pointed claim belongs to its
            #    new owner and is left alone). A backend failure raises through
            #    the guarded transaction and is handled below as a retryable
            #    outage; the caller's bearer is still alive, so the retry finds
            #    the claim again by uuid and finishes.
            _release_claims_naming(db, owners_collection, uuid)
            # 3. Tombstone the subject and revoke every OAuth/PAT credential
            #    LAST (T S159 F-03). The subject tombstone is consulted on every
            #    validation path, so once it has landed the erasure is complete
            #    even if the hygiene sweep of ``revoked`` flags did not finish —
            #    and the receipt says so instead of denying an erasure that
            #    happened. The ≤60s validation cache bounds cross-instance
            #    propagation (Design v2).
            from verifimind_mcp.oauth.stores import revoke_all_for_subject
            try:
                revoke_all_for_subject(uuid)
            except Exception as exc:  # noqa: BLE001
                if not _subject_revoked(uuid):
                    raise
                logger.warning(
                    "Opt-out: subject tombstone landed but the credential sweep did not "
                    "finish (error_type=%s); every validation path denies on the tombstone",
                    type(exc).__name__,
                )
            logger.info("Opt-out processed for a stored account")
        else:
            # Do not reveal whether a caller-supplied UUID belongs to an account.
            logger.info("Opt-out request did not match a stored account")
    except Exception as exc:
        # This is a rights-request path: never convert a failed read/write into a
        # success receipt, and never expose the UUID or backend error text.
        logger.error(
            "Opt-out persistence unavailable (error_type=%s)",
            type(exc).__name__,
        )
        return build_optout_unavailable_response()

    return OptOutResponse(
        processed=True,
        message=(
            "The opt-out request was processed. If the UUID matched a stored "
            "account, principal account PII has been de-identified and remaining "
            "personal data is targeted to be purged within 7 business days; a "
            "legal obligation or documented security/legal hold may limit or "
            "delay deletion. The 8 active validation and built-in-template tools "
            "remain available without registration."
        ),
        deletion_scheduled_within=(
            "target: 7 business days; legal/security retention may apply"
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# v0.5.13 "Fortify" — Lightweight /register endpoint
# XV PIN #49 architecture: email optional, UUID = identity spine
# v0.5.15 — P1-C: registration response enhanced with MCP config snippet
# ─────────────────────────────────────────────────────────────────────────────

_SERVER_BASE_URL = "https://verifimind.ysenseai.org"


def _build_registration_extras(uuid: str, checkout: Optional[str] = None) -> dict:
    """Build the P1-C enhanced fields for the registration response.

    Returns test/dashboard/config fields plus the deprecated checkout field,
    which is null unless a separately reviewed paid service supplies a URL.
    Security: uuid is already validated (UUIDv7 from generate_ea_uuid()).
    """
    return {
        "checkout_url": checkout,
        "test_url": f"{_SERVER_BASE_URL}/mcp/test?key={uuid}",
        "dashboard_url": f"{_SERVER_BASE_URL}/early-adopters/dashboard/{uuid}",
        "mcp_config": {
            "mcpServers": {
                "verifimind": {
                    "command": "npx",
                    "args": [
                        "-y", "mcp-remote", f"{_SERVER_BASE_URL}/mcp/",
                        "--header", "X-VerifiMind-UUID:${VERIFIMIND_UUID}",
                    ],
                    "env": {"VERIFIMIND_UUID": uuid},
                }
            }
        },
    }

# Firestore collection for lightweight registrations
COLLECTION_REGISTRATIONS = "ea_registrations"


class UserRegistrationRequest(BaseModel):
    """Lightweight registration request — v0.5.13.

    Only consent is required. Email and display_name are optional.
    A user who registers with only consent: true gets a UUID — maximum privacy.
    """
    email: Optional[EmailStr] = Field(
        None,
        description="Your email address (optional — used only for account recovery)"
    )
    display_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Display name (optional)"
    )
    consent: bool = Field(
        ...,
        description=(
            f"You consent to Privacy Policy v{PRIVACY_POLICY_VERSION} and "
            f"Terms & Conditions v{TERMS_VERSION}"
        )
    )

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "Consent is required to register. "
                "Please review our Privacy Policy and Terms & Conditions."
            )
        return v


class UserRegistrationResponse(BaseModel):
    """Response from POST /register — v0.5.15."""
    uuid: str
    tier: str = "ea"
    registered_at: str
    # Honest-degradation flag (F-RES-1 parity with the EA path): False means
    # storage was unavailable and this registration was NOT saved — the UUID
    # cannot verify anywhere. Never report success for an unpersisted record.
    persisted: bool = True
    # Deprecated compatibility fields. No paid service or timed entitlement is
    # currently offered, so these serialize as null.
    expires_at: Optional[str] = None
    pioneer_checkout: Optional[str] = None
    checkout_url: Optional[str] = None
    availability_notice: str = CURRENT_AVAILABILITY_NOTICE
    message: str
    opt_out_url: str
    test_url: str
    dashboard_url: str
    mcp_config: dict
    privacy_version: str
    tc_version: str


async def register_user(data: UserRegistrationRequest) -> UserRegistrationResponse:
    """Register a new user with minimal data — UUID is their identity.

    XV PIN #49 architecture (v0.5.13):
    - Email is optional: consent-only registration returns a UUID
    - UUID is UUIDv7 (time-ordered for Firestore query efficiency)
    - UUID is a pseudonymous identifier, not an authorization credential
    - Anonymous Scholar users are NOT required to register (zero friction)
    - legacy checkout response fields remain null while no paid service exists

    An email-bearing registration has ONE canonical owner across both lanes
    (T S158 Finding 1) and ONE external response whether the address is new
    or already registered (T S158 Finding 3). The anonymous (email-absent)
    path is unchanged: the UUID is that user's only handle.
    """
    # Environment identity resolves BEFORE the client or any I/O: a
    # misdeclared staging service stops here (T S157 Finding 3).
    lanes = _lane_collections()
    collection = lanes[COLLECTION_REGISTRATIONS]
    owners_collection = account_collection(COLLECTION_EMAIL_OWNERS)
    db = _get_firestore()
    now = _now_iso()
    new_uuid = generate_ea_uuid()
    if data.email and db is not None:
        normalized = normalize_email(data.email)
        try:
            legacy = _legacy_owner(db, lanes, normalized)
            if legacy is not None:
                # Existing address: the SAME class of write a new address
                # performs (T S159 F-04) — see _reassert_owner_claim.
                _reassert_owner_claim(
                    db, owners_collection, normalized,
                    legacy_base=legacy[0], legacy_uuid=legacy[1], now=now,
                )
                owned = True
            else:
                owned = not claim_email(
                    db, owners_collection, normalized, uuid=new_uuid,
                    collection_base=COLLECTION_REGISTRATIONS, lane="lightweight_v0513", now=now,
                )
        except Exception as exc:  # noqa: BLE001
            from .oauth.stores import is_backend_failure

            if is_backend_failure(exc):
                # Storage outage mid-request (T S159 F-04): both a new and an
                # existing address fail here identically, and the receipt is the
                # lane's honest not-saved contract rendered as a retryable 503.
                logger.warning(
                    "Lightweight registration storage unavailable (error_type=%s)", type(exc).__name__,
                )
                raise RegistrationStoreUnavailable(_unsaved_lightweight_response(now)) from exc
            raise
        if owned:
            # T P0-2: do not disclose an existing UUID from an email lookup —
            # and (T S158 Finding 3) say nothing that a new address would
            # not also be told.
            logger.info(
                "Lightweight register: duplicate email %s — disclosure withheld",
                _mask_email(str(data.email)),
            )
            return _uniform_lightweight_response(now)

    # Store in Firestore (when available)
    if db is not None:
        record = {
            "uuid": new_uuid,
            "email": normalize_email(data.email) if data.email else None,
            "display_name": data.display_name,
            "tier": "ea",
            "registered_at": now,
            "consent": True,
            "consent_ts": now,
            "privacy_version": PRIVACY_POLICY_VERSION,
            "tc_version": TERMS_VERSION,
            "status": "active",
            "registration_path": "lightweight_v0513",
            # Mailbox NOT proven on this path; the identifier is withheld and
            # the OAuth ceremony upgrades the record once it is proven.
            "email_verified": False,
        }
        try:
            if _create_account_record(db, collection, new_uuid, record):
                logger.info("Lightweight cohort record created (identifier withheld)")
        except Exception as exc:  # noqa: BLE001
            from .oauth.stores import is_backend_failure

            # An email-bearing record-write outage must stay uniform with the
            # existing-address receipt (T S159 F-04). The anonymous path has no
            # address to probe, so its write failure keeps the existing honest
            # not-saved behaviour (re-raised to the handler).
            if is_backend_failure(exc) and data.email is not None:
                logger.warning(
                    "Lightweight record storage unavailable (error_type=%s)", type(exc).__name__,
                )
                raise RegistrationStoreUnavailable(_unsaved_lightweight_response(now)) from exc
            raise
    else:
        logger.warning("Firestore unavailable — lightweight registration UUID=%s not persisted", new_uuid)
        # F-RES-1 parity: never show a success screen for a registration
        # that was not saved — this UUID does not exist server-side and can
        # never verify at /whoami or any registration check.
        return UserRegistrationResponse(
            uuid=new_uuid,
            tier="ea",
            registered_at=now,
            persisted=False,
            message=(
                "Registration storage is temporarily unavailable — your "
                "registration was NOT saved. No data was stored and this UUID "
                "is not registered. Please try again in a few minutes."
            ),
            opt_out_url="/register",
            privacy_version=PRIVACY_POLICY_VERSION,
            tc_version=TERMS_VERSION,
            **_build_registration_extras(new_uuid),
        )

    # CS Finding 2: the anonymous (email-absent) path has NO email to probe and
    # NO victim to hijack, so withholding the UUID there orphans a legitimate
    # maximum-privacy user at birth — they have no email and thus no way to
    # recover the identifier through the verified ceremony. Branch on email:
    #   - email ABSENT  → return the UUID (it is the anonymous user's only
    #     handle; no oracle/hijack surface exists without an email).
    #   - email PRESENT → withhold, uniform with the duplicate-email branch, so
    #     the endpoint is neither an existence oracle nor a way to plant the
    #     identifier a victim's future verified sign-in would adopt.
    if data.email is None:
        return UserRegistrationResponse(
            uuid=new_uuid,
            tier="ea",
            registered_at=now,
            message=(
                "Registration successful. Your UUID is your identity — save it; "
                "there is no email on this account to recover it with. "
                f"{CURRENT_AVAILABILITY_NOTICE}"
            ),
            opt_out_url=f"/early-adopters/optout/{new_uuid}",
            privacy_version=PRIVACY_POLICY_VERSION,
            tc_version=TERMS_VERSION,
            **_build_registration_extras(new_uuid),
        )

    return _uniform_lightweight_response(now)


def _uniform_lightweight_response(now: str) -> UserRegistrationResponse:
    """The ONE receipt an email-bearing lightweight registration returns,
    whether the address is new or already registered (T S158 Finding 3)."""
    return UserRegistrationResponse(
        uuid="",
        tier="",
        registered_at=now,
        persisted=True,
        message=_UNIFORM_EMAIL_MESSAGE,
        opt_out_url="",
        privacy_version=PRIVACY_POLICY_VERSION,
        tc_version=TERMS_VERSION,
        **_build_registration_extras(""),
    )


def _unsaved_lightweight_response(now: str) -> UserRegistrationResponse:
    """The honest not-saved receipt for a mid-request storage outage on the
    lightweight lane — the same bytes for a new and an existing address
    (T S159 F-04), no phantom identifier, ``persisted`` False (F-RES-1)."""
    return UserRegistrationResponse(
        uuid="",
        tier="",
        registered_at=now,
        persisted=False,
        message=_UNSAVED_EMAIL_MESSAGE,
        opt_out_url="",
        privacy_version=PRIVACY_POLICY_VERSION,
        tc_version=TERMS_VERSION,
        **_build_registration_extras(""),
    )
