"""Privacy-minimal aggregate telemetry for public MCP tool invocations."""

import json
import sys

from fastmcp.server.middleware import Middleware


# Exact allowlist prevents unknown caller-controlled names from creating
# high-cardinality log labels. Keep this equal to the registered public tools.
INSTRUMENTED_TOOL_NAMES = frozenset({
    "consult_agent_x",
    "consult_agent_z",
    "consult_agent_cs",
    "run_full_trinity",
    "list_prompt_templates",
    "get_prompt_template",
    "export_prompt_template",
    "register_custom_template",
    "import_template_from_url",
    "get_template_statistics",
    "coordination_handoff_create",
    "coordination_handoff_read",
    "coordination_team_status",
})


def emit_tool_invoked(tool_name: object) -> None:
    """Emit one name-only event for an allowlisted public tool."""
    if not isinstance(tool_name, str) or tool_name not in INSTRUMENTED_TOOL_NAMES:
        return
    print(
        json.dumps({
            "severity": "INFO",
            "event": "tool_invoked",
            "tool": tool_name,
        }),
        file=sys.stderr,
        flush=True,
    )


class ToolInvocationTelemetry(Middleware):
    """Observe the outer tools/call boundary without reading tool arguments."""

    async def on_call_tool(self, context, call_next):
        emit_tool_invoked(getattr(context.message, "name", None))
        return await call_next(context)
