"""
Tests for v0.5.6 Gateway: Early Adopter Registration
Z-Protocol compliance: consent enforcement, data minimization, opt-out.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from verifimind_mcp.registration import (
    EarlyAdopterRegistration,
    FeedbackRequest,
    RegistrationResponse,
    FeedbackResponse,
    EAStatusResponse,
    OptOutResponse,
    register_early_adopter,
    get_ea_status,
    submit_feedback,
    process_optout,
    _mask_email,
)
from verifimind_mcp.utils.uuid_helper import generate_ea_uuid, generate_feedback_id
from verifimind_mcp.policies import (
    PRIVACY_POLICY,
    PRIVACY_POLICY_VERSION,
    TERMS_AND_CONDITIONS,
    TERMS_VERSION,
)


# ─────────────────────────────────────────────
# UUID Helper Tests
# ─────────────────────────────────────────────

class TestUUIDHelper:
    def test_generate_ea_uuid_is_valid_uuid_format(self):
        import uuid
        result = generate_ea_uuid()
        parsed = uuid.UUID(result)
        assert str(parsed) == result

    def test_generate_ea_uuid_version_is_7(self):
        import uuid
        result = generate_ea_uuid()
        parsed = uuid.UUID(result)
        assert parsed.version == 7

    def test_generate_ea_uuid_uniqueness(self):
        uuids = {generate_ea_uuid() for _ in range(100)}
        assert len(uuids) == 100

    def test_generate_ea_uuid_is_timestamp_ordered(self):
        import time
        u1 = generate_ea_uuid()
        time.sleep(0.01)
        u2 = generate_ea_uuid()
        # UUIDv7 is timestamp-ordered: later UUID should sort after earlier
        assert u1 < u2

    def test_generate_feedback_id_is_valid_uuid(self):
        import uuid
        result = generate_feedback_id()
        parsed = uuid.UUID(result)
        assert str(parsed) == result


# ─────────────────────────────────────────────
# Policy Document Tests
# ─────────────────────────────────────────────

class TestPolicyDocuments:
    def test_privacy_policy_not_empty(self):
        assert len(PRIVACY_POLICY) > 100
        assert "data" in PRIVACY_POLICY.lower()
        assert "opt" in PRIVACY_POLICY.lower()

    def test_privacy_policy_version_set(self):
        assert PRIVACY_POLICY_VERSION == "2.6"

    def test_terms_not_empty(self):
        assert len(TERMS_AND_CONDITIONS) > 100

    def test_terms_version_set(self):
        assert TERMS_VERSION == "2.5"

    def test_privacy_mentions_right_to_deletion(self):
        assert "delet" in PRIVACY_POLICY.lower()

    def test_terms_mentions_beta_disclaimer(self):
        assert "beta" in TERMS_AND_CONDITIONS.lower()

    def test_terms_discloses_current_no_paid_service(self):
        assert "no active paid services" in TERMS_AND_CONDITIONS.lower()
        assert "3 months" not in TERMS_AND_CONDITIONS.lower()
        assert "6 months" not in TERMS_AND_CONDITIONS.lower()


# ─────────────────────────────────────────────
# Registration Model Validation Tests
# ─────────────────────────────────────────────

class TestEarlyAdopterRegistrationModel:
    def _valid_data(self, **overrides):
        base = {
            "email": "test@example.com",
            "tc_accepted": True,
            "privacy_acknowledged": True,
        }
        base.update(overrides)
        return base

    def test_valid_registration_model(self):
        reg = EarlyAdopterRegistration(**self._valid_data())
        assert reg.email == "test@example.com"
        assert reg.tc_accepted is True
        assert reg.privacy_acknowledged is True

    def test_tc_not_accepted_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            EarlyAdopterRegistration(**self._valid_data(tc_accepted=False))
        assert "Terms" in str(exc_info.value)

    def test_privacy_not_acknowledged_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            EarlyAdopterRegistration(**self._valid_data(privacy_acknowledged=False))
        assert "Privacy" in str(exc_info.value)

    def test_invalid_email_raises_validation_error(self):
        with pytest.raises(ValidationError):
            EarlyAdopterRegistration(**self._valid_data(email="not-an-email"))

    def test_optional_fields_default_none(self):
        reg = EarlyAdopterRegistration(**self._valid_data())
        assert reg.name is None
        assert reg.feedback is None
        assert reg.feedback_type is None
        assert reg.updates_consent is False

    def test_optional_fields_accepted(self):
        reg = EarlyAdopterRegistration(**self._valid_data(
            name="Jane Doe",
            feedback="Love the Trinity validation!",
            feedback_type="returning_user",
            updates_consent=True,
        ))
        assert reg.name == "Jane Doe"
        assert reg.feedback_type == "returning_user"
        assert reg.updates_consent is True

    def test_invalid_feedback_type_raises(self):
        with pytest.raises(ValidationError):
            EarlyAdopterRegistration(**self._valid_data(feedback_type="invalid_type"))

    def test_feedback_max_length_enforced(self):
        with pytest.raises(ValidationError):
            EarlyAdopterRegistration(**self._valid_data(feedback="x" * 1001))


# ─────────────────────────────────────────────
# Registration Function Tests (Firestore mocked)
# ─────────────────────────────────────────────

def _make_registration(**overrides):
    base = {
        "email": "user@example.com",
        "tc_accepted": True,
        "privacy_acknowledged": True,
    }
    base.update(overrides)
    return EarlyAdopterRegistration(**base)


@pytest.mark.asyncio
class TestRegisterEarlyAdopter:
    async def test_new_registration_returns_response(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            data = _make_registration()
            result = await register_early_adopter(data)

        assert isinstance(result, RegistrationResponse)
        assert result.tier == "early_adopter"
        assert result.tc_version == TERMS_VERSION
        assert result.privacy_version == PRIVACY_POLICY_VERSION
        # v0.5.50 (F-RES-1): without Firestore the registration is NOT saved
        # and the response says so instead of promising benefits.
        assert result.persisted is False
        assert "NOT saved" in result.message
        assert result.opt_out_url == "/register"

    async def test_new_registration_uuid_is_valid(self):
        import uuid
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await register_early_adopter(_make_registration())
        parsed = uuid.UUID(result.uuid)
        assert parsed.version == 7

    async def test_email_masked_in_response(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await register_early_adopter(_make_registration(email="alice@example.com"))
        # Full email must not appear in response
        assert "alice@example.com" not in result.email_masked
        assert "@example.com" in result.email_masked

    async def test_feedback_received_flag(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await register_early_adopter(
                _make_registration(feedback="Great tool!")
            )
        # v0.5.50 (F-RES-1): storage down -> the feedback was NOT stored either,
        # so the flag is honestly False on the degraded path.
        assert result.feedback_received is False
        assert result.persisted is False

    async def test_no_feedback_flag_false(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await register_early_adopter(_make_registration())
        assert result.feedback_received is False

    async def test_duplicate_email_returns_existing_uuid(self):
        existing_uuid = "01950000-0000-7000-8000-000000000001"
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "uuid": existing_uuid,
            "email": "user@example.com",
            "registered_at": "2026-03-18T00:00:00+00:00",
            "tier": "early_adopter",
            "tc_version": "1.0",
            "privacy_version": "1.0",
            "benefits": {"v060_beta_free_until": "2026-06-18T00:00:00+00:00"},
        }
        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.limit.return_value.get.return_value = [mock_doc]

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await register_early_adopter(_make_registration())

        assert result.uuid == existing_uuid
        assert "already registered" in result.message

    async def test_registration_has_no_timed_access_entitlement(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await register_early_adopter(_make_registration())

        assert result.free_months is None
        assert result.benefits_free_until is None
        assert "not create a time-limited" in result.availability_notice


# ─────────────────────────────────────────────
# Feedback Tests
# ─────────────────────────────────────────────

@pytest.mark.asyncio
class TestSubmitFeedback:
    async def test_anonymous_feedback_accepted(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            data = FeedbackRequest(
                content="Love the Z Guardian agent!",
                feedback_type="feedback",
            )
            result = await submit_feedback(data)

        assert isinstance(result, FeedbackResponse)
        assert result.feedback_id
        assert "Thank you" in result.message

    async def test_registered_user_feedback(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            data = FeedbackRequest(
                content="The CS agent found a real security issue in my code.",
                feedback_type="recommendation",
                uuid="01950000-0000-7000-8000-000000000001",
                connection_context="consult_agent_cs",
            )
            result = await submit_feedback(data)

        assert isinstance(result, FeedbackResponse)

    async def test_feedback_id_is_unique(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            data = FeedbackRequest(content="Test", feedback_type="general")
            r1 = await submit_feedback(data)
            r2 = await submit_feedback(data)
        assert r1.feedback_id != r2.feedback_id

    async def test_invalid_feedback_type_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackRequest(content="Test", feedback_type="invalid")

    async def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackRequest(content="", feedback_type="general")


# ─────────────────────────────────────────────
# EA Status Tests
# ─────────────────────────────────────────────

@pytest.mark.asyncio
class TestGetEAStatus:
    async def test_unknown_uuid_returns_none(self):
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await get_ea_status("unknown-uuid")

        assert result is None

    async def test_known_uuid_returns_status(self):
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "uuid": "test-uuid",
            "tier": "early_adopter",
            "registered_at": "2026-03-18T00:00:00+00:00",
            "benefits": {"v060_beta_free_until": "2026-06-18T00:00:00+00:00"},
            "status": "active",
            "updates_consent": False,
        }
        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await get_ea_status("test-uuid")

        assert isinstance(result, EAStatusResponse)
        assert result.tier == "early_adopter"
        assert result.status == "active"

    async def test_firestore_unavailable_returns_none(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await get_ea_status("any-uuid")
        assert result is None


# ─────────────────────────────────────────────
# Opt-Out Tests
# ─────────────────────────────────────────────

@pytest.mark.asyncio
class TestProcessOptout:
    async def test_optout_returns_confirmation(self):
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            result = await process_optout("some-uuid")

        assert isinstance(result, OptOutResponse)
        assert result.processed is False
        assert result.deletion_scheduled_within is None
        assert "No deletion action is confirmed" in result.message

    async def test_optout_updates_firestore_record(self):
        # Design v2 UNION revocation (T S152 P0 #2): opt-out must revoke the
        # identity in BOTH registration collections and tombstone every live
        # OAuth/PAT credential — success only when all stores answered.
        class _Doc:
            def __init__(self, store, key):
                self._store, self._key = store, key

            def get(self):
                doc = MagicMock()
                doc.exists = self._key in self._store
                doc.to_dict.return_value = self._store.get(self._key)
                return doc

            def update(self, fields):
                self._store[self._key].update(fields)

        class _Query:
            def __init__(self, store, filters):
                self._store, self._filters = store, filters

            def where(self, field, op, value):
                return _Query(self._store, self._filters + [(field, value)])

            def get(self):
                out = []
                for key, data in self._store.items():
                    if all(data.get(f) == v for f, v in self._filters):
                        snap = MagicMock()
                        snap.to_dict.return_value = data
                        snap.reference = _Doc(self._store, key)
                        out.append(snap)
                return out

        class _Coll:
            def __init__(self, store):
                self._store = store

            def document(self, key):
                return _Doc(self._store, key)

            def where(self, field, op, value):
                return _Query(self._store, [(field, value)])

        class _Db:
            def __init__(self):
                self.data = {
                    "early_adopters": {"test-uuid": {
                        "uuid": "test-uuid", "email": "a@b.co", "status": "active",
                    }},
                    "ea_registrations": {"test-uuid": {
                        "uuid": "test-uuid", "email": "a@b.co", "status": "active",
                    }},
                    "oauth_tokens": {"tok1": {
                        "token_id": "tok1", "subject_uuid": "test-uuid",
                        "revoked": False,
                    }},
                }

            def collection(self, name):
                return _Coll(self.data.setdefault(name, {}))

        db = _Db()
        with patch("verifimind_mcp.registration._get_firestore", return_value=db):
            result = await process_optout("test-uuid")

        assert db.data["early_adopters"]["test-uuid"]["status"] == "deletion_requested"
        assert db.data["early_adopters"]["test-uuid"]["email"] == "[deletion_requested]"
        assert db.data["ea_registrations"]["test-uuid"]["status"] == "deletion_requested"
        assert db.data["oauth_tokens"]["tok1"]["revoked"] is True
        assert result.processed is True
        assert "7 business days" in result.deletion_scheduled_within
        assert "purged" in result.message

    async def test_firestore_read_failure_returns_retryable_non_confirmation(self):
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.side_effect = RuntimeError("backend-secret-read-error")
        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await process_optout("sensitive-uuid")

        assert result.processed is False
        assert result.deletion_scheduled_within is None
        assert "No deletion action is confirmed" in result.message
        assert "backend-secret" not in result.message
        assert "sensitive-uuid" not in result.message
        mock_doc_ref.update.assert_not_called()

    async def test_firestore_write_failure_returns_retryable_non_confirmation(self):
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.update.side_effect = RuntimeError("backend-secret-write-error")
        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await process_optout("sensitive-uuid")

        assert result.processed is False
        assert result.deletion_scheduled_within is None
        assert "No deletion action is confirmed" in result.message
        assert "backend-secret" not in result.message
        assert "sensitive-uuid" not in result.message

    async def test_http_handler_returns_503_when_deletion_is_not_confirmed(self):
        import http_server

        class Request:
            path_params = {"uuid": "some-uuid"}

        unavailable = OptOutResponse(
            processed=False,
            message="No deletion action is confirmed.",
        )
        with patch(
            "http_server.process_optout",
            new=AsyncMock(return_value=unavailable),
        ):
            response = await http_server.ea_optout_handler(Request())

        assert response.status_code == 503
        assert b"No deletion action is confirmed" in response.body

    async def test_http_handler_normalizes_unexpected_failure_to_structured_503(self):
        import http_server

        class Request:
            path_params = {"uuid": "sensitive-uuid"}

        with patch(
            "http_server.process_optout",
            new=AsyncMock(side_effect=RuntimeError("backend-secret-handler-error")),
        ):
            response = await http_server.ea_optout_handler(Request())

        assert response.status_code == 503
        body = response.body.decode("utf-8")
        assert '"processed":false' in body
        assert "No deletion action is confirmed" in body
        assert "backend-secret" not in body
        assert "sensitive-uuid" not in body


# ─────────────────────────────────────────────
# Email Masking Tests
# ─────────────────────────────────────────────

class TestMaskEmail:
    def test_standard_email_masked(self):
        assert _mask_email("alice@example.com") == "a***@example.com"

    def test_single_char_local_masked(self):
        result = _mask_email("a@example.com")
        assert "@example.com" in result

    def test_invalid_format_returns_safe_fallback(self):
        result = _mask_email("notanemail")
        assert result == "***@***"
