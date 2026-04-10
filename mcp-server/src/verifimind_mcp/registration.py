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
from datetime import datetime, timezone, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .utils.uuid_helper import generate_ea_uuid, generate_feedback_id
from .policies import PRIVACY_POLICY_VERSION, TERMS_VERSION

logger = logging.getLogger(__name__)

# ── Tier constants ─────────────────────────────────────────────────────────────
# Pilot tier: active MCP users invited via SYSTEM_NOTICE
PILOT_FREE_MONTHS = 6
PILOT_MAX_SLOTS = 50

# Early Adopter tier: public open registration
EA_BETA_FREE_MONTHS = 3
EA_MAX_SLOTS = 100

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
    free_months: int = EA_BETA_FREE_MONTHS
    registered_at: str
    benefits_free_until: str
    tc_version: str
    privacy_version: str
    message: str
    benefit_summary: str = ""
    opt_out_url: str
    feedback_received: bool


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
    benefits_free_until: str
    status: str
    updates_consent: bool


class OptOutResponse(BaseModel):
    """Response after opt-out request."""
    message: str
    deletion_scheduled_within: str = "7 business days"


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


# ─────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────

class SlotCapReachedError(Exception):
    """Raised when a tier's slot cap is full."""
    def __init__(self, tier: str, max_slots: int):
        self.tier = tier
        self.max_slots = max_slots
        super().__init__(f"{tier} slots full ({max_slots}/{max_slots})")


def _build_benefit_summary(tier: str, tier_label: str, benefits_until: str) -> str:
    """Build a clear human-readable benefit summary for the registration response."""
    free_months = PILOT_FREE_MONTHS if tier == "pilot" else EA_BETA_FREE_MONTHS
    until_date = benefits_until[:10]
    if tier == "pilot":
        return (
            f"Pilot Member: {free_months} months FREE v0.6.0-Beta access (launching Jun 2026). "
            f"Free until {until_date}. You are among our 50-slot exclusive Pilot cohort."
        )
    return (
        f"Early Adopter: {free_months} months FREE v0.6.0-Beta access (launching Jun 2026). "
        f"Free until {until_date}. One of 100 open Early Adopter slots."
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


def _benefits_until_iso(months: int) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=months * 30)
    return dt.isoformat()


def _count_tier_slots(db, tier: str) -> int:
    """Count registered slots for a given tier. Returns 0 if Firestore unavailable."""
    try:
        docs = db.collection(COLLECTION_EA).where("tier", "==", tier).where("status", "==", "active").count().get()
        return int(docs[0][0].value)
    except Exception as e:
        logger.warning(f"Slot count query failed for tier={tier}: {e}")
        return 0


async def register_early_adopter(data: EarlyAdopterRegistration) -> RegistrationResponse:
    """Register a new Early Adopter or Pilot, or return existing record for duplicate email.

    Tier assignment:
    - Pilot (6 months free, 50 slots): valid invite_code matching PILOT_INVITE_CODE env var
    - Early Adopter (3 months free, 100 slots): everyone else

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
    free_months = PILOT_FREE_MONTHS if is_pilot else EA_BETA_FREE_MONTHS
    max_slots = PILOT_MAX_SLOTS if is_pilot else EA_MAX_SLOTS
    benefits_until = _benefits_until_iso(free_months)

    if db is not None:
        # ── Slot cap check ──────────────────────────────────────────────────────
        current_slots = _count_tier_slots(db, tier)
        if current_slots >= max_slots:
            logger.info(f"Slot cap reached for tier={tier}: {current_slots}/{max_slots}")
            raise SlotCapReachedError(tier, max_slots)

        # ── Duplicate email check ───────────────────────────────────────────────
        existing = db.collection(COLLECTION_EA).where("email", "==", str(data.email)).limit(1).get()
        if existing:
            doc = existing[0].to_dict()
            existing_tier = doc.get("tier", "early_adopter")
            existing_label = "Pilot Member" if existing_tier == "pilot" else "Early Adopter"
            existing_until = doc["benefits"]["v060_beta_free_until"]
            logger.info(f"Duplicate registration for masked email {_mask_email(str(data.email))} — returning existing UUID")
            return RegistrationResponse(
                uuid=doc["uuid"],
                email_masked=_mask_email(str(data.email)),
                tier=existing_tier,
                tier_label=existing_label,
                free_months=doc.get("pilot_free_months", EA_BETA_FREE_MONTHS) if existing_tier == "pilot" else EA_BETA_FREE_MONTHS,
                registered_at=doc["registered_at"],
                benefits_free_until=existing_until,
                tc_version=doc.get("tc_version", TERMS_VERSION),
                privacy_version=doc.get("privacy_version", PRIVACY_POLICY_VERSION),
                message=f"You're already registered as {existing_label}! Your UUID and benefits are unchanged.",
                benefit_summary=_build_benefit_summary(existing_tier, existing_label, existing_until),
                opt_out_url=f"/early-adopters/optout/{doc['uuid']}",
                feedback_received=False,
            )

        # ── New registration ────────────────────────────────────────────────────
        new_uuid = generate_ea_uuid()
        record = {
            "uuid": new_uuid,
            "email": str(data.email),  # stored securely in Firestore, never logged
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
            "benefits": {
                "v060_beta_free": True,
                "v060_beta_free_until": benefits_until,
            },
            "registration_feedback": data.feedback,
            "feedback_type": data.feedback_type or ("new_user" if not data.feedback else "general"),
            "status": "active",
        }
        if is_pilot:
            record["pilot_free_months"] = PILOT_FREE_MONTHS
            record["pilot_source"] = "system_notice_invite"
        db.collection(COLLECTION_EA).document(new_uuid).set(record)
        logger.info(f"New {tier} registered: UUID={new_uuid}")

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
        # Fallback: Firestore unavailable — generate UUID but cannot persist
        logger.warning("Firestore unavailable — registration cannot be persisted")
        new_uuid = generate_ea_uuid()

    return RegistrationResponse(
        uuid=new_uuid,
        email_masked=_mask_email(str(data.email)),
        tier=tier,
        tier_label=tier_label,
        free_months=free_months,
        registered_at=now,
        benefits_free_until=benefits_until,
        tc_version=TERMS_VERSION,
        privacy_version=PRIVACY_POLICY_VERSION,
        message=(
            f"Welcome to the VerifiMind-PEAS {tier_label} program! "
            f"Your UUID is your access key — save it. "
            f"You receive {free_months} months free access to v0.6.0-Beta when it launches. "
            f"Your free access runs until {benefits_until[:10]}."
        ),
        benefit_summary=_build_benefit_summary(tier, tier_label, benefits_until),
        opt_out_url=f"/early-adopters/optout/{new_uuid}",
        feedback_received=bool(data.feedback),
    )


async def get_ea_status(uuid: str) -> Optional[EAStatusResponse]:
    """Return EA status for a given UUID. Returns None if not found."""
    db = _get_firestore()
    if db is None:
        return None

    doc = db.collection(COLLECTION_EA).document(uuid).get()
    if not doc.exists:
        return None

    data = doc.to_dict()
    return EAStatusResponse(
        uuid=data["uuid"],
        tier=data.get("tier", "early_adopter"),
        registered_at=data["registered_at"],
        benefits_free_until=data["benefits"]["v060_beta_free_until"],
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
    """Mark EA record for deletion. Data purged within 7 business days."""
    db = _get_firestore()

    if db is not None:
        doc_ref = db.collection(COLLECTION_EA).document(uuid)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({
                "status": "deletion_requested",
                "deletion_requested_at": _now_iso(),
                # Immediately nullify PII fields
                "email": "[deletion_requested]",
                "name": None,
                "registration_feedback": None,
            })
            logger.info(f"Opt-out processed for UUID={uuid}")
        else:
            logger.info(f"Opt-out request for unknown UUID={uuid} — no action taken")

    return OptOutResponse(
        message=(
            "Your opt-out request has been received. All personal data associated "
            "with your Early Adopter account will be purged within 7 business days. "
            "Your UUID will no longer grant EA benefits after deletion is complete. "
            "The free Trinity validation tier (v0.5.5) remains available without registration."
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# v0.5.13 "Fortify" — Lightweight /register endpoint
# XV PIN #49 architecture: email optional, UUID = identity spine
# ─────────────────────────────────────────────────────────────────────────────

# Polar Pioneer checkout URL — set via GCP env var
_POLAR_CHECKOUT_URL = os.environ.get(
    "POLAR_CHECKOUT_URL",
    "https://polar.sh/ysenseai-ecosystem/pioneer",
)

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
        description="You consent to the Privacy Policy v2.0 and Terms & Conditions v2.0"
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
    """Response from POST /register — v0.5.13."""
    uuid: str
    tier: str = "ea"
    registered_at: str
    expires_at: str
    pioneer_checkout: str
    message: str
    opt_out_url: str
    privacy_version: str
    tc_version: str


async def register_user(data: UserRegistrationRequest) -> UserRegistrationResponse:
    """Register a new user with minimal data — UUID is their identity.

    XV PIN #49 architecture (v0.5.13):
    - Email is optional: consent-only registration returns a UUID
    - UUID is UUIDv7 (time-ordered for Firestore query efficiency)
    - UUID = Polar external_id when user upgrades to Pioneer
    - Anonymous Scholar users are NOT required to register (zero friction)
    - pioneer_checkout URL embeds UUID as Polar customer_metadata.external_id

    Idempotent by UUID — each call generates a new UUID (email-based
    dedup is best-effort only, not enforced for privacy-first anonymous path).
    """
    db = _get_firestore()
    now = _now_iso()
    new_uuid = generate_ea_uuid()
    expires_at = _benefits_until_iso(EA_BETA_FREE_MONTHS)

    # Best-effort email dedup (only when email provided and Firestore available)
    if data.email and db is not None:
        existing = (
            db.collection(COLLECTION_REGISTRATIONS)
            .where("email", "==", str(data.email))
            .limit(1)
            .get()
        )
        if existing:
            doc = existing[0].to_dict()
            logger.info(
                "Lightweight register: duplicate email %s — returning existing UUID",
                _mask_email(str(data.email)),
            )
            checkout = f"{_POLAR_CHECKOUT_URL}?customer[external_id]={doc['uuid']}"
            return UserRegistrationResponse(
                uuid=doc["uuid"],
                tier=doc.get("tier", "ea"),
                registered_at=doc["registered_at"],
                expires_at=doc.get("expires_at", expires_at),
                pioneer_checkout=checkout,
                message=(
                    "You're already registered! Your UUID and Pioneer checkout link are below. "
                    "Save your UUID — it is your permanent identity."
                ),
                opt_out_url=f"/early-adopters/optout/{doc['uuid']}",
                privacy_version=PRIVACY_POLICY_VERSION,
                tc_version=TERMS_VERSION,
            )

    # Store in Firestore (when available)
    if db is not None:
        record = {
            "uuid": new_uuid,
            "email": str(data.email) if data.email else None,
            "display_name": data.display_name,
            "tier": "ea",
            "registered_at": now,
            "expires_at": expires_at,
            "consent": True,
            "consent_ts": now,
            "privacy_version": PRIVACY_POLICY_VERSION,
            "tc_version": TERMS_VERSION,
            "status": "active",
            "registration_path": "lightweight_v0513",
        }
        db.collection(COLLECTION_REGISTRATIONS).document(new_uuid).set(record)
        logger.info("Lightweight registration: UUID=%s", new_uuid)
    else:
        logger.warning("Firestore unavailable — lightweight registration UUID=%s not persisted", new_uuid)

    checkout = f"{_POLAR_CHECKOUT_URL}?customer[external_id]={new_uuid}"

    return UserRegistrationResponse(
        uuid=new_uuid,
        tier="ea",
        registered_at=now,
        expires_at=expires_at,
        pioneer_checkout=checkout,
        message=(
            "Registration successful! Your UUID is your permanent identity — save it. "
            f"Use the pioneer_checkout URL to upgrade to Pioneer tier ($9/month). "
            f"Free EA access runs until {expires_at[:10]}."
        ),
        opt_out_url=f"/early-adopters/optout/{new_uuid}",
        privacy_version=PRIVACY_POLICY_VERSION,
        tc_version=TERMS_VERSION,
    )
