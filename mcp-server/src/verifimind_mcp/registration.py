"""
VerifiMind-PEAS Registration — v0.5.13 Fortify
Z-Protocol v1.1 compliant: consent-first, data minimization, explicit opt-out.

Two registration paths:
  1. POST /register           — Lightweight (v0.5.13): email optional, UUIDv7 identity spine
  2. POST /early-adopters/register — Full EA (v0.5.6): email required, feedback, invite codes

Storage: Google Cloud Firestore (free tier, GCP project)
UUID format: UUIDv7-compatible (timestamp-ordered per AI Council recommendation)
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .utils.uuid_helper import generate_ea_uuid, generate_feedback_id
from .policies import PRIVACY_POLICY_VERSION, TERMS_VERSION

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
    uuid: Optional[str] = Field(None, description="Your EA UUID if registered (optional)")
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

    Idempotent: same email → returns existing UUID (no duplicate records).
    Slot cap: returns 410 Gone (raises ValueError with code) if tier is full.
    """
    db = _get_firestore()
    now = _now_iso()

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

        # ── Duplicate email check ───────────────────────────────────────────────
        existing = db.collection(account_collection(COLLECTION_EA)).where("email", "==", normalize_email(data.email)).limit(1).get()
        if existing:
            # T P0-2: NEVER return an existing UUID (or its opt-out URL) from a
            # bare email lookup — that is the first link in the disclosure →
            # unauthenticated history → unauthenticated revocation chain.
            # Account recovery goes through the verified-mailbox OAuth ceremony.
            logger.info(
                "Duplicate registration for masked email %s — disclosure withheld",
                _mask_email(str(data.email)),
            )
            return RegistrationResponse(
                uuid="",
                email_masked=_mask_email(str(data.email)),
                tier="",
                tier_label="",
                registered_at=now,
                tc_version=TERMS_VERSION,
                privacy_version=PRIVACY_POLICY_VERSION,
                message=(
                    "If an account already exists for this email, sign in "
                    "through your MCP client's Connect flow, which verifies "
                    "your email. Account details are never disclosed here."
                ),
                benefit_summary="",
                opt_out_url="",
                feedback_received=False,
            )

        # ── New registration ────────────────────────────────────────────────────
        new_uuid = generate_ea_uuid()
        record = {
            "uuid": new_uuid,
            "email": normalize_email(data.email),  # canonical form; never logged
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
        # The mailbox is NOT proven on this path, so the record is marked
        # unverified and its identifier is never returned (see the uniform
        # response below). The OAuth ceremony upgrades it once the mailbox
        # is actually proven.
        record["email_verified"] = False
        if is_pilot:
            record["pilot_source"] = "system_notice_invite"
        db.collection(account_collection(COLLECTION_EA)).document(new_uuid).set(record)
        logger.info(f"New {tier} cohort record created (identifier withheld)")

        # ── Store feedback separately ───────────────────────────────────────────
        if data.feedback:
            feedback_record = {
                "feedback_id": generate_feedback_id(),
                "submitted_at": now,
                "type": data.feedback_type or "general",
                "content": data.feedback,
                "uuid": new_uuid,
                "email": None,  # never store email in feedback collection
                "connection_context": "registration",
            }
            db.collection(COLLECTION_FEEDBACK).add(feedback_record)

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

    # UNIFORM response (T P0-2 + adversarial B-3/B-6): byte-identical in shape
    # to the duplicate-email branch, so this endpoint is not an account-
    # existence oracle, and it never hands out a subject identifier the
    # mailbox owner has not proven. The identifier is delivered only through
    # the verified Connect ceremony.
    return RegistrationResponse(
        uuid="",
        email_masked=_mask_email(str(data.email)),
        tier="",
        tier_label="",
        registered_at=now,
        tc_version=TERMS_VERSION,
        privacy_version=PRIVACY_POLICY_VERSION,
        message=(
            "Thanks — your interest is recorded. Finish sign-in through your "
            "MCP client's Connect flow, which verifies your email and issues "
            "your credentials. Account details are never disclosed here. "
            f"{CURRENT_AVAILABILITY_NOTICE}"
        ),
        benefit_summary="",
        opt_out_url="",
        feedback_received=bool(data.feedback),
    )


def account_collection(base: str) -> str:
    """Environment-namespaced account collection name.

    Production and local development keep the bare historical names; a
    declared staging environment is isolated, so it can never read, create,
    or tombstone a production account.
    """
    try:
        from verifimind_mcp.oauth.config import current_environment

        return current_environment().account_collection(base)
    except Exception:
        return base


def normalize_email(value) -> str:
    """Canonical email form used for EVERY store and lookup.

    Pydantic's EmailStr lowercases only the domain, so `Bob@x.com` and
    `bob@x.com` previously produced two accounts and defeated both dedup
    checks — and made a verified-mailbox sign-in fork a second subject.
    """
    return str(value or "").strip().lower()


async def get_ea_status(uuid: str) -> Optional[EAStatusResponse]:
    """Return EA status for a given UUID. Returns None if not found."""
    db = _get_firestore()
    if db is None:
        return None

    doc = db.collection(account_collection(COLLECTION_EA)).document(uuid).get()
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


async def submit_feedback(data: FeedbackRequest) -> FeedbackResponse:
    """Submit feedback, issue, or recommendation (registered or anonymous)."""
    db = _get_firestore()
    now = _now_iso()
    feedback_id = generate_feedback_id()

    record = {
        "feedback_id": feedback_id,
        "submitted_at": now,
        "type": data.feedback_type,
        "content": data.content,
        "uuid": data.uuid,
        "email": None,  # never store email in feedback collection
        "connection_context": data.connection_context,
    }

    if db is not None:
        db.collection(COLLECTION_FEEDBACK).document(feedback_id).set(record)
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
    db = _get_firestore()

    if db is None:
        logger.warning("Opt-out not processed: Firestore unavailable")
        return build_optout_unavailable_response()

    try:
        # UNION revocation (T S152 P0 #2): a rights request must revoke the
        # identity in EVERY registration store and kill every live
        # credential — success is reported only when all stores answered.
        matched = False
        doc_ref = db.collection(account_collection(COLLECTION_EA)).document(uuid)
        doc = doc_ref.get()
        if doc.exists:
            matched = True
            doc_ref.update({
                "status": "deletion_requested",
                "deletion_requested_at": _now_iso(),
                # Immediately nullify PII fields
                "email": "[deletion_requested]",
                "name": None,
                "registration_feedback": None,
            })
        light_ref = db.collection(account_collection(COLLECTION_REGISTRATIONS)).document(uuid)
        light_doc = light_ref.get()
        if light_doc.exists:
            matched = True
            light_ref.update({
                "status": "deletion_requested",
                "deletion_requested_at": _now_iso(),
                "email": "[deletion_requested]",
                "display_name": None,
            })
        if matched:
            # Tombstone every OAuth/PAT credential for the subject; the
            # ≤60s validation cache bounds propagation (Design v2).
            from verifimind_mcp.oauth.stores import revoke_all_for_subject
            revoke_all_for_subject(uuid)
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

    Idempotent by UUID — each call generates a new UUID (email-based
    dedup is best-effort only, not enforced for privacy-first anonymous path).
    """
    db = _get_firestore()
    now = _now_iso()
    new_uuid = generate_ea_uuid()
    # Best-effort email dedup (only when email provided and Firestore available)
    if data.email and db is not None:
        existing = (
            db.collection(account_collection(COLLECTION_REGISTRATIONS))
            .where("email", "==", normalize_email(data.email))
            .limit(1)
            .get()
        )
        if existing:
            # T P0-2: do not disclose an existing UUID from an email lookup.
            logger.info(
                "Lightweight register: duplicate email %s — disclosure withheld",
                _mask_email(str(data.email)),
            )
            return UserRegistrationResponse(
                uuid="",
                tier="",
                registered_at=now,
                persisted=True,
                message=(
                    "If an account already exists for this email, sign in "
                    "through your MCP client's Connect flow, which verifies "
                    "your email. Account details are never disclosed here."
                ),
                opt_out_url="",
                privacy_version=PRIVACY_POLICY_VERSION,
                tc_version=TERMS_VERSION,
                **_build_registration_extras(""),
            )

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
        db.collection(account_collection(COLLECTION_REGISTRATIONS)).document(new_uuid).set(record)
        logger.info("Lightweight cohort record created (identifier withheld)")
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

    # UNIFORM response, identical in shape to the duplicate-email branch: no
    # account-existence oracle and no unproven subject identifier handed out
    # (T P0-2 + adversarial B-3/B-6).
    return UserRegistrationResponse(
        uuid="",
        tier="",
        registered_at=now,
        message=(
            "Thanks — your interest is recorded. Finish sign-in through your "
            "MCP client's Connect flow, which verifies your email and issues "
            "your credentials. Account details are never disclosed here. "
            f"{CURRENT_AVAILABILITY_NOTICE}"
        ),
        opt_out_url="",
        privacy_version=PRIVACY_POLICY_VERSION,
        tc_version=TERMS_VERSION,
        **_build_registration_extras(""),
    )
