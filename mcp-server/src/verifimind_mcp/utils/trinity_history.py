"""
P1-B: Fire-and-forget Firestore persistence for Scholar Trinity history.

Writes validation metadata to:
  trinity_history/{uuid}/validations/{validation_id}

Privacy invariants (consistent with Privacy Policy v2.1):
  - NO concept names or descriptions stored
  - NO agent response content stored
  - Only scores, recommendations, timestamps, session IDs
  - Only written when user_uuid is explicitly provided (opt-in)
  - Silently skipped if Firestore unavailable (non-blocking)
"""

import asyncio
import logging
from datetime import datetime, timezone

from verifimind_mcp.utils.uuid_tracer import is_valid_uuid

logger = logging.getLogger(__name__)


def _get_firestore_async():
    try:
        from google.cloud import firestore
        return firestore.AsyncClient()
    except Exception:
        return None


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_record(uuid: str, tool: str, raw_result: dict) -> dict:
    """Extract metadata-only record — no concept content."""
    record: dict = {
        "uuid": uuid,
        "tool": tool,
        "timestamp": _ts(),
        "validation_id": raw_result.get("validation_id", _ts()),
    }
    if tool == "run_full_trinity":
        synthesis = raw_result.get("synthesis", {})
        record.update({
            "overall_score": synthesis.get("overall_score"),
            "recommendation": synthesis.get("recommendation"),
            "veto_triggered": synthesis.get("veto_triggered", False),
            "session_id": raw_result.get("_session_id", ""),
            "agents_completed": raw_result.get("_agents_completed", []),
            "quality": raw_result.get("_overall_quality", ""),
        })
    elif tool == "consult_agent_x":
        record["score"] = raw_result.get("innovation_score")
        record["recommendation"] = raw_result.get("recommendation", "")
    elif tool == "consult_agent_z":
        record["score"] = raw_result.get("ethics_score")
        record["recommendation"] = raw_result.get("recommendation", "")
        record["veto_triggered"] = raw_result.get("veto_triggered", False)
    elif tool == "consult_agent_cs":
        record["score"] = raw_result.get("security_score")
        record["recommendation"] = raw_result.get("recommendation", "")
    return record


async def _write_to_firestore(uuid: str, record: dict) -> None:
    """Async Firestore write — runs as background task."""
    try:
        db = _get_firestore_async()
        if db is None:
            return
        validation_id = record.get("validation_id", _ts())
        doc_ref = (
            db.collection("trinity_history")
            .document(uuid)
            .collection("validations")
            .document(validation_id)
        )
        await doc_ref.set(record)
        logger.debug("trinity_history written: uuid=%s tool=%s", uuid[:8], record["tool"])
    except Exception as exc:
        logger.warning("trinity_history write skipped (non-critical): %s", type(exc).__name__)


def persist_trinity_result(uuid: str | None, tool: str, raw_result: dict) -> None:
    """
    Fire-and-forget: schedule Firestore write for Scholar validation history.

    - Skips silently if uuid is invalid or result is an error response.
    - Non-blocking: schedules as asyncio task, does not await.
    - Firestore failures are caught and logged — never raise to caller.
    """
    if not is_valid_uuid(uuid):
        return
    if raw_result.get("status") == "error":
        return
    record = _build_record(uuid, tool, raw_result)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_write_to_firestore(uuid, record))
    except RuntimeError:
        pass
