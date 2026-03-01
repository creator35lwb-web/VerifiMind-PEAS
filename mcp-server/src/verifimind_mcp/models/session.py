"""
Session state management for VerifiMind-PEAS.

v0.5.0 — ADK-inspired SessionContext for Trinity run traceability.

Each Trinity run gets a unique session_id for correlation and debugging.
Agents write their outputs to named keys; the orchestrator reads them.

SECURITY: Never write api_key values into session state.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SessionContext:
    """
    Tracks state across a single Trinity validation run.

    Inspired by Google ADK's output_key pattern — each agent writes its
    output to a named key in the session, which subsequent agents can
    reference. The session_id enables log correlation and future
    re-run-single-agent capabilities.

    Usage::

        session = SessionContext(concept_name="My Idea")
        session.write("X", {"score": 7.5, "provider": "groq/llama-3.3-70b"})
        session.write("Z", {"score": 8.0, "veto": False})
        session.write("CS", {"score": 6.5})

        # In tool response:
        response.update(session.to_metadata())
        # Adds: _session_id, _session_started, _agents_completed

    Security note: NEVER write api_key values into session state.
    Keys are ephemeral (v0.4.5 BYOK design) — they must not enter any
    persistent or loggable structure.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    concept_name: str = ""
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    outputs: Dict[str, Any] = field(default_factory=dict)

    def write(self, output_key: str, value: Any) -> None:
        """Agent writes its output to the session.

        Args:
            output_key: Agent identifier (e.g. "X", "Z", "CS")
            value: Agent output dict — must NOT contain api_key values
        """
        self.outputs[output_key] = value

    def read(self, output_key: str) -> Optional[Any]:
        """Orchestrator reads a previous agent's output.

        Args:
            output_key: Agent identifier to read

        Returns:
            Agent output dict, or None if not yet written
        """
        return self.outputs.get(output_key)

    @property
    def agents_completed(self) -> List[str]:
        """List of agent keys that have written output."""
        return list(self.outputs.keys())

    def to_metadata(self) -> Dict[str, Any]:
        """Return session metadata for inclusion in tool response.

        Returns backward-compatible fields (all prefixed with _session_).
        Only Trinity-level tools include session metadata — individual
        consult_agent_x/z/cs calls do not create sessions.
        """
        return {
            "_session_id": self.session_id,
            "_session_started": self.started_at,
            "_agents_completed": self.agents_completed,
        }
