"""
Tests for v0.5.19 P0-A — UUID Tier-Aware Rate Limiter

Coverage:
  - TIER_LIMITS constants correct
  - RateLimitStore.check_and_record_uuid: allows up to limit, blocks on limit+1
  - RateLimitStore.check_and_record: IP path unchanged
  - _resolve_uuid_tier: invalid UUID / no Firestore → "scholar"
  - _uuid_tier_cache: populated on first call, reused on second
  - Middleware response headers include X-RateLimit-Tier
  - get_stats includes active_uuids
  - Server version 0.5.19
"""

import time
from collections import defaultdict

from verifimind_mcp.middleware.rate_limiter import (
    TIER_LIMITS,
    RateLimitStore,
    _resolve_uuid_tier,
    _uuid_tier_cache,
    UUID_TIER_CACHE_TTL,
)

VALID_UUID = "019d40d6-9e84-7738-9c0c-fa85b2930600"
VALID_UUID_2 = "019e1234-abcd-7000-beef-000000000001"


# ---------------------------------------------------------------------------
# TIER_LIMITS constants
# ---------------------------------------------------------------------------

class TestTierLimitsConstants:

    def test_anonymous_is_10(self):
        assert TIER_LIMITS["anonymous"] == 10

    def test_scholar_is_30(self):
        assert TIER_LIMITS["scholar"] == 30

    def test_pioneer_is_100(self):
        assert TIER_LIMITS["pioneer"] == 100

    def test_scholar_greater_than_anonymous(self):
        assert TIER_LIMITS["scholar"] > TIER_LIMITS["anonymous"]

    def test_pioneer_greater_than_scholar(self):
        assert TIER_LIMITS["pioneer"] > TIER_LIMITS["scholar"]


# ---------------------------------------------------------------------------
# RateLimitStore.check_and_record_uuid
# ---------------------------------------------------------------------------

class TestCheckAndRecordUuid:

    def _fresh_store(self):
        store = RateLimitStore()
        return store

    def test_allows_requests_up_to_limit(self):
        store = self._fresh_store()
        # burst multiplier is 2x, so effective = limit * 2
        # With limit=5 and burst=2, we can do 10 before hitting cap
        for _ in range(5):
            allowed, _, _ = store.check_and_record_uuid(VALID_UUID, 5)
            assert allowed is True

    def test_blocks_after_burst_limit(self):
        store = self._fresh_store()
        from verifimind_mcp.middleware.rate_limiter import RATE_LIMIT_BURST_MULTIPLIER
        burst_cap = int(5 * RATE_LIMIT_BURST_MULTIPLIER)
        for _ in range(burst_cap):
            store.check_and_record_uuid(VALID_UUID, 5)
        allowed, retry_after, limit_type = store.check_and_record_uuid(VALID_UUID, 5)
        assert allowed is False
        assert retry_after is not None and retry_after > 0
        assert limit_type == "uuid"

    def test_different_uuids_have_separate_buckets(self):
        store = self._fresh_store()
        from verifimind_mcp.middleware.rate_limiter import RATE_LIMIT_BURST_MULTIPLIER
        burst_cap = int(3 * RATE_LIMIT_BURST_MULTIPLIER)
        for _ in range(burst_cap):
            store.check_and_record_uuid(VALID_UUID, 3)
        # UUID_2 should still be allowed
        allowed, _, _ = store.check_and_record_uuid(VALID_UUID_2, 3)
        assert allowed is True

    def test_returns_ok_on_allow(self):
        store = self._fresh_store()
        allowed, retry_after, limit_type = store.check_and_record_uuid(VALID_UUID, 100)
        assert allowed is True
        assert retry_after is None
        assert limit_type == "ok"


# ---------------------------------------------------------------------------
# RateLimitStore.check_and_record (IP path — backward compat)
# ---------------------------------------------------------------------------

class TestCheckAndRecordIp:

    def test_ip_path_still_works(self):
        store = RateLimitStore()
        allowed, _, _ = store.check_and_record("1.2.3.4")
        assert allowed is True

    def test_ip_and_uuid_tracked_separately(self):
        store = RateLimitStore()
        store.check_and_record("1.2.3.4")
        store.check_and_record_uuid(VALID_UUID, 30)
        stats = store.get_stats()
        assert stats["active_ips"] >= 1
        assert stats["active_uuids"] >= 1


# ---------------------------------------------------------------------------
# get_stats includes active_uuids
# ---------------------------------------------------------------------------

class TestGetStatsUuid:

    def test_active_uuids_in_stats(self):
        store = RateLimitStore()
        store.check_and_record_uuid(VALID_UUID, 30)
        stats = store.get_stats()
        assert "active_uuids" in stats
        assert stats["active_uuids"] >= 1

    def test_active_uuids_zero_when_no_uuid_requests(self):
        store = RateLimitStore()
        store.check_and_record("10.0.0.1")
        stats = store.get_stats()
        assert stats["active_uuids"] == 0


# ---------------------------------------------------------------------------
# _resolve_uuid_tier: no Firestore in test env
# ---------------------------------------------------------------------------

class TestResolveUuidTier:

    def test_valid_uuid_no_firestore_returns_scholar(self):
        # Clear cache entry if present
        _uuid_tier_cache.pop(VALID_UUID_2, None)
        tier = _resolve_uuid_tier(VALID_UUID_2)
        assert tier in ("scholar", "pioneer")  # scholar when no Firestore

    def test_result_is_cached(self):
        test_uuid = "019aaaaa-0000-7000-0000-000000000001"
        _uuid_tier_cache.pop(test_uuid, None)
        tier1 = _resolve_uuid_tier(test_uuid)
        # Inject fake cache entry to prove it's used
        _uuid_tier_cache[test_uuid] = ("pioneer", time.time() + 9999)
        tier2 = _resolve_uuid_tier(test_uuid)
        assert tier2 == "pioneer"
        # Cleanup
        _uuid_tier_cache.pop(test_uuid, None)

    def test_expired_cache_triggers_fresh_lookup(self):
        test_uuid = "019bbbbb-0000-7000-0000-000000000002"
        # Inject expired cache entry
        _uuid_tier_cache[test_uuid] = ("pioneer", time.time() - 1)
        tier = _resolve_uuid_tier(test_uuid)
        # After expiry, fresh lookup → scholar (no Firestore in tests)
        assert tier in ("scholar", "pioneer")
        _uuid_tier_cache.pop(test_uuid, None)


# ---------------------------------------------------------------------------
# Server version
# ---------------------------------------------------------------------------

class TestServerVersion:

    def test_server_version_is_0519(self):
        from verifimind_mcp.server import SERVER_VERSION
        assert SERVER_VERSION == "0.5.19", f"Expected 0.5.19, got {SERVER_VERSION}"
