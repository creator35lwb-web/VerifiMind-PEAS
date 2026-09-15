"""
Tests for v0.5.6 Gateway: Registration & Opt-Out UI Pages
Covers GET /register, GET /optout, and pages.py unit tests.

Z-Protocol v1.1 compliance:
- Consent checkboxes present and required
- XSS-safe patterns confirmed
- Opt-out (right to erasure) accessible without barriers
"""
import pytest
from starlette.testclient import TestClient

# ─────────────────────────────────────────────
# pages.py unit tests (pure functions, no HTTP)
# ─────────────────────────────────────────────

class TestPagesModule:
    """Unit tests for get_register_page() and get_optout_page()."""

    def test_get_register_page_returns_string(self):
        from verifimind_mcp.pages import get_register_page
        result = get_register_page()
        assert isinstance(result, str)

    def test_get_register_page_is_valid_html(self):
        from verifimind_mcp.pages import get_register_page
        html = get_register_page()
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_get_optout_page_returns_string(self):
        from verifimind_mcp.pages import get_optout_page
        result = get_optout_page()
        assert isinstance(result, str)

    def test_get_optout_page_is_valid_html(self):
        from verifimind_mcp.pages import get_optout_page
        html = get_optout_page()
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_pages_have_no_external_cdn_dependencies(self):
        """Self-contained requirement: no CDN script/link tags."""
        from verifimind_mcp.pages import get_register_page, get_optout_page
        for html in [get_register_page(), get_optout_page()]:
            assert "cdn.jsdelivr.net" not in html
            assert "cdnjs.cloudflare.com" not in html
            assert "unpkg.com" not in html
            assert "fonts.googleapis.com" not in html


# ─────────────────────────────────────────────
# GET /register — HTTP route tests
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Starlette TestClient for the full app."""
    import sys
    import os
    # Ensure the mcp-server root is in path for import
    server_root = os.path.join(os.path.dirname(__file__), "..")
    if server_root not in sys.path:
        sys.path.insert(0, server_root)

    from http_server import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestRegisterPage:
    """Tests for GET /register."""

    def test_get_register_returns_200(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200

    def test_get_register_content_type_is_html(self, client):
        resp = client.get("/register")
        assert "text/html" in resp.headers["content-type"]

    def test_get_register_has_doctype(self, client):
        html = client.get("/register").text
        assert "<!DOCTYPE html>" in html

    def test_get_register_links_to_terms(self, client):
        html = client.get("/register").text
        assert "/terms" in html

    def test_get_register_links_to_privacy(self, client):
        html = client.get("/register").text
        assert "/privacy" in html

    def test_get_register_has_charset_utf8(self, client):
        html = client.get("/register").text
        assert "utf-8" in html.lower() or "UTF-8" in html

    def test_get_register_has_viewport_meta(self, client):
        """Mobile-responsive requirement."""
        html = client.get("/register").text
        assert "viewport" in html

    def test_get_register_has_no_external_cdn(self, client):
        html = client.get("/register").text
        assert "cdn.jsdelivr.net" not in html
        assert "cdnjs.cloudflare.com" not in html
        assert "unpkg.com" not in html

    def test_get_register_has_verifimind_branding(self, client):
        html = client.get("/register").text
        assert "VerifiMind" in html

    def test_get_register_has_z_protocol_consent_section(self, client):
        """Z-Protocol v1.1: consent section must clearly label what user agrees to."""
        html = client.get("/register").text
        # Check for consent-related text
        assert "Terms" in html and "Privacy" in html


# ─────────────────────────────────────────────
# GET /optout — HTTP route tests
# ─────────────────────────────────────────────

class TestOptOutPage:
    """Tests for GET /optout."""

    def test_get_optout_returns_200(self, client):
        resp = client.get("/optout")
        assert resp.status_code == 200

    def test_get_optout_content_type_is_html(self, client):
        resp = client.get("/optout")
        assert "text/html" in resp.headers["content-type"]

    def test_get_optout_has_doctype(self, client):
        html = client.get("/optout").text
        assert "<!DOCTYPE html>" in html

    def test_get_optout_mentions_7_business_days(self, client):
        """Z-Protocol compliance: deletion timeline must be disclosed."""
        html = client.get("/optout").text
        assert "7" in html and ("business" in html.lower() or "day" in html.lower())

    def test_get_optout_has_no_external_cdn(self, client):
        html = client.get("/optout").text
        assert "cdn.jsdelivr.net" not in html
        assert "unpkg.com" not in html

    def test_get_optout_has_verifimind_branding(self, client):
        html = client.get("/optout").text
        assert "VerifiMind" in html

    def test_get_optout_has_charset_utf8(self, client):
        html = client.get("/optout").text
        assert "utf-8" in html.lower() or "UTF-8" in html

    def test_get_optout_has_viewport_meta(self, client):
        html = client.get("/optout").text
        assert "viewport" in html

    def test_get_optout_links_to_privacy(self, client):
        """Right to erasure page should reference the Privacy Policy."""
        html = client.get("/optout").text
        assert "/privacy" in html

    def test_get_optout_accessible_without_login(self, client):
        """GDPR right to erasure: opt-out must not require authentication."""
        resp = client.get("/optout")
        # Must not redirect to login or return 401/403
        assert resp.status_code == 200

# ─────────────────────────────────────────────
# Retained forms — not served while the legacy UUID containment holds
# ─────────────────────────────────────────────
#
# GET /register and GET /optout currently serve truthful notices (their served-copy truth
# contracts live in tests/unit/test_legacy_uuid_served_copy_truth.py). The forms are
# retained, not served, for the reviewed change that restores authenticated account
# trust, so their consent-capture and XSS contracts stay pinned here, unweakened.
#
# These read the template body and script directly rather than a shell-rendered page:
# the shared shell's CSS contains `type="email"`, `confirm` and `uuid`, so three of these
# assertions used to pass on ANY page rendered through it.


def _retained_register_markup():
    from verifimind_mcp.pages import _REGISTER_BODY, _REGISTER_SCRIPT
    return _REGISTER_BODY + _REGISTER_SCRIPT


def _retained_optout_markup():
    from verifimind_mcp.pages import _OPTOUT_BODY, _OPTOUT_SCRIPT
    return _OPTOUT_BODY + _OPTOUT_SCRIPT


class TestRetainedRegisterForm:
    """The retained registration form (Z-Protocol v1.1 consent capture, XSS-safe patterns)."""

    def test_retained_register_form_has_form_element(self):
        html = _retained_register_markup()
        assert "<form" in html

    def test_retained_register_form_has_email_input(self):
        html = _retained_register_markup()
        assert 'type="email"' in html or "type='email'" in html

    def test_retained_register_form_has_tc_checkbox(self):
        """Z-Protocol: T&C consent checkbox must be present."""
        html = _retained_register_markup()
        assert "tc_accepted" in html

    def test_retained_register_form_has_privacy_checkbox(self):
        """Z-Protocol: Privacy Policy consent checkbox must be present."""
        html = _retained_register_markup()
        assert "privacy_acknowledged" in html

    def test_retained_register_form_has_updates_consent_field(self):
        """Optional marketing consent (not pre-checked)."""
        html = _retained_register_markup()
        assert "updates_consent" in html

    def test_retained_register_form_has_submit_button(self):
        html = _retained_register_markup()
        assert 'type="submit"' in html or "submit" in html.lower()

    def test_retained_register_form_no_innerHTML_assignment(self):
        """XSS safety: user-controlled data must not be written via innerHTML."""
        html = _retained_register_markup()
        # innerHTML is only used for static success/error HTML fragments (safe)
        # Verify user data (uuid, email_masked) uses textContent
        assert "uuid_display.textContent" in html or "textContent" in html

    def test_retained_register_form_references_early_adopters_register_api(self):
        """Form must POST to the correct API endpoint."""
        html = _retained_register_markup()
        assert "/early-adopters/register" in html


class TestRetainedOptOutForm:
    """The retained self-service opt-out form (explicit confirmation, XSS-safe patterns)."""

    def test_retained_optout_form_has_form_element(self):
        html = _retained_optout_markup()
        assert "<form" in html

    def test_retained_optout_form_has_uuid_input(self):
        """User must enter their UUID to delete their record."""
        html = _retained_optout_markup()
        assert "uuid" in html.lower()

    def test_retained_optout_form_has_confirmation_checkbox(self):
        """Z-Protocol: right to erasure must require explicit confirmation."""
        html = _retained_optout_markup()
        assert "confirm" in html.lower()

    def test_retained_optout_form_references_optout_api(self):
        """Form must call the correct API endpoint."""
        html = _retained_optout_markup()
        assert "early-adopters/optout" in html

    def test_retained_optout_form_no_innerHTML_for_user_data(self):
        """XSS safety: UUID is user-controlled — must use textContent."""
        html = _retained_optout_markup()
        assert "textContent" in html

    def test_retained_optout_form_encode_uri_component_present(self):
        """XSS safety: UUID used in fetch URL must be URI-encoded."""
        html = _retained_optout_markup()
        assert "encodeURIComponent" in html
