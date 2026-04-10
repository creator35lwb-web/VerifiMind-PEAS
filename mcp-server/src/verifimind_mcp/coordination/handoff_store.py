"""
Handoff Store — v0.5.13 Fortify
================================

Dual-backend storage for MACP v2.2 handoff records:
  Primary:  Firestore `coordination_handoffs` collection (cross-instance persistence)
  Fallback: In-memory deque per pioneer key (when Firestore unavailable)

Firestore document ID: record["filename"] (e.g. "20260410_RNA_development.md")
Firestore collection:  coordination_handoffs

The HandoffStore is process-global and thread-safe. Each pioneer_key is an isolated
namespace — one user's handoffs are never visible to another user.

Max handoffs per key (in-memory): 50 (configurable via MAX_HANDOFFS_PER_KEY).
"""

import logging
import os
import threading
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Firestore collection for coordination handoffs
COLLECTION_HANDOFFS = "coordination_handoffs"


def _get_firestore_client():
    """Lazy-init Firestore client. Returns None if unavailable."""
    project_id = os.environ.get("FIRESTORE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        return None
    try:
        from google.cloud import firestore  # type: ignore
        return firestore.Client(project=project_id)
    except Exception as e:
        logger.warning("Firestore unavailable for handoff store: %s", e)
        return None

MAX_HANDOFFS_PER_KEY = 50


class HandoffStore:
    """Thread-safe in-memory store for coordination handoff records.

    Keys are pioneer_key strings (per-user namespace).
    Values are deques of handoff dicts, newest-last.
    """

    def __init__(self, max_per_key: int = MAX_HANDOFFS_PER_KEY):
        self._max = max_per_key
        self._lock = threading.Lock()
        self._data: dict[str, deque] = defaultdict(lambda: deque(maxlen=self._max))

    def add(self, pioneer_key: str, handoff: dict) -> None:
        """Append a handoff record under the given pioneer_key.

        Writes to Firestore (coordination_handoffs collection) when available,
        then appends to in-memory deque. If Firestore fails, in-memory only.
        """
        # Firestore write (primary persistence — cross-instance)
        try:
            db = _get_firestore_client()
            if db is not None:
                doc_id = handoff.get("filename", handoff.get("handoff_id", str(uuid.uuid4())))
                doc_data = {**handoff, "pioneer_key_prefix": pioneer_key[:8]}
                db.collection(COLLECTION_HANDOFFS).document(doc_id).set(doc_data)
                logger.debug("Handoff persisted to Firestore: %s", doc_id)
        except Exception as e:
            logger.warning("Firestore handoff write failed (in-memory fallback): %s", e)

        # In-memory write (fast reads, process-lifetime)
        with self._lock:
            self._data[pioneer_key].append(handoff)

    def get(
        self,
        pioneer_key: str,
        agent_id: str | None = None,
        count: int = 1,
    ) -> list[dict]:
        """Return the most recent `count` handoffs for a pioneer_key.

        Args:
            pioneer_key: User namespace key.
            agent_id: If provided, filter to handoffs from this agent only.
            count: Maximum number of records to return (newest first).

        Returns:
            List of handoff dicts, most recent first.
        """
        count = max(1, min(count, self._max))
        with self._lock:
            records = list(self._data[pioneer_key])

        if agent_id:
            records = [r for r in records if r.get("agent_id") == agent_id]

        # Return newest first
        return list(reversed(records))[:count]

    def get_all(self, pioneer_key: str) -> list[dict]:
        """Return all handoffs for a pioneer_key (oldest first)."""
        with self._lock:
            return list(self._data[pioneer_key])

    def count(self, pioneer_key: str) -> int:
        """Return total number of stored handoffs for a key."""
        with self._lock:
            return len(self._data[pioneer_key])

    def clear(self, pioneer_key: str) -> None:
        """Remove all handoffs for a key (testing / cleanup use only)."""
        with self._lock:
            self._data[pioneer_key].clear()


# Process-global singleton
_global_store = HandoffStore()


def get_store() -> HandoffStore:
    """Return the process-global HandoffStore singleton."""
    return _global_store


def build_handoff_record(
    agent_id: str,
    session_type: str,
    completed: list[str],
    decisions: list[str],
    artifacts: list[str],
    pending: list[str],
    blockers: list[str],
    next_agent: str | None,
) -> dict[str, Any]:
    """Construct a handoff dict with all required MACP v2.2 fields.

    Args:
        agent_id: Short identifier for the agent (e.g. "RNA", "cursor", "XV").
        session_type: Type of session (e.g. "development", "research", "review").
        completed: List of completed items.
        decisions: List of decisions made (as strings).
        artifacts: List of artifact paths/descriptions created.
        pending: List of pending items for the next agent.
        blockers: List of current blockers (empty list if none).
        next_agent: Recommended next agent ID (or None).

    Returns:
        Handoff dict ready for storage and markdown generation.
    """
    now = datetime.now(timezone.utc)
    handoff_id = str(uuid.uuid4())[:8]
    date_str = now.strftime("%Y%m%d")

    desc_slug = session_type.lower().replace(" ", "-").replace("_", "-")
    filename = f"{date_str}_{agent_id.upper()}_{desc_slug}.md"

    return {
        "handoff_id": handoff_id,
        "filename": filename,
        "timestamp": now.isoformat(),
        "date": date_str,
        "agent_id": agent_id,
        "session_type": session_type,
        "completed": completed,
        "decisions": decisions,
        "artifacts": artifacts,
        "pending": pending,
        "blockers": blockers,
        "next_agent": next_agent or "",
        "macp_version": "2.2",
        "status": "CREATED",
    }
