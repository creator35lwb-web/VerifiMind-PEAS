"""
Reasoning-view serialization for VerifiMind-PEAS — v0.5.44 "Reasoning Visible".

The X/Z/CS agents generate a rich auditable-reasoning layer (per-step reasoning,
framework citations, ethics scoring breakdown, Socratic questions, security
dimensions) on every call. Prior to v0.5.44 the flagship `run_full_trinity` JSON
response trimmed all of it, returning only scores + a short summary. That layer IS
the product — this module serializes it into an additive `reasoning` block.

Verbosity ladder (the `detail` parameter):
- "summary"  → no reasoning block (exact pre-0.5.44 response shape — opt-out)
- "standard" → reasoning steps + citations + breakdowns (NEW default; T+L D-41-2)
- "full"     → standard + per-step evidence + the heaviest structured fields

Backward compatibility: the block is strictly additive. Existing response keys are
never removed or renamed; a "summary" call reproduces the old bytes exactly.

Note on per-step citations: the `ReasoningStep` model only persists
step_number / thought / evidence / confidence. Per-step `frameworks_cited` /
`stage` / `standards_cited` that the prompts request are NOT in the schema, so they
are surfaced via the model-level structured fields (scoring_breakdown,
applicable_frameworks, dimensions_evaluated, standards_referenced) instead.
"""

from typing import Any, Dict, List, Optional

VALID_DETAIL = ("summary", "standard", "full")
DEFAULT_DETAIL = "standard"


def normalize_detail(detail: Optional[str]) -> str:
    """Coerce an arbitrary detail value to a valid level (default 'standard')."""
    if not detail:
        return DEFAULT_DETAIL
    d = str(detail).strip().lower()
    return d if d in VALID_DETAIL else DEFAULT_DETAIL


def _serialize_steps(steps: List[Any], full: bool) -> List[Dict[str, Any]]:
    """Render reasoning steps. Evidence is included only at 'full' detail."""
    out: List[Dict[str, Any]] = []
    for s in steps or []:
        d: Dict[str, Any] = {
            "n": s.step_number,
            "thought": s.thought,
            "confidence": s.confidence,
        }
        if full:
            ev = getattr(s, "evidence", None)
            if ev:
                d["evidence"] = ev
        out.append(d)
    return out


def consult_steps(steps: List[Any], detail: str) -> List[Dict[str, Any]]:
    """Reasoning steps for the single-agent consult tools.

    Preserves the legacy ``{"step", "thought", "confidence"}`` key shape (the
    flagship Trinity block uses ``"n"`` instead) for backward compatibility, and
    adds ``evidence`` only at 'full' detail.
    """
    full = detail == "full"
    out: List[Dict[str, Any]] = []
    for s in steps or []:
        d: Dict[str, Any] = {"step": s.step_number, "thought": s.thought, "confidence": s.confidence}
        if full:
            ev = getattr(s, "evidence", None)
            if ev:
                d["evidence"] = ev
        out.append(d)
    return out


def x_reasoning(x_result: Any, detail: str) -> Dict[str, Any]:
    """X Intelligent reasoning view."""
    full = detail == "full"
    block: Dict[str, Any] = {
        "steps": _serialize_steps(x_result.reasoning_steps, full),
        "opportunities": x_result.opportunities,
        "risks": x_result.risks,
        "next_steps": getattr(x_result, "next_steps", None) or [],
    }
    if full:
        block["market_competition"] = getattr(x_result, "market_competition", None)
        block["competitive_analysis"] = getattr(x_result, "competitive_analysis", None)
    return block


def z_reasoning(z_result: Any, detail: str) -> Dict[str, Any]:
    """Z Guardian reasoning view (carries framework citations + scoring breakdown)."""
    full = detail == "full"
    block: Dict[str, Any] = {
        "steps": _serialize_steps(z_result.reasoning_steps, full),
        "scoring_breakdown": getattr(z_result, "scoring_breakdown", None),
        "jurisdiction_detected": getattr(z_result, "jurisdiction_detected", None),
        "applicable_frameworks": getattr(z_result, "applicable_frameworks", None),
        "compliance_timeline": getattr(z_result, "compliance_timeline", None),
        "ethical_concerns": z_result.ethical_concerns,
        "mitigation_measures": z_result.mitigation_measures,
    }
    if full:
        block["total_frameworks_evaluated"] = getattr(z_result, "total_frameworks_evaluated", None)
    return block


def cs_reasoning(cs_result: Any, detail: str) -> Dict[str, Any]:
    """CS Security reasoning view (Socratic questions + threat assessment)."""
    full = detail == "full"
    block: Dict[str, Any] = {
        "steps": _serialize_steps(cs_result.reasoning_steps, full),
        "threat_level": getattr(cs_result, "threat_level", None),
        "socratic_questions": cs_result.socratic_questions,
        "attack_vectors": cs_result.attack_vectors,
        "agentic_threats": getattr(cs_result, "agentic_threats", None),
        "reasoning_layer_findings": getattr(cs_result, "reasoning_layer_findings", None),
        "security_recommendations": cs_result.security_recommendations,
    }
    if full:
        block["dimensions_evaluated"] = getattr(cs_result, "dimensions_evaluated", None)
        block["stages_completed"] = getattr(cs_result, "stages_completed", None)
        block["macp_security_assessment"] = getattr(cs_result, "macp_security_assessment", None)
        block["standards_referenced"] = getattr(cs_result, "standards_referenced", None)
    return block


def build_reasoning_block(
    x_result: Any,
    z_result: Any,
    cs_result: Any,
    chain_status: Dict[str, str],
    overall_quality: str,
    inference_warning: Optional[str],
    detail: str,
) -> Dict[str, Any]:
    """Build the additive `reasoning` block for run_full_trinity.

    Caller must only invoke this for detail in ('standard', 'full'); 'summary'
    callers skip the block entirely to preserve the exact legacy shape.
    """
    return {
        "detail": detail,
        "x": x_reasoning(x_result, detail),
        "z": z_reasoning(z_result, detail),
        "cs": cs_reasoning(cs_result, detail),
        "inference": {
            "x": chain_status.get("x_agent"),
            "z": chain_status.get("z_agent"),
            "cs": chain_status.get("cs_agent"),
            "overall": overall_quality,
            "warning": inference_warning,
        },
    }
