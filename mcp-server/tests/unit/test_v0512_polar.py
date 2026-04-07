"""
v0.5.12 Polar Integration — Unit Tests
=======================================

Tests for:
1. PolarClient  — base URL selection, has_pioneer_access logic, API call (mocked)
2. PolarAdapter — cache hit/miss/TTL, 404 handling, update_cache, invalidate, stats
3. get_polar_adapter / reset_polar_adapter — singleton lifecycle
4. PolarWebhookHandler — verify delegation, handle routing, _check_pioneer_benefit
5. _handle_customer_state_changed — missing external_id, with/without adapter
6. Docstring regression — Stripe references removed from tier_gate.py
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

TEST_UUID = "abc12345-0000-0000-0000-000000000001"
TEST_TOKEN = "polar_oat_testtoken"
TEST_SECRET = "whsec_testsecret"


def _make_state(granted: bool = True, benefit_type: str = "feature", tier: str = "pioneer") -> dict:
    """Build a minimal Polar customer state dict."""
    return {
        "benefit_grants": [
            {
                "granted": granted,
                "benefit": {"type": benefit_type},
                "properties": {"metadata": {"tier": tier}},
            }
        ]
    }


def _make_polar_client(has_access: bool = True, status_code: int = 200):
    """Build a mock PolarClient."""
    client = MagicMock()
    client.environment = "sandbox"
    if status_code == 200:
        client.get_customer_state = AsyncMock(return_value=_make_state(granted=has_access))
        client.has_pioneer_access = MagicMock(return_value=has_access)
    else:
        import httpx
        resp = MagicMock()
        resp.status_code = status_code
        client.get_customer_state = AsyncMock(
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=resp)
        )
    return client


# ===========================================================================
# 1. PolarClient
# ===========================================================================

class TestPolarClientBaseURL:
    """PolarClient selects sandbox vs production base URL correctly."""

    def test_production_base_url(self, monkeypatch):
        monkeypatch.delenv("POLAR_ENVIRONMENT", raising=False)
        from verifimind_mcp.integrations.polar_client import PolarClient, _PRODUCTION_BASE
        c = PolarClient(access_token=TEST_TOKEN, environment="production")
        assert c.base_url == _PRODUCTION_BASE

    def test_sandbox_base_url_from_argument(self, monkeypatch):
        monkeypatch.delenv("POLAR_ENVIRONMENT", raising=False)
        from verifimind_mcp.integrations.polar_client import PolarClient, _SANDBOX_BASE
        c = PolarClient(access_token=TEST_TOKEN, environment="sandbox")
        assert c.base_url == _SANDBOX_BASE

    def test_env_var_overrides_argument(self, monkeypatch):
        monkeypatch.setenv("POLAR_ENVIRONMENT", "sandbox")
        from verifimind_mcp.integrations.polar_client import PolarClient, _SANDBOX_BASE
        c = PolarClient(access_token=TEST_TOKEN, environment="production")
        assert c.base_url == _SANDBOX_BASE

    def test_environment_property(self, monkeypatch):
        monkeypatch.delenv("POLAR_ENVIRONMENT", raising=False)
        from verifimind_mcp.integrations.polar_client import PolarClient
        c = PolarClient(access_token=TEST_TOKEN, environment="sandbox")
        assert c.environment == "sandbox"


class TestPolarClientHasPioneerAccess:
    """has_pioneer_access correctly inspects benefit_grants."""

    def _client(self):
        from verifimind_mcp.integrations.polar_client import PolarClient
        return PolarClient(access_token=TEST_TOKEN, environment="sandbox")

    def test_returns_true_when_granted(self):
        assert self._client().has_pioneer_access(_make_state(granted=True)) is True

    def test_returns_false_when_not_granted(self):
        assert self._client().has_pioneer_access(_make_state(granted=False)) is False

    def test_returns_false_wrong_benefit_type(self):
        assert self._client().has_pioneer_access(_make_state(benefit_type="custom")) is False

    def test_returns_false_wrong_tier_metadata(self):
        assert self._client().has_pioneer_access(_make_state(tier="scholar")) is False

    def test_returns_false_empty_state(self):
        assert self._client().has_pioneer_access({}) is False

    def test_returns_false_empty_grants(self):
        assert self._client().has_pioneer_access({"benefit_grants": []}) is False


class TestPolarClientAPICall:
    """get_customer_state makes the right HTTP request (mocked httpx)."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, monkeypatch):
        monkeypatch.delenv("POLAR_ENVIRONMENT", raising=False)
        from verifimind_mcp.integrations.polar_client import PolarClient

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"benefit_grants": []}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            c = PolarClient(access_token=TEST_TOKEN, environment="sandbox")
            result = await c.get_customer_state(TEST_UUID)

        mock_client.get.assert_called_once()
        call_url = mock_client.get.call_args[0][0]
        assert TEST_UUID in call_url
        assert "customers/external" in call_url
        assert result == {"benefit_grants": []}


# ===========================================================================
# 2. PolarAdapter
# ===========================================================================

class TestPolarAdapterCacheHit:
    """Adapter returns cached result without calling Polar API."""

    @pytest.mark.asyncio
    async def test_cache_hit_no_api_call(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        client = _make_polar_client(has_access=True)
        adapter = PolarAdapter(client, cache_ttl=300)

        # Prime cache
        result1 = await adapter.check_pioneer_access(TEST_UUID)
        assert result1 is True
        assert client.get_customer_state.call_count == 1

        # Second call — cache hit
        result2 = await adapter.check_pioneer_access(TEST_UUID)
        assert result2 is True
        assert client.get_customer_state.call_count == 1  # no new API call

    @pytest.mark.asyncio
    async def test_cache_miss_after_ttl(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        client = _make_polar_client(has_access=True)
        adapter = PolarAdapter(client, cache_ttl=0)  # TTL=0 → always expired

        await adapter.check_pioneer_access(TEST_UUID)
        await adapter.check_pioneer_access(TEST_UUID)
        assert client.get_customer_state.call_count == 2


class TestPolarAdapterAccessCheck:
    """Adapter correctly maps API responses to access decisions."""

    @pytest.mark.asyncio
    async def test_pioneer_granted(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(_make_polar_client(has_access=True), cache_ttl=300)
        assert await adapter.check_pioneer_access(TEST_UUID) is True

    @pytest.mark.asyncio
    async def test_scholar_returned(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(_make_polar_client(has_access=False), cache_ttl=300)
        assert await adapter.check_pioneer_access(TEST_UUID) is False

    @pytest.mark.asyncio
    async def test_404_returns_false(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(_make_polar_client(status_code=404), cache_ttl=300)
        result = await adapter.check_pioneer_access(TEST_UUID)
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_uuid_returns_false(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(_make_polar_client(), cache_ttl=300)
        assert await adapter.check_pioneer_access("") is False
        assert await adapter.check_pioneer_access("   ") is False

    @pytest.mark.asyncio
    async def test_non_404_http_error_propagates(self):
        import httpx
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(_make_polar_client(status_code=500), cache_ttl=300)
        with pytest.raises(httpx.HTTPStatusError):
            await adapter.check_pioneer_access(TEST_UUID)


class TestPolarAdapterCacheManagement:
    """update_cache, invalidate_cache, and get_cache_stats work correctly."""

    def test_update_cache_grants_access(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(MagicMock(), cache_ttl=300)
        adapter.update_cache(TEST_UUID, True)
        assert TEST_UUID in adapter._cache
        assert adapter._cache[TEST_UUID][0] is True

    def test_update_cache_revokes_access(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(MagicMock(), cache_ttl=300)
        adapter.update_cache(TEST_UUID, True)
        adapter.update_cache(TEST_UUID, False)
        assert adapter._cache[TEST_UUID][0] is False

    def test_invalidate_removes_entry(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(MagicMock(), cache_ttl=300)
        adapter.update_cache(TEST_UUID, True)
        adapter.invalidate_cache(TEST_UUID)
        assert TEST_UUID not in adapter._cache

    def test_invalidate_noop_on_unknown_uuid(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(MagicMock(), cache_ttl=300)
        adapter.invalidate_cache("nonexistent-uuid")  # should not raise

    def test_cache_stats_structure(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(MagicMock(), cache_ttl=300)
        adapter.update_cache(TEST_UUID, True)
        stats = adapter.get_cache_stats()
        assert stats["total_cached"] == 1
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 0
        assert stats["cache_ttl_seconds"] == 300

    def test_cache_stats_counts_expired(self):
        from verifimind_mcp.middleware.polar_adapter import PolarAdapter
        adapter = PolarAdapter(MagicMock(), cache_ttl=300)
        # Manually insert an expired entry
        adapter._cache[TEST_UUID] = (True, time.time() - 400)
        stats = adapter.get_cache_stats()
        assert stats["expired_entries"] == 1
        assert stats["active_entries"] == 0


# ===========================================================================
# 3. Singleton lifecycle
# ===========================================================================

class TestGetPolarAdapterSingleton:
    """get_polar_adapter() returns None without token, creates singleton with token."""

    def test_returns_none_without_token(self, monkeypatch):
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        from verifimind_mcp.middleware import polar_adapter as pa
        pa.reset_polar_adapter()
        assert pa.get_polar_adapter() is None

    def test_creates_adapter_with_token(self, monkeypatch):
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", TEST_TOKEN)
        monkeypatch.setenv("POLAR_ENVIRONMENT", "sandbox")
        from verifimind_mcp.middleware import polar_adapter as pa
        pa.reset_polar_adapter()
        adapter = pa.get_polar_adapter()
        assert adapter is not None
        assert isinstance(adapter, pa.PolarAdapter)

    def test_returns_same_singleton(self, monkeypatch):
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", TEST_TOKEN)
        monkeypatch.setenv("POLAR_ENVIRONMENT", "sandbox")
        from verifimind_mcp.middleware import polar_adapter as pa
        pa.reset_polar_adapter()
        a1 = pa.get_polar_adapter()
        a2 = pa.get_polar_adapter()
        assert a1 is a2

    def test_reset_clears_singleton(self, monkeypatch):
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", TEST_TOKEN)
        monkeypatch.setenv("POLAR_ENVIRONMENT", "sandbox")
        from verifimind_mcp.middleware import polar_adapter as pa
        pa.reset_polar_adapter()
        a1 = pa.get_polar_adapter()
        pa.reset_polar_adapter()
        # After reset, module-level _adapter is None
        assert pa._adapter is None


# ===========================================================================
# 4. PolarWebhookHandler
# ===========================================================================

def _make_webhook_handler(adapter=None):
    """Build a PolarWebhookHandler with a mocked standardwebhooks.Webhook."""
    mock_wh = MagicMock()
    with patch("standardwebhooks.Webhook", return_value=mock_wh):
        from verifimind_mcp.webhooks.polar_webhook import PolarWebhookHandler
        handler = PolarWebhookHandler(TEST_SECRET, adapter=adapter)
    handler._wh = mock_wh
    return handler


class TestPolarWebhookHandlerVerify:
    """verify() delegates to standardwebhooks.Webhook.verify."""

    def test_verify_calls_wh_verify(self):
        handler = _make_webhook_handler()
        handler._wh.verify = MagicMock(return_value={"type": "subscription.active"})
        result = handler.verify(b'{"type":"subscription.active"}', {})
        handler._wh.verify.assert_called_once()
        assert result["type"] == "subscription.active"

    def test_import_error_without_standardwebhooks(self, monkeypatch):
        import sys
        original = sys.modules.get("standardwebhooks")
        sys.modules["standardwebhooks"] = None  # type: ignore[assignment]
        try:
            import importlib
            from verifimind_mcp.webhooks import polar_webhook
            importlib.reload(polar_webhook)
            with pytest.raises((ImportError, TypeError)):
                polar_webhook.PolarWebhookHandler(TEST_SECRET)
        finally:
            if original is None:
                sys.modules.pop("standardwebhooks", None)
            else:
                sys.modules["standardwebhooks"] = original


class TestPolarWebhookHandlerHandle:
    """handle() routes the 6 Polar subscription events correctly."""

    @pytest.mark.asyncio
    async def test_grant_event_processed(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(return_value={
            "type": "subscription.active",
            "data": {"customer": {"external_id": TEST_UUID}},
        })
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is True
        mock_adapter.update_cache.assert_called_once_with(TEST_UUID, True)

    @pytest.mark.asyncio
    async def test_revoke_event_processed(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(return_value={
            "type": "subscription.revoked",
            "data": {"customer": {"external_id": TEST_UUID}},
        })
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is False
        mock_adapter.update_cache.assert_called_once_with(TEST_UUID, False)

    @pytest.mark.asyncio
    async def test_missing_external_id_skipped(self):
        handler = _make_webhook_handler()
        handler._wh.verify = MagicMock(return_value={
            "type": "subscription.active",
            "data": {"customer": {}},
        })
        result = await handler.handle(b"{}", {})
        assert result["status"] == "skipped"
        assert "external_id" in result["reason"]

    @pytest.mark.asyncio
    async def test_no_adapter_action_logged(self):
        handler = _make_webhook_handler(adapter=None)
        handler._wh.verify = MagicMock(return_value={
            "type": "subscription.active",
            "data": {"customer": {"external_id": TEST_UUID}},
        })
        # Patch _update_adapter_cache to return "no_adapter" directly
        handler._update_adapter_cache = AsyncMock(return_value="no_adapter")
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["action"] == "no_adapter"


class TestExtractExternalId:
    """_extract_external_id pulls UUID from subscription event data."""

    def test_extracts_from_customer_field(self):
        handler = _make_webhook_handler()
        event = {"data": {"customer": {"external_id": TEST_UUID}}}
        assert handler._extract_external_id(event) == TEST_UUID

    def test_returns_none_when_missing(self):
        handler = _make_webhook_handler()
        assert handler._extract_external_id({"data": {"customer": {}}}) is None
        assert handler._extract_external_id({"data": {}}) is None
        assert handler._extract_external_id({}) is None


# ===========================================================================
# 5. Subscription event handlers (T's 6 configured events)
# ===========================================================================

def _make_subscription_event(event_type: str, external_id: str = TEST_UUID, status: str = "") -> dict:
    """Build a minimal Polar subscription event dict."""
    data = {
        "customer": {"external_id": external_id},
        "status": status,
    }
    return {"type": event_type, "data": data}


class TestSubscriptionEvents:
    """PolarWebhookHandler correctly maps T's 6 configured Polar events."""

    @pytest.mark.asyncio
    async def test_subscription_active_grants_access(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(
            return_value=_make_subscription_event("subscription.active")
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is True
        mock_adapter.update_cache.assert_called_once_with(TEST_UUID, True)

    @pytest.mark.asyncio
    async def test_subscription_revoked_denies_access(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(
            return_value=_make_subscription_event("subscription.revoked")
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is False
        mock_adapter.update_cache.assert_called_once_with(TEST_UUID, False)

    @pytest.mark.asyncio
    async def test_subscription_canceled_denies_access(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(
            return_value=_make_subscription_event("subscription.canceled")
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is False

    @pytest.mark.asyncio
    async def test_subscription_created_no_access(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(
            return_value=_make_subscription_event("subscription.created", status="incomplete")
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is False

    @pytest.mark.asyncio
    async def test_subscription_updated_active_grants(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(
            return_value=_make_subscription_event("subscription.updated", status="active")
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is True

    @pytest.mark.asyncio
    async def test_subscription_updated_inactive_denies(self):
        mock_adapter = MagicMock()
        mock_adapter.update_cache = MagicMock()
        handler = _make_webhook_handler(adapter=mock_adapter)
        handler._wh.verify = MagicMock(
            return_value=_make_subscription_event("subscription.updated", status="past_due")
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "processed"
        assert result["pioneer_access"] is False

    @pytest.mark.asyncio
    async def test_order_created_ignored(self):
        handler = _make_webhook_handler()
        handler._wh.verify = MagicMock(
            return_value={"type": "order.created", "data": {}}
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "ignored"
        assert result["event_type"] == "order.created"

    @pytest.mark.asyncio
    async def test_missing_external_id_skipped(self):
        handler = _make_webhook_handler()
        handler._wh.verify = MagicMock(
            return_value={"type": "subscription.active", "data": {"customer": {}}}
        )
        result = await handler.handle(b"{}", {})
        assert result["status"] == "skipped"
        assert "external_id" in result["reason"]


# ===========================================================================
# 6. Docstring regression — Stripe removed from tier_gate.py
# ===========================================================================

class TestStripeDocstringRemoved:
    """Confirm tier_gate.py no longer references Stripe (T's note, Issue #46)."""

    def test_no_stripe_in_tier_gate(self):
        import inspect
        from verifimind_mcp.middleware import tier_gate
        source = inspect.getsource(tier_gate)
        assert "Stripe" not in source, (
            "tier_gate.py still references 'Stripe' — update to 'Polar' per T review note"
        )

# ===========================================================================
# 7. Version regression — server.py must be v0.5.12
# ===========================================================================

class TestServerVersion:
    def test_server_version_is_0512(self):
        from verifimind_mcp.server import SERVER_VERSION
        assert SERVER_VERSION == "0.5.12"
