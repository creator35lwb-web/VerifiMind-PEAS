"""CS round 4 (2026-09-05, T S158) identity/provenance findings at ``2c43cd5``.

F1  unverified preregistration state crossed the mailbox-verification
    boundary: anyone could pre-register a victim's address with marketing
    consent, cohort privilege, profile, and feedback; adoption wiped only the
    name and inline feedback, kept ``updates_consent`` and the separately
    linked feedback document — and no canonical owner per email existed
    across the two registration lanes (query-then-write in two collections)
F2  anonymous feedback persisted a caller-claimed victim UUID as attribution
F3  both email-registration lanes were account-existence oracles: the
    new-vs-duplicate responses differed in message and flags
F4  owner routes (dashboard, opt-out) collapsed a credential-store outage
    into 401 instead of a retryable, non-enumerating 503

Every test whose comment begins with "2c43cd5:" was demonstrated FAILING
against the ``2c43cd5`` tree — its FIRST failing assertion is the stated one
(sparse-worktree receipt in the S161 record). Tests marked "pin:" pass at
both heads; they prove the repair moved nothing next to it.
"""

import asyncio
import hashlib
import threading
import types
import warnings
from unittest.mock import patch

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from verifimind_mcp import registration
from verifimind_mcp.middleware import rate_limiter
from verifimind_mcp.oauth import endpoints, stores
from verifimind_mcp.oauth.stores import StoreUnavailable

from .test_auth_boundary import _issue_access
from .test_cs_round3_security import RecordingFirestore

VICTIM_EMAIL = "victim@example.com"
UUID_OTHER = "018f6b2a-cccc-7abc-8def-0123456789ab"
REGISTRATION_NOW = "2026-09-05T08:00:00+00:00"
CEREMONY_NOW = "2026-09-05T09:30:00+00:00"
PILOT_CODE = "pilot-invite-for-tests"
FEEDBACK_TEXT = "The Trinity summary was clear; the CS questions were sharp."


def _owner_key(email):
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setattr(registration, "PILOT_INVITE_CODE", PILOT_CODE)
    monkeypatch.setattr(registration, "_now_iso", lambda: REGISTRATION_NOW)


@pytest.fixture()
def rdb(env):
    fake = RecordingFirestore()
    stores.clear_caches()
    rate_limiter._uuid_tier_cache.clear()
    with patch("verifimind_mcp.registration._get_firestore", side_effect=fake.handed_out):
        yield fake
    stores.clear_caches()


@pytest.fixture()
def http(monkeypatch):
    import http_server
    from starlette.testclient import TestClient

    monkeypatch.setattr(rate_limiter, "_rate_limit_store", rate_limiter.RateLimitStore())
    with TestClient(http_server.app) as client:
        yield client


def _ea(email=VICTIM_EMAIL, **extra):
    fields = dict(email=email, tc_accepted=True, privacy_acknowledged=True)
    fields.update(extra)
    return registration.EarlyAdopterRegistration(**fields)


def _light(email=VICTIM_EMAIL, **extra):
    return registration.UserRegistrationRequest(consent=True, email=email, **extra)


def _run_elsewhere(coro):
    """Drive a coroutine on its own event loop in another thread — the way a
    concurrent request would run — from inside synchronous code under test."""
    out = {}

    def target():
        out["value"] = asyncio.run(coro)

    worker = threading.Thread(target=target)
    worker.start()
    worker.join()
    return out["value"]


def _accounts(rdb, email):
    """Every account record for ``email`` across BOTH lanes."""
    found = []
    for name in ("early_adopters", "ea_registrations"):
        for doc_id, doc in rdb.docs(name).items():
            if doc.get("email") == email:
                found.append((name, doc_id, doc))
    return found


def _feedback_post(http, headers=None, **fields):
    body = {"content": FEEDBACK_TEXT, "feedback_type": "general"}
    body.update(fields)
    return http.post("/early-adopters/feedback", json=body, headers=headers or {})


# ── contract 1 · one canonical owner per email across both lanes ────────────

class TestCanonicalEmailOwnership:
    def test_second_lane_cannot_create_a_second_account_for_the_same_email(self, rdb):
        # 2c43cd5: each lane checked only its own collection, so one address
        # got two accounts and the verified resolver adopted whichever it
        # scanned first.
        asyncio.run(registration.register_early_adopter(_ea()))
        second = asyncio.run(registration.register_user(_light()))
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1
        assert second.uuid == "" and second.persisted is True
        owner = rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]
        assert owner["uuid"] == _accounts(rdb, VICTIM_EMAIL)[0][2]["uuid"]

    def test_reverse_lane_order_is_also_one_owner(self, rdb):
        # 2c43cd5: same defect, opposite order.
        asyncio.run(registration.register_user(_light()))
        asyncio.run(registration.register_early_adopter(_ea()))
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1
        assert len(rdb.docs("email_owners")) == 1

    def test_legacy_record_in_the_other_lane_blocks_a_new_account(self, rdb):
        # 2c43cd5: the lightweight lane checked only ea_registrations, so a
        # legacy early_adopters record (written before claims existed) did
        # not stop a second account for the same address — and vice versa.
        rdb.seed("early_adopters", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
        })
        light = asyncio.run(registration.register_user(_light()))
        assert light.uuid == "" and len(_accounts(rdb, VICTIM_EMAIL)) == 1
        rdb.seed("ea_registrations", "018f6b2a-dddd-7abc-8def-0123456789ab", {
            "uuid": "018f6b2a-dddd-7abc-8def-0123456789ab", "email": "other@example.com",
            "status": "active", "email_verified": False,
        })
        ea = asyncio.run(registration.register_early_adopter(_ea(email="other@example.com")))
        assert ea.uuid == "" and len(_accounts(rdb, "other@example.com")) == 1

    def test_a_claimed_email_is_owned_even_before_its_record_is_visible(self, rdb):
        # 2c43cd5: no claim existed, so a concurrent winner could not stop the
        # loser — both wrote accounts. The claim document is the atomic
        # create-if-absent that lets exactly one caller win.
        rdb.seed("email_owners", _owner_key(VICTIM_EMAIL), {
            "uuid": UUID_OTHER, "collection": "ea_registrations", "verified": False,
        })
        result = asyncio.run(registration.register_early_adopter(_ea()))
        assert result.uuid == ""
        assert _accounts(rdb, VICTIM_EMAIL) == []
        assert rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]["uuid"] == UUID_OTHER

    def test_verified_ceremony_creates_one_subject_and_its_claim(self, rdb):
        # 2c43cd5: the ceremony wrote a record but no ownership claim, so a
        # later preregistration could still plant a second record.
        subject = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert subject
        claim = rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]
        assert claim["uuid"] == subject and claim["verified"] is True
        record = rdb.docs("ea_registrations")[subject]
        assert record["email_verified"] is True and record["updates_consent"] is False
        assert record["tier"] == "ea" and record["consent_ts"] == REGISTRATION_NOW
        later = asyncio.run(registration.register_early_adopter(_ea()))
        assert later.uuid == "" and len(_accounts(rdb, VICTIM_EMAIL)) == 1

    def test_legacy_record_without_a_claim_is_backfilled_and_adopted(self, rdb):
        # 2c43cd5: legacy adoption created no claim, leaving the address open
        # to a second owner.
        rdb.seed("early_adopters", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "active",
            "email_verified": False, "tier": "early_adopter", "updates_consent": True,
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == UUID_OTHER
        claim = rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]
        assert claim["uuid"] == UUID_OTHER
        assert claim["collection"] == "early_adopters" and claim["verified"] is True

    def test_claim_without_a_record_is_healed_under_the_claimed_identifier(self, rdb):
        # 2c43cd5: no claim concept — the ceremony minted a fresh identifier,
        # so one address could end up with two.
        rdb.seed("email_owners", _owner_key(VICTIM_EMAIL), {
            "uuid": UUID_OTHER, "collection": "ea_registrations", "verified": False,
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == UUID_OTHER
        healed = rdb.docs("ea_registrations")[UUID_OTHER]
        assert healed["email_verified"] is True and healed["tier"] == "ea"
        assert rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]["verified"] is True

    def test_a_claim_in_the_ea_lane_is_healed_with_that_lanes_default_tier(self, rdb):
        # 2c43cd5: no claim concept. The healed record lives in the collection
        # the claim names and carries THAT lane's default tier (Lens B, M15).
        rdb.seed("email_owners", _owner_key(VICTIM_EMAIL), {
            "uuid": UUID_OTHER, "collection": "early_adopters", "verified": False,
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == UUID_OTHER
        healed = rdb.docs("early_adopters")[UUID_OTHER]
        assert healed["email_verified"] is True and healed["tier"] == "early_adopter"

    def test_a_competitor_that_claims_first_wins_the_lane_race(self, rdb, monkeypatch):
        # 2c43cd5: no claim — both writers created accounts. Here the OTHER
        # lane registers the same address between this lane's legacy scan and
        # its claim: the store decides, this caller loses, and exactly one
        # account exists — the competitor's.
        original = registration.claim_email
        raced = {}

        def contested_claim(db, owners, email, **kw):
            if not raced:  # the competitor runs exactly once, inside the window
                raced["done"] = True
                _run_elsewhere(registration.register_user(_light()))
            return original(db, owners, email, **kw)

        monkeypatch.setattr(registration, "claim_email", contested_claim)
        result = asyncio.run(registration.register_early_adopter(_ea()))
        assert result.uuid == ""
        ((name, uuid, _),) = _accounts(rdb, VICTIM_EMAIL)
        assert name == "ea_registrations"
        assert rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]["uuid"] == uuid

    def test_resolver_adopts_the_concurrent_winner_instead_of_forking(self, rdb, monkeypatch):
        # 2c43cd5: no claim — the ceremony wrote its own record next to the
        # competitor's. Here a lane registration claims the address between
        # the ceremony's legacy scan and its claim: the ceremony loses the
        # claim, re-reads it, and adopts (sanitized) the winner's record
        # (Lens B, M29: the re-read path must be live).
        original = registration.claim_email
        raced = {}

        def contested_claim(db, owners, email, **kw):
            if not raced:
                raced["done"] = True
                _run_elsewhere(registration.register_early_adopter(_ea(name="Mallory", updates_consent=True)))
            return original(db, owners, email, **kw)

        monkeypatch.setattr(registration, "claim_email", contested_claim)
        subject = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        ((name, uuid, record),) = _accounts(rdb, VICTIM_EMAIL)
        assert subject == uuid and name == "early_adopters"
        assert record["email_verified"] is True and record["updates_consent"] is False
        assert record["name"] is None

    def test_the_claim_is_one_atomic_create_and_nothing_else(self, rdb):
        # 2c43cd5: no claim at all. On the repaired tree this pins the
        # primitive (Lens B, M27c): a check-then-set claim would pass every
        # other test on the single-threaded fake — the ownership claim must be
        # exactly ONE create-if-absent on the owners collection, no read and
        # no set, so the race is decided by the store, not by the caller.
        ops = []
        original_collection = rdb.collection

        def recording_collection(name):
            collection = original_collection(name)
            if name != "email_owners":
                return collection
            original_document = collection.document

            def document(doc_id):
                reference = original_document(doc_id)

                class _Proxy:
                    def __getattr__(self, op):
                        target = getattr(reference, op)
                        if not callable(target):
                            return target

                        def call(*args, **kwargs):
                            ops.append(op)
                            return target(*args, **kwargs)

                        return call

                return _Proxy()

            collection.document = document
            return collection

        rdb.collection = recording_collection
        asyncio.run(registration.register_early_adopter(_ea()))
        assert ops == ["create"]

    def test_owner_key_is_canonical(self):
        # 2c43cd5: no canonical owner key existed at all.
        assert registration.email_owner_key("  Victim@Example.COM ") == _owner_key(VICTIM_EMAIL)


# ── contracts 1/2 · mailbox proof is a sanitizer, not retroactive authorship ─

class TestVerifiedAdoptionSanitizer:
    @staticmethod
    def _preregister_victim(rdb):
        result = asyncio.run(registration.register_early_adopter(_ea(
            name="Mallory", updates_consent=True, feedback="attacker-linked-feedback",
            feedback_type="general", invite_code=PILOT_CODE,
        )))
        assert result.uuid == ""
        ((_, victim_uuid, record),) = _accounts(rdb, VICTIM_EMAIL)
        assert record["email_verified"] is False and record["tier"] == "pilot"
        return victim_uuid

    def test_attacker_chosen_consent_privilege_and_profile_do_not_survive_proof(self, rdb, monkeypatch):
        # 2c43cd5: adoption wiped name/inline feedback but kept
        # updates_consent=True, tier=pilot, pilot_source and the attacker's
        # consent timestamps (T probe: adopted_updates_consent: True).
        victim_uuid = self._preregister_victim(rdb)
        monkeypatch.setattr(registration, "_now_iso", lambda: CEREMONY_NOW)
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == victim_uuid
        record = rdb.docs("early_adopters")[victim_uuid]
        assert record["email_verified"] is True
        assert record["updates_consent"] is False
        assert record["tier"] == "early_adopter" and record["pilot_source"] is None
        assert record["name"] is None and record["registration_feedback"] is None
        assert record["feedback_type"] is None
        # The verified actor's OWN ceremony supplies acceptance.
        assert record["tc_accepted_at"] == CEREMONY_NOW
        assert record["privacy_acknowledged_at"] == CEREMONY_NOW
        assert record["consent_ts"] == CEREMONY_NOW
        assert record["consent_source"] == "oauth_ceremony_v2"
        assert "updates_consent" in record["preregistration"]["neutralized"]

    def test_lightweight_preregistration_profile_does_not_survive_proof(self, rdb):
        # 2c43cd5: the lightweight lane's display_name survived adoption only
        # by the round-3 test's grace; round 4 pins it here (Lens B, M10).
        asyncio.run(registration.register_user(_light(display_name="Mallory")))
        ((_, victim_uuid, record),) = _accounts(rdb, VICTIM_EMAIL)
        assert record["display_name"] == "Mallory" and record["email_verified"] is False
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == victim_uuid
        record = rdb.docs("ea_registrations")[victim_uuid]
        assert record["email_verified"] is True and record["display_name"] is None
        assert record["updates_consent"] is False

    def test_claim_path_adoption_detaches_legacy_linked_feedback(self, rdb):
        # 2c43cd5: adoption never detached anything. On the repaired tree this
        # pins the CLAIM-EXISTS path, not only the legacy-backfill path
        # (Lens B, M11).
        rdb.seed("email_owners", _owner_key(VICTIM_EMAIL), {
            "uuid": UUID_OTHER, "collection": "early_adopters", "verified": False,
        })
        rdb.seed("early_adopters", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
        })
        rdb.seed("feedback", "fb-legacy", {"feedback_id": "fb-legacy", "uuid": UUID_OTHER})
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == UUID_OTHER
        assert rdb.docs("feedback")["fb-legacy"]["uuid"] is None

    def test_linked_feedback_never_becomes_the_verified_subjects_content(self, rdb):
        # 2c43cd5: the lane linked the feedback document to the preregistered
        # UUID (uuid=<victim>) and adoption never detached it
        # (T probe: linked_feedback_survives_adoption: True).
        victim_uuid = self._preregister_victim(rdb)
        endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert [doc for doc in rdb.docs("feedback").values() if doc.get("uuid") == victim_uuid] == []
        (doc,) = rdb.docs("feedback").values()
        assert doc["uuid"] is None
        assert doc["attribution"] == "registration_unverified"
        assert doc["registration_uuid_unverified"] == victim_uuid

    def test_legacy_linked_feedback_is_detached_on_proof(self, rdb):
        # 2c43cd5: a pre-existing feedback record carrying uuid=<victim> kept
        # that attribution after the victim proved the mailbox.
        rdb.seed("early_adopters", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
        })
        rdb.seed("feedback", "fb-legacy", {
            "feedback_id": "fb-legacy", "uuid": UUID_OTHER, "content": "attacker-linked-feedback",
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == UUID_OTHER
        doc = rdb.docs("feedback")["fb-legacy"]
        assert doc["uuid"] is None and doc["claimed_uuid_unverified"] == UUID_OTHER
        assert doc["attribution"] == "detached_on_verification"

    def test_verified_bearer_feedback_is_not_detached(self, rdb):
        # pin: only unverified links are detached.
        rdb.seed("early_adopters", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "active", "email_verified": False,
        })
        rdb.seed("feedback", "fb-verified", {
            "feedback_id": "fb-verified", "uuid": UUID_OTHER, "attribution": "verified_bearer",
        })
        endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert rdb.docs("feedback")["fb-verified"]["uuid"] == UUID_OTHER

    def test_already_verified_subject_is_adopted_unchanged(self, rdb):
        # pin: a verified record IS the subject; nothing is rewritten.
        rdb.seed("ea_registrations", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "active",
            "email_verified": True, "updates_consent": True, "display_name": "Owner",
        })
        before = dict(rdb.docs("ea_registrations")[UUID_OTHER])
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) == UUID_OTHER
        assert rdb.docs("ea_registrations")[UUID_OTHER] == before  # the WHOLE record

    def test_deletion_requested_record_is_never_adopted(self, rdb):
        # pin: revocation stays revoked.
        rdb.seed("ea_registrations", UUID_OTHER, {
            "uuid": UUID_OTHER, "email": VICTIM_EMAIL, "status": "deletion_requested",
            "email_verified": False,
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None


# ── contract 3 · feedback attribution comes only from a validated bearer ────

class TestFeedbackAttribution:
    def test_anonymous_feedback_cannot_claim_a_victim_uuid(self, rdb, http):
        # 2c43cd5: the body uuid was stored in the authoritative field
        # (T probe: anonymous_claimed_uuid_persisted: True).
        response = _feedback_post(http, uuid=UUID_OTHER)
        assert response.status_code == 201
        (doc,) = rdb.docs("feedback").values()
        assert doc["uuid"] is None and doc["attribution"] == "anonymous"
        assert doc["claimed_uuid_unverified"] == UUID_OTHER

    def test_bearer_subject_is_the_only_attribution(self, rdb, http):
        # 2c43cd5: no bearer was consulted; the mismatched body uuid won.
        access, _refresh = _issue_access(rdb)
        subject = stores.validate_bearer(access).subject_uuid
        response = _feedback_post(http, headers={"Authorization": f"Bearer {access}"}, uuid=UUID_OTHER)
        assert response.status_code == 201
        (doc,) = rdb.docs("feedback").values()
        assert doc["uuid"] == subject and doc["attribution"] == "verified_bearer"
        assert doc["claimed_uuid_unverified"] == UUID_OTHER  # kept only as a claim

    def test_present_but_invalid_bearer_is_refused_and_nothing_stored(self, rdb, http):
        # 2c43cd5: 201, stored as if anonymous with the body uuid.
        response = _feedback_post(http, headers={"Authorization": "Bearer vmat.not.real"}, uuid=UUID_OTHER)
        assert response.status_code == 401
        assert rdb.docs("feedback") == {}

    def test_credential_store_outage_is_retryable_and_nothing_stored(self, rdb, http):
        # 2c43cd5: 201, stored as anonymous with the body uuid.
        with patch("verifimind_mcp.oauth.authlib_server.authenticate_bearer",
                   side_effect=StoreUnavailable("down")):
            response = _feedback_post(http, headers={"Authorization": "Bearer vmat.any.thing"}, uuid=UUID_OTHER)
        assert response.status_code == 503
        # WHICH 503: the credential-store outage contract, not the
        # environment-misconfiguration handler (Lens B, M44).
        assert response.json()["error"] == "temporarily_unavailable"
        assert response.headers.get("retry-after") == "60"
        assert response.headers.get("cache-control") == "no-store"
        assert rdb.docs("feedback") == {}

    def test_anonymous_feedback_without_a_claim_stays_admitted(self, rdb, http):
        # pin: public feedback is a product decision, not this repair's.
        response = _feedback_post(http)
        assert response.status_code == 201
        (doc,) = rdb.docs("feedback").values()
        assert doc["uuid"] is None and doc.get("claimed_uuid_unverified") is None


# ── contract 4 · neither email lane is an existence oracle ──────────────────

class TestEmailLanesAreNotOracles:
    @staticmethod
    def _same_modulo_clock(first, second, second_now):
        """Byte-equal bodies and headers, allowing only the request clock to
        differ — and the SECOND receipt must carry the CURRENT time: a
        duplicate that echoed the stored registration time would itself be
        an existence oracle (Lens B, M42)."""
        assert first.status_code == second.status_code
        assert first.headers.get("content-type") == second.headers.get("content-type")
        assert first.headers.get("content-length") == second.headers.get("content-length")
        body_first, body_second = first.json(), second.json()
        assert body_second["registered_at"] == second_now
        assert body_first["registered_at"] != second_now
        body_first.pop("registered_at")
        body_second.pop("registered_at")
        assert body_first == body_second

    def test_ea_lane_new_and_existing_are_byte_equal(self, rdb, http, monkeypatch):
        # 2c43cd5: duplicate said "If an account already exists…" with
        # feedback_received=False; new said "Thanks — your interest is
        # recorded…" with feedback_received=True (T probe: ea_messages_equal: False).
        payload = {"email": VICTIM_EMAIL, "tc_accepted": True, "privacy_acknowledged": True,
                   "feedback": FEEDBACK_TEXT, "feedback_type": "general"}
        first = http.post("/early-adopters/register", json=payload)   # new
        monkeypatch.setattr(registration, "_now_iso", lambda: CEREMONY_NOW)  # the clock moves on
        second = http.post("/early-adopters/register", json=payload)  # existing
        assert first.status_code == 201
        self._same_modulo_clock(first, second, CEREMONY_NOW)
        assert first.json()["feedback_received"] is True
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1
        assert len(rdb.docs("email_owners")) == 1
        # Both submissions' feedback is kept, both explicitly unverified.
        assert {doc["attribution"] for doc in rdb.docs("feedback").values()} == {"registration_unverified"}
        assert len(rdb.docs("feedback")) == 2

    def test_lightweight_lane_new_and_existing_are_byte_equal(self, rdb, http, monkeypatch):
        # 2c43cd5: duplicate said "If an account already exists…", new said
        # "Thanks — your interest is recorded…" (T probe: lightweight_messages_equal: False).
        payload = {"consent": True, "email": VICTIM_EMAIL}
        first = http.post("/register", json=payload)   # new
        monkeypatch.setattr(registration, "_now_iso", lambda: CEREMONY_NOW)
        second = http.post("/register", json=payload)  # existing
        assert first.status_code == 200
        self._same_modulo_clock(first, second, CEREMONY_NOW)
        assert first.json()["uuid"] == "" and first.json()["persisted"] is True
        assert len(_accounts(rdb, VICTIM_EMAIL)) == 1
        assert len(rdb.docs("email_owners")) == 1

    def test_anonymous_lightweight_registration_still_returns_its_uuid(self, rdb, http):
        # pin: no email → no oracle surface → the UUID is the user's only handle.
        response = http.post("/register", json={"consent": True})
        assert response.status_code == 200 and response.json()["uuid"]


# ── contract 5 · owner routes tell outage from invalid credential ───────────

class TestOwnerRouteOutageTruth:
    def test_dashboard_outage_is_503_without_reading_history(self, rdb, http):
        # 2c43cd5: 401 "unauthorized" (T probe: owner_dashboard_auth_outage_status: 401).
        with patch("verifimind_mcp.oauth.authlib_server.authenticate_bearer",
                   side_effect=StoreUnavailable("down")), \
                patch("http_server.read_trinity_history") as history:
            response = http.get(f"/early-adopters/dashboard/{UUID_OTHER}",
                                headers={"Authorization": "Bearer vmat.any.thing"})
        assert response.status_code == 503
        # WHICH 503: the owner-route outage page — names the credential
        # store, says nothing was read (Lens B, M44).
        assert "credential store" in response.text and "Nothing was read" in response.text
        assert response.headers.get("retry-after") == "60"
        assert response.headers.get("cache-control") == "no-store"
        assert not history.called

    def test_optout_outage_is_503_without_deletion(self, rdb, http):
        # 2c43cd5: 401 (T probe: owner_optout_auth_outage_status: 401).
        with patch("verifimind_mcp.oauth.authlib_server.authenticate_bearer",
                   side_effect=StoreUnavailable("down")), \
                patch("http_server.process_optout") as optout:
            response = http.post(f"/early-adopters/optout/{UUID_OTHER}",
                                 headers={"Authorization": "Bearer vmat.any.thing"})
        assert response.status_code == 503
        assert response.json()["processed"] is False
        assert "No deletion action is confirmed" in response.json()["message"]
        assert response.headers.get("retry-after") == "60"
        assert response.headers.get("cache-control") == "no-store"
        assert not optout.called

    def test_missing_invalid_and_wrong_subject_credentials_stay_401(self, rdb, http):
        # pin: T contract 5 — only an OUTAGE is a 503.
        dashboard = f"/early-adopters/dashboard/{UUID_OTHER}"
        optout = f"/early-adopters/optout/{UUID_OTHER}"
        assert http.get(dashboard).status_code == 401
        assert http.get(dashboard, headers={"Authorization": "Bearer vmat.not.real"}).status_code == 401
        access, _refresh = _issue_access(rdb)  # a real subject that is NOT UUID_OTHER
        assert http.get(dashboard, headers={"Authorization": f"Bearer {access}"}).status_code == 401
        assert http.post(optout).status_code == 401
        assert http.post(optout, headers={"Authorization": "Bearer vmat.not.real"}).status_code == 401
        assert http.post(optout, headers={"Authorization": f"Bearer {access}"}).status_code == 401

    def test_programming_errors_are_not_reported_as_invalid_credentials(self, rdb):
        # 2c43cd5: a broad except turned ANY exception from bearer
        # authentication into "your credential is invalid" (401).
        import http_server

        request = types.SimpleNamespace(headers={"authorization": "Bearer vmat.any.thing"})
        with patch("verifimind_mcp.oauth.authlib_server.authenticate_bearer",
                   side_effect=RuntimeError("programming error")):
            with pytest.raises(RuntimeError):
                http_server._bearer_subject(request)


# ── lens follow-ups (S161 Lens A): the claim's lifecycle and cohort privilege ─

class TestOwnershipLifecycle:
    """The claim must not outlive the identity it named; a revoked identity
    is never adopted, healed, or re-issued; a lane write can never clobber a
    record the ceremony verified; corrupt claims fail closed."""

    @staticmethod
    def _register_and_verify(rdb):
        asyncio.run(registration.register_early_adopter(_ea()))
        subject = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert subject
        assert rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]["uuid"] == subject
        return subject

    def test_optout_releases_the_mailbox_for_a_fresh_registration(self, rdb):
        # 2c43cd5: no claim concept (the helper's claim assertion has nothing
        # to find). On the repaired tree this guards the primitive's lifecycle:
        # opt-out de-identifies the record, tombstones the subject, AND
        # releases the ownership claim — the address can be registered again
        # by a fresh identity, and no email hash lingers after erasure.
        subject = self._register_and_verify(rdb)
        assert asyncio.run(registration.process_optout(subject)).processed is True
        assert _owner_key(VICTIM_EMAIL) not in rdb.docs("email_owners")
        later = asyncio.run(registration.register_user(_light()))
        assert later.uuid == "" and later.persisted is True
        fresh = [doc for _, _, doc in _accounts(rdb, VICTIM_EMAIL)]
        assert len(fresh) == 1 and fresh[0]["uuid"] != subject
        assert rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]["uuid"] == fresh[0]["uuid"]

    def test_purged_account_is_never_resurrected_under_a_revoked_subject(self, rdb):
        # 2c43cd5: no claim concept, so a stale claim was neither honoured nor
        # re-pointed. Here the claim was NOT released (the failure Lens A
        # named) and the record was purged: the returning owner must get a
        # FRESH subject — never the revoked identifier, whose tokens every
        # bearer validation refuses — and the stale claim must be replaced.
        subject = self._register_and_verify(rdb)
        asyncio.run(registration.process_optout(subject))
        rdb._collection_store("early_adopters")._remove(subject)  # the promised purge
        rdb.seed("email_owners", _owner_key(VICTIM_EMAIL), {
            "uuid": subject, "collection": "early_adopters", "verified": True,
        })
        fresh = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        assert fresh and fresh != subject
        assert not stores._is_tombstoned(grant_id="", parent_grant_id="", subject_uuid=fresh)
        assert subject not in rdb.docs("early_adopters")  # not resurrected
        assert rdb.docs("email_owners")[_owner_key(VICTIM_EMAIL)]["uuid"] == fresh

    def test_lane_write_never_clobbers_a_record_the_ceremony_healed(self, rdb, monkeypatch):
        # 2c43cd5: no claim primitive — and the lane's record write was an
        # unconditional set() that would replace a verified record written in
        # the same window with the unverified preregistration.
        original = registration.claim_email

        def claim_then_heal(db, owners, email, **kw):
            won = original(db, owners, email, **kw)
            if won:  # the ceremony heals the claimed identifier before the lane's record write
                db.collection("early_adopters").document(kw["uuid"]).set(
                    registration._verified_record(kw["uuid"], email, CEREMONY_NOW)
                )
            return won

        monkeypatch.setattr(registration, "claim_email", claim_then_heal)
        result = asyncio.run(registration.register_early_adopter(_ea(name="Mallory", updates_consent=True)))
        assert result.uuid == ""
        ((_, _uuid, record),) = _accounts(rdb, VICTIM_EMAIL)
        assert record["email_verified"] is True and record["updates_consent"] is False
        assert record.get("name") is None

    def test_registered_at_is_the_verified_actors_moment(self, rdb, monkeypatch):
        # 2c43cd5: the attacker's preregistration timestamp survived as the
        # account's registration time (surfaced by /whoami and status).
        asyncio.run(registration.register_early_adopter(_ea()))
        monkeypatch.setattr(registration, "_now_iso", lambda: CEREMONY_NOW)
        subject = endpoints._resolve_or_create_subject(VICTIM_EMAIL)
        record = rdb.docs("early_adopters")[subject]
        assert record["registered_at"] == CEREMONY_NOW
        assert record["preregistration"]["created_at"] == REGISTRATION_NOW

    def test_corrupt_claim_fails_closed(self, rdb):
        # 2c43cd5: no claim concept (a fresh subject was minted regardless);
        # the primitive must never guess a collection or heal an empty id.
        rdb.seed("email_owners", _owner_key(VICTIM_EMAIL), {
            "uuid": UUID_OTHER, "collection": "bogus", "verified": False,
        })
        assert endpoints._resolve_or_create_subject(VICTIM_EMAIL) is None
        assert _accounts(rdb, VICTIM_EMAIL) == []
        rdb.seed("email_owners", _owner_key("empty@example.com"), {
            "uuid": "", "collection": "ea_registrations", "verified": False,
        })
        assert endpoints._resolve_or_create_subject("empty@example.com") is None


class TestCohortPrivilegeRequiresVerification:
    def test_unverified_preregistration_earns_no_cohort_tier(self, rdb):
        # 2c43cd5: any early_adopters document — including an unproven
        # preregistration planted with someone else's address — was granted
        # the pioneer bucket.
        rdb.seed("early_adopters", UUID_OTHER, {"uuid": UUID_OTHER, "status": "active", "email_verified": False})
        assert rate_limiter._resolve_uuid_tier(UUID_OTHER) == "scholar"

    def test_verified_and_legacy_cohort_members_keep_pioneer(self, rdb):
        # pin: a verified record, and a legacy record written before the flag
        # existed, keep their standing.
        rdb.seed("early_adopters", UUID_OTHER, {"uuid": UUID_OTHER, "status": "active", "email_verified": True})
        assert rate_limiter._resolve_uuid_tier(UUID_OTHER) == "pioneer"
        rate_limiter._uuid_tier_cache.clear()
        legacy = "018f6b2a-eeee-7abc-8def-0123456789ab"
        rdb.seed("early_adopters", legacy, {"uuid": legacy, "status": "active"})
        assert rate_limiter._resolve_uuid_tier(legacy) == "pioneer"
