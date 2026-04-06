"""
Middleware modules for VerifiMind MCP Server.

v0.3.1 - Security & Sustainability
v0.5.11 - Tier-Gating (Pioneer vs Scholar)
"""

from .rate_limiter import (
    RateLimitMiddleware,
    get_rate_limit_stats,
    get_client_ip,
    RATE_LIMIT_PER_IP,
    RATE_LIMIT_GLOBAL,
    RATE_LIMIT_WINDOW,
)
from .tier_gate import (
    check_tier,
    tier_gate_error,
    sanitize_handoff_content,
    TIER_SCHOLAR,
    TIER_PIONEER,
)

__all__ = [
    "RateLimitMiddleware",
    "get_rate_limit_stats",
    "get_client_ip",
    "RATE_LIMIT_PER_IP",
    "RATE_LIMIT_GLOBAL",
    "RATE_LIMIT_WINDOW",
    "check_tier",
    "tier_gate_error",
    "sanitize_handoff_content",
    "TIER_SCHOLAR",
    "TIER_PIONEER",
]
