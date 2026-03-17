"""
VerifiMind-PEAS Early Adopter Registration — v0.5.6 Gateway
Z-Protocol v1.1 compliant: consent-first, data minimization, explicit opt-out.

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

# EA benefit: 3 months free v0.6.0-Beta access
EA_BETA_FREE_MONTHS = 3

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
    registered_at: str
    benefits_free_until: str
    tc_version: str
    privacy_version: str
    message: str
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

    try:
        from google.cloud import firestore  # type: ignore
        project_id = os.environ.get("FIRESTORE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            _firestore_client = firestore.Client(project=project_id)
        else:
            _firestore_client = firestore.Client()
        logger.info("Firestore client initialized")
        return _firestore_client
    except Exception as e:
        logger.warning(f"Firestore unavailable: {e} — EA registration will use fallback storage")
        return None


# ─────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────

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


def _benefits_until_iso() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=EA_BETA_FREE_MONTHS * 30)
    return dt.isoformat()


async def register_early_adopter(data: EarlyAdopterRegistration) -> RegistrationResponse:
    """Register a new Early Adopter or return existing record for duplicate email.

    Idempotent: same email → returns existing UUID (no duplicate records).
    """
    db = _get_firestore()
    now = _now_iso()
    benefits_until = _benefits_until_iso()

    if db is not None:
        # Check for duplicate email
        existing = db.collection(COLLECTION_EA).where("email", "==", str(data.email)).limit(1).get()
        if existing:
            doc = existing[0].to_dict()
            logger.info(f"Duplicate EA registration for masked email {_mask_email(str(data.email))} — returning existing UUID")
            return RegistrationResponse(
                uuid=doc["uuid"],
                email_masked=_mask_email(str(data.email)),
                tier=doc.get("tier", "early_adopter"),
                registered_at=doc["registered_at"],
                benefits_free_until=doc["benefits"]["v060_beta_free_until"],
                tc_version=doc.get("tc_version", TERMS_VERSION),
                privacy_version=doc.get("privacy_version", PRIVACY_POLICY_VERSION),
                message="You're already registered as an Early Adopter! Your UUID and benefits are unchanged.",
                opt_out_url=f"/early-adopters/optout/{doc['uuid']}",
                feedback_received=False,
            )

        # New registration
        new_uuid = generate_ea_uuid()
        record = {
            "uuid": new_uuid,
            "email": str(data.email),  # stored securely in Firestore, never logged
            "name": data.name,
            "registered_at": now,
            "tier": "early_adopter",
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
        db.collection(COLLECTION_EA).document(new_uuid).set(record)
        logger.info(f"New EA registered: UUID={new_uuid}")

        # Store registration feedback separately if provided
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
        logger.warning("Firestore unavailable — EA registration cannot be persisted")
        new_uuid = generate_ea_uuid()

    return RegistrationResponse(
        uuid=new_uuid,
        email_masked=_mask_email(str(data.email)),
        tier="early_adopter",
        registered_at=now,
        benefits_free_until=benefits_until,
        tc_version=TERMS_VERSION,
        privacy_version=PRIVACY_POLICY_VERSION,
        message=(
            f"Welcome to the VerifiMind-PEAS Early Adopter program! "
            f"Your UUID is your access key. Save it — you'll need it to check your status "
            f"and access v0.6.0-Beta when it launches. "
            f"Your 3 months free access expires on {benefits_until[:10]}."
        ),
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
