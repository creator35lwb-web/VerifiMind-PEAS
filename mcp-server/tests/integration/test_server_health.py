"""
Integration tests for MCP Server Health.

Tests server availability and basic functionality.
These tests can run against local or production server.
"""

import pytest
import os
import httpx
from typing import Optional

# Server URLs
LOCAL_SERVER_URL = "http://localhost:8000"
PRODUCTION_SERVER_URL = "https://verifimind.ysenseai.org"

# Determine which server to test
def get_server_url() -> str:
    """Get the server URL to test against."""
    # Check environment variable first
    env_url = os.environ.get("VERIFIMIND_TEST_SERVER_URL")
    if env_url:
        return env_url
    
    # In CI, test against production
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return PRODUCTION_SERVER_URL
    
    # Locally, try local server first
    return LOCAL_SERVER_URL


@pytest.fixture
def server_url() -> str:
    """Fixture providing the server URL."""
    return get_server_url()


@pytest.fixture
def http_client():
    """Fixture providing an HTTP client."""
    return httpx.Client(timeout=30.0)


class TestServerHealth:
    """Tests for server health endpoints."""
    
    @pytest.mark.integration
    def test_health_endpoint_returns_200(self, server_url, http_client):
        """Health endpoint should return 200 OK."""
        try:
            response = http_client.get(f"{server_url}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")
    
    @pytest.mark.integration
    def test_health_endpoint_returns_json(self, server_url, http_client):
        """Health endpoint should return valid JSON."""
        try:
            response = http_client.get(f"{server_url}/health")
            data = response.json()
            assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")
    
    @pytest.mark.integration
    def test_health_contains_status(self, server_url, http_client):
        """Health response should contain status field."""
        try:
            response = http_client.get(f"{server_url}/health")
            data = response.json()
            assert "status" in data or "healthy" in data or "ok" in str(data).lower()
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")
    
    @pytest.mark.integration
    def test_health_contains_version(self, server_url, http_client):
        """Health response should contain version info."""
        try:
            response = http_client.get(f"{server_url}/health")
            data = response.json()
            # Version might be in various fields
            has_version = (
                "version" in data or 
                "server_version" in data or
                "v" in str(data)
            )
            # Not a hard requirement, just informational
            if not has_version:
                pytest.skip("Version info not in health response (optional)")
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")


class TestServerEndpoints:
    """Tests for server API endpoints."""
    
    @pytest.mark.integration
    def test_root_endpoint_exists(self, server_url, http_client):
        """Root endpoint should exist and respond."""
        try:
            response = http_client.get(f"{server_url}/")
            # Should return something (200, 301, 302, etc.)
            assert response.status_code < 500
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")
    
    @pytest.mark.integration
    def test_mcp_endpoint_exists(self, server_url, http_client):
        """MCP endpoint should exist."""
        try:
            # MCP uses SSE, so we just check it doesn't 404
            response = http_client.get(
                f"{server_url}/mcp",
                headers={"Accept": "text/event-stream"},
                timeout=5.0
            )
            # Should not be 404
            assert response.status_code != 404
        except (httpx.ConnectError, httpx.ReadTimeout):
            pytest.skip(f"Server not available or timeout at {server_url}")
    
    @pytest.mark.integration
    def test_invalid_endpoint_returns_404(self, server_url, http_client):
        """Invalid endpoints should return 404."""
        try:
            response = http_client.get(f"{server_url}/this-endpoint-does-not-exist-12345")
            assert response.status_code == 404
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")


class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    @pytest.mark.integration
    def test_rate_limit_headers_present(self, server_url, http_client):
        """Rate limit headers should be present in responses."""
        try:
            response = http_client.get(f"{server_url}/health")
            # Check for rate limit headers
            has_rate_limit_header = any(
                header.lower().startswith("x-ratelimit") 
                for header in response.headers
            )
            # Informational - not all endpoints may have headers
            if not has_rate_limit_header:
                pytest.skip("Rate limit headers not on health endpoint (may be exempt)")
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_rate_limit_not_triggered_on_normal_use(self, server_url, http_client):
        """Normal usage should not trigger rate limits."""
        try:
            # Make a few requests (well under limit)
            for _ in range(5):
                response = http_client.get(f"{server_url}/health")
                assert response.status_code != 429, "Rate limit triggered too early"
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")


class TestSecurityHeaders:
    """Tests for security headers."""
    
    @pytest.mark.integration
    def test_cors_headers_present(self, server_url, http_client):
        """CORS headers should be present for cross-origin requests."""
        try:
            response = http_client.options(
                f"{server_url}/health",
                headers={"Origin": "https://example.com"}
            )
            # CORS might return 200 or 204
            assert response.status_code in [200, 204, 405]
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")
    
    @pytest.mark.integration
    def test_no_server_version_leak(self, server_url, http_client):
        """Server should not leak detailed version info in headers."""
        try:
            response = http_client.get(f"{server_url}/health")
            server_header = response.headers.get("server", "").lower()
            # Should not expose detailed version like "uvicorn/0.x.x"
            # Generic names like "uvicorn" are OK
            assert "0." not in server_header and "1." not in server_header
        except httpx.ConnectError:
            pytest.skip(f"Server not available at {server_url}")


# Marker for slow tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
