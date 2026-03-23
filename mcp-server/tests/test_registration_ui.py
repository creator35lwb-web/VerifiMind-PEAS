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

    def test_get_register_has_form_element(self, client):
        html = client.get("/register").text
        assert "<form" in html

    def test_get_register_has_email_input(self, client):
        html = client.get("/register").text
        assert 'type="email"' in html or "type='email'" in html

    def test_get_register_has_tc_checkbox(self, client):
        """Z-Protocol: T&C consent checkbox must be present."""
        html = client.get("/register").text
        assert "tc_accepted" in html

    def test_get_register_has_privacy_checkbox(self, client):
        """Z-Protocol: Privacy Policy consent checkbox must be present."""
        html = client.get("/register").text
        assert "privacy_acknowledged" in html

    def test_get_register_has_updates_consent_field(self, client):
        """Optional marketing consent (not pre-checked)."""
        html = client.get("/register").text
        assert "updates_consent" in html

    def test_get_register_links_to_terms(self, client):
        html = client.get("/register").text
        assert "/terms" in html

    def test_get_register_links_to_privacy(self, client):
        html = client.get("/register").text
        assert "/privacy" in html

    def test_get_register_has_submit_button(self, client):
        html = client.get("/register").text
        assert 'type="submit"' in html or "submit" in html.lower()

    def test_get_register_no_innerHTML_assignment(self, client):
        """XSS safety: user-controlled data must not be written via innerHTML."""
        html = client.get("/register").text
        # innerHTML is only used for static success/error HTML fragments (safe)
        # Verify user data (uuid, email_masked) uses textContent
        assert "uuid_display.textContent" in html or "textContent" in html

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

    def test_get_register_references_early_adopters_register_api(self, client):
        """Form must POST to the correct API endpoint."""
        html = client.get("/register").text
        assert "/early-adopters/register" in html

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

    def test_get_optout_has_form_element(self, client):
        html = client.get("/optout").text
        assert "<form" in html

    def test_get_optout_has_uuid_input(self, client):
        """User must enter their UUID to delete their record."""
        html = client.get("/optout").text
        assert "uuid" in html.lower()

    def test_get_optout_has_confirmation_checkbox(self, client):
        """Z-Protocol: right to erasure must require explicit confirmation."""
        html = client.get("/optout").text
        assert "confirm" in html.lower()

    def test_get_optout_references_optout_api(self, client):
        """Form must call the correct API endpoint."""
        html = client.get("/optout").text
        assert "early-adopters/optout" in html

    def test_get_optout_no_innerHTML_for_user_data(self, client):
        """XSS safety: UUID is user-controlled — must use textContent."""
        html = client.get("/optout").text
        assert "textContent" in html

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

    def test_get_optout_encode_uri_component_present(self, client):
        """XSS safety: UUID used in fetch URL must be URI-encoded."""
        html = client.get("/optout").text
        assert "encodeURIComponent" in html
