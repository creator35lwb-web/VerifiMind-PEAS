"""
Shared in-process harness for walking REGISTERED MCP tool bodies.
=================================================================

Extracted from `test_v0550_robustness_walk.py` when the coordination
containment suite (VM-IR-2026-07-28-COORD-01) needed the same two helpers.
Two copies of the payload extractor would have been two places to fix when a
fastmcp result shape changes — and a security suite that decodes tool
responses differently from the robustness suite could disagree about what a
tool actually returned.

Used by:
  - test_v0550_robustness_walk.py  (mock-provider E2E walks)
  - test_coordination_containment.py  (fail-closed denial contract)
"""

import json

from fastmcp import Client


def payload_of(result):
    """Extract the tool's dict payload from a fastmcp CallToolResult."""
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    raise AssertionError(f"no dict payload in tool result: {result!r}")


async def call(app, name, args):
    """Call a registered tool in-process and return its dict payload."""
    async with Client(app) as client:
        return payload_of(await client.call_tool(name, args))
