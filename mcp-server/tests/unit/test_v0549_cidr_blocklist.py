"""
CIDR Blocklist — v0.5.49 Security Layer
========================================

Tests for the 45.148.10.0/24 subnet block (4th confirmed scanner IP from the
subnet — .15, .62, .67, .194 — triggering the pre-agreed CIDR threshold,
Alton 2026-06-28) and the new BLOCKED_CIDRS matching layer:
  - Scanner #27 (45.148.10.194) blocked by exact match
  - Unlisted successor IPs in 45.148.10.0/24 blocked by CIDR fallback
  - Adjacent subnets and legitimate traffic unaffected
  - Malformed X-Forwarded-For fragments never crash the check
"""

from unittest.mock import MagicMock

from verifimind_mcp.middleware.ip_blocklist import (
    BLOCKED_CIDRS,
    BLOCKED_IPS,
    _check_ip,
)

# Fixture addresses. The 45.148.x values are the REAL production blocklist
# targets under test — hardcoded by design; the blocklist must match exactly these.
SCANNER_27_IP = "45.148.10.194"  # NOSONAR
SCANNER_NET_CIDR = "45.148.10.0/24"  # NOSONAR
UNLISTED_SUBNET_IP = "45.148.10.200"  # NOSONAR
XFF_SUBNET_IP = "45.148.10.250"  # NOSONAR
SUBNET_EDGE_LOW = "45.148.10.0"  # NOSONAR
SUBNET_EDGE_HIGH = "45.148.10.255"  # NOSONAR
ADJACENT_SUBNET_IP = "45.148.11.194"  # NOSONAR
# Benign-traffic roles use RFC 5737 / RFC 3849 documentation addresses.
BENIGN_FINAL_HOP = "203.0.113.50"
BENIGN_CLIENT = "198.51.100.42"
IPV6_CLIENT = "2001:db8::1"


def _make_request(
    xff: str = "",
    ua: str = "python-httpx/0.27.0",
    client_host: str = "203.0.113.1",
    path: str = "/mcp/",
):
    req = MagicMock()
    req.url.path = path
    req.client = MagicMock()
    req.client.host = client_host
    headers = {}
    if xff:
        headers["x-forwarded-for"] = xff
    headers["user-agent"] = ua
    req.headers = headers
    return req


class TestScanner27Entry:

    def test_45_148_10_194_present(self):
        ips = {ip for ip, *_ in BLOCKED_IPS}
        assert SCANNER_27_IP in ips

    def test_45_148_10_194_blocked_exact(self):
        blocked, matched, reason = _check_ip(_make_request(client_host=SCANNER_27_IP))
        assert blocked and matched == SCANNER_27_IP
        assert reason == "CONFIG_SECRET_SCANNER"


class TestCidrLayer:

    def test_slash24_cidr_defined(self):
        cidrs = {c for c, *_ in BLOCKED_CIDRS}
        assert SCANNER_NET_CIDR in cidrs

    def test_all_cidr_entries_have_four_fields(self):
        for entry in BLOCKED_CIDRS:
            assert len(entry) == 4

    def test_unlisted_subnet_ip_blocked_via_cidr(self):
        # .200 is NOT in BLOCKED_IPS — only the CIDR layer can catch it
        listed = {ip for ip, *_ in BLOCKED_IPS}
        assert UNLISTED_SUBNET_IP not in listed
        blocked, matched, reason = _check_ip(_make_request(client_host=UNLISTED_SUBNET_IP))
        assert blocked and matched == UNLISTED_SUBNET_IP
        assert reason == "CONFIG_SECRET_SCANNER_NET"

    def test_cidr_catches_ip_in_xff_chain(self):
        blocked, matched, _ = _check_ip(
            _make_request(xff=f"198.51.100.7, {XFF_SUBNET_IP}", client_host=BENIGN_FINAL_HOP)
        )
        assert blocked and matched == XFF_SUBNET_IP

    def test_adjacent_subnet_not_blocked(self):
        blocked, _, _ = _check_ip(_make_request(client_host=ADJACENT_SUBNET_IP))
        assert not blocked

    def test_subnet_boundary_edges_blocked(self):
        for edge in (SUBNET_EDGE_LOW, SUBNET_EDGE_HIGH):
            blocked, _, _ = _check_ip(_make_request(client_host=edge))
            assert blocked, edge


class TestRobustness:

    def test_malformed_xff_fragment_does_not_crash(self):
        blocked, _, _ = _check_ip(
            _make_request(xff="unknown, garbage-value, 203.0.113.9", client_host="203.0.113.9")
        )
        assert not blocked

    def test_ipv6_client_unaffected_by_ipv4_cidr(self):
        blocked, _, _ = _check_ip(_make_request(client_host=IPV6_CLIENT))
        assert not blocked

    def test_legitimate_traffic_unaffected(self):
        blocked, _, _ = _check_ip(_make_request(client_host=BENIGN_CLIENT))
        assert not blocked
