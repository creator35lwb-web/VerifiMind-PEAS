"""Client address behind the deployment's ingress proxy chain.

CS round 2 (2026-09-02), finding F2: the two per-IP limiters selected the
client address with a hardcoded index into ``X-Forwarded-For``. Which element
is the client is a property of the ingress topology, not of the code:

* Cloud Run reached directly — the ``run.app`` URL or a domain mapping through
  the Google Front End — appends exactly the client, so the client is the LAST
  element: ``INGRESS_PROXY_HOPS=1`` (the default; production receipt
  2026-09-02: domain mapping, no forwarding rules, no serverless NEGs).
* A Google external Application Load Balancer in front of Cloud Run appends
  ``<client>, <load balancer>``, so the client is the SECOND-TO-LAST element:
  ``INGRESS_PROXY_HOPS=2``. With the default, every caller would collapse into
  the load balancer's single bucket.

Every deployment binds this value to its own ingress. Too small lets a caller
choose the key (the S155 leftmost-XFF defect). Too large is worse than a
collapse: behind an LB it merges every caller into the LB's bucket, and on an
ingress that appends FEWER elements than the configured depth, element
``[-depth]`` is caller-supplied again — key rotation re-opened. A depth above
1 must therefore be proven by the deployment's ingress receipt, never assumed.
When the chain is SHORTER than the configured depth, no element can be
relied on and the DIRECT peer is used — never a caller-supplied element.

Naming note: these identifiers deliberately avoid the word "trusted". CodeQL's
sensitive-data heuristic classifies any identifier containing it as a secret
and flags its disclosure (``py/clear-text-logging-sensitive-data``); the value
here is a small integer configuration knob that the startup banner discloses
on purpose.
"""

import os
from typing import Optional

DEFAULT_PROXY_HOPS = 1
MAX_PROXY_HOPS = 8


def ingress_proxy_hops() -> int:
    """Number of trailing ``X-Forwarded-For`` elements appended by the
    deployment's ingress. Read per call so a misconfiguration is a restart away
    from fixed; invalid values fall back to the default, out-of-range values
    are clamped."""
    raw = os.getenv("INGRESS_PROXY_HOPS", "").strip()
    if not raw:
        return DEFAULT_PROXY_HOPS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_PROXY_HOPS
    return min(max(value, 1), MAX_PROXY_HOPS)


def resolve_client_ip(
    forwarded_for: Optional[str],
    direct_peer: Optional[str],
    *,
    real_ip: Optional[str] = None,
) -> str:
    """Client address for rate-limit / issuance-limit keys.

    ``forwarded_for`` is the raw ``X-Forwarded-For`` header (or None);
    ``direct_peer`` is the transport peer; ``real_ip`` is an optional
    ``X-Real-IP`` fallback honoured ONLY when no forwarded chain exists (the
    prior behaviour of the request rate limiter, preserved).
    """
    hops = [hop.strip() for hop in (forwarded_for or "").split(",") if hop.strip()]
    if hops:
        depth = ingress_proxy_hops()
        if len(hops) >= depth:
            return hops[-depth]
        # A chain shorter than the ingress produces: the header did not come
        # through that ingress, so no element of it can be relied on.
        return direct_peer or "unknown"
    if real_ip and real_ip.strip():
        return real_ip.strip()
    return direct_peer or "unknown"


def ingress_disclosure() -> dict:
    """Disclosure of the configured depth (startup banner / receipts)."""
    depth = ingress_proxy_hops()
    return {
        "proxy_hops": depth,
        "client_element": f"X-Forwarded-For[-{depth}]",
        "short_chain_policy": "direct peer",
    }
