"""
Markdown-first report generation for VerifiMind-PEAS.

Converts TrinityResult validation output into structured Markdown
with YAML frontmatter, aligned with the Markdown-first strategic pivot
and agent-native communication standards (Cloudflare, A2A, MCP).

v0.4.1 — February 2026
"""

from datetime import timezone
from typing import List, Optional

from ..models.results import TrinityResult, TrinitySynthesis
from ..models.reasoning import (
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    ReasoningStep,
)

FORMAT_VERSION = "markdown-first/1.0"


def _server_version() -> str:
    """Source the live server version lazily (avoids a hardcoded 3rd constant
    drifting out of sync — v0.5.44 fix; was pinned at a stale "0.4.1")."""
    try:
        from ..server import SERVER_VERSION as _SV
        return _SV
    except Exception:  # pragma: no cover - defensive
        return "unknown"


def generate_yaml_frontmatter(result: TrinityResult) -> str:
    """Generate YAML frontmatter block from a TrinityResult.

    Returns the frontmatter string including opening/closing ``---`` delimiters.
    """
    ts = result.completed_at or result.started_at
    iso_ts = ts.isoformat() if ts.tzinfo else ts.replace(tzinfo=timezone.utc).isoformat()

    s = result.synthesis
    gate_agents = s.quality_gate.get("agents", {}) if s.quality_gate else {}

    def _frontmatter_score(agent_id: str, score: Optional[float]) -> str:
        if score is None or gate_agents.get(agent_id, "real") != "real":
            return "null"
        return f"{score:.1f}"

    confidence = (
        f"{s.confidence:.2f}" if s.confidence is not None else "null"
    )
    degraded = ", ".join(s.degraded_agents)

    lines = [
        "---",
        f"validation_id: {result.validation_id}",
        f'concept: "{_escape_yaml(result.concept_name)}"',
        f"recommendation: {s.recommendation}",
        f"overall_score: {_nullable_score(s.overall_score, yaml=True)}",
        f"innovation_score: {_frontmatter_score('X', s.innovation_score)}",
        f"ethics_score: {_frontmatter_score('Z', s.ethics_score)}",
        f"security_score: {_frontmatter_score('CS', s.security_score)}",
        "veto_triggered: " + (
            "null" if s.veto_triggered is None
            else "true" if s.veto_triggered
            else "false"
        ),
        f"confidence: {confidence}",
        f"confidence_valid: {'true' if s.confidence_valid else 'false'}",
        f"analysis_incomplete: {'true' if s.analysis_incomplete else 'false'}",
        f'degraded_agents: "{degraded}"',
        f"timestamp: {iso_ts}",
        f"generator: verifimind-peas/{_server_version()}",
        f"format: {FORMAT_VERSION}",
        "---",
    ]
    return "\n".join(lines)


def generate_markdown_summary(result: TrinityResult) -> str:
    """Generate a concise Markdown summary (no frontmatter, no reasoning chains).

    Suitable for inline display, MCP tool responses, and quick reviews.
    """
    s = result.synthesis
    rec_display = s.recommendation.upper().replace("_", " ")
    confidence_display = _synthesis_confidence_display(s)

    lines = [
        f"# Trinity Validation: {result.concept_name}",
        "",
        f"**Recommendation:** {rec_display} | "
        f"**Score:** {_nullable_score(s.overall_score)} | "
        f"**Confidence:** {confidence_display}",
        "",
    ]

    if s.veto_triggered:
        lines.append(f"> **VETO TRIGGERED** by Z Guardian: {s.veto_reason or 'Ethical red line crossed'}")
        lines.append("")

    lines.extend([
        "| Agent | Score | Role |",
        "|-------|-------|------|",
        f"| X Intelligent | {_nullable_score(s.innovation_score)} | Innovation & Strategy |",
        f"| Z Guardian | {_nullable_score(s.ethics_score)} | Ethics & Compliance |",
        f"| CS Security | {_nullable_score(s.security_score)} | Security & Socratic Scrutiny |",
        "",
    ])

    if s.strengths:
        lines.append("**Strengths:** " + "; ".join(s.strengths[:3]))
        lines.append("")

    if s.concerns:
        lines.append("**Concerns:** " + "; ".join(s.concerns[:3]))
        lines.append("")

    lines.extend([
        "---",
        f"*Validation ID: {result.validation_id} | Human decision required*",
    ])

    return "\n".join(lines)


def generate_markdown_report(result: TrinityResult) -> str:
    """Generate a full Markdown validation report with YAML frontmatter.

    This is the primary report format for VerifiMind-PEAS, replacing PDF
    as the canonical output. The report includes:
    - YAML frontmatter with machine-readable metadata
    - Executive summary with scores and recommendation
    - Full agent analyses with reasoning chains
    - Synthesis strengths, concerns, and recommendations
    - Audit footer with validation ID and timestamps
    """
    sections = [
        generate_yaml_frontmatter(result),
        "",
        _section_title(result),
        _section_executive_summary(result.synthesis),
        _section_x_agent(result.x_analysis),
        _section_z_agent(result.z_analysis),
        _section_cs_agent(result.cs_analysis),
        _section_synthesis(result.synthesis),
        _section_footer(result),
    ]

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Internal section builders
# ---------------------------------------------------------------------------


def _section_title(result: TrinityResult) -> str:
    return f"# Trinity Validation Report: {result.concept_name}\n"


def _section_executive_summary(s: TrinitySynthesis) -> str:
    rec_display = s.recommendation.upper().replace("_", " ")
    confidence_display = _synthesis_confidence_display(s)
    gate_agents = s.quality_gate.get("agents", {}) if s.quality_gate else {}

    def _score(agent_id: str, value: Optional[float]) -> str:
        if value is None or gate_agents.get(agent_id, "real") != "real":
            return "unavailable"
        return f"{value:.1f}/10"

    lines = [
        "## Executive Summary",
        "",
        s.summary,
        "",
        f"**Recommendation:** {rec_display} | "
        f"**Score:** {_nullable_score(s.overall_score)} | "
        f"**Confidence:** {confidence_display}",
        "",
    ]

    if s.veto_triggered:
        lines.extend([
            f"> **VETO TRIGGERED** by Z Guardian: {s.veto_reason or 'Ethical red line crossed'}",
            "",
        ])

    # v0.5.44: surface the degraded-inference fail-safe (if set)
    inference_warning = getattr(s, "inference_warning", None)
    if inference_warning:
        lines.extend([
            f"> ⚠️ **DEGRADED INFERENCE — HUMAN REVIEW REQUIRED:** {inference_warning}",
            "",
        ])

    lines.extend([
        "| Agent | Score | Role |",
        "|-------|-------|------|",
        f"| X Intelligent | {_score('X', s.innovation_score)} | Innovation & Strategy |",
        f"| Z Guardian | {_score('Z', s.ethics_score)} | Ethics & Compliance |",
        f"| CS Security | {_score('CS', s.security_score)} | Security & Socratic Scrutiny |",
        "",
    ])

    return "\n".join(lines)


def _section_x_agent(x: XAgentAnalysis) -> str:
    quality = getattr(x, "_inference_quality", "real")
    if quality != "real":
        return _degraded_agent_section(x.agent, "Innovation & Strategy", quality)
    conf_pct = int(x.confidence * 100)
    lines = [
        f"## {x.agent} — Innovation & Strategy",
        "",
        f"**Innovation Score:** {x.innovation_score:.1f}/10 | "
        f"**Strategic Value:** {x.strategic_value:.1f}/10 | "
        f"**Confidence:** {conf_pct}%",
        "",
    ]

    lines.extend(_format_reasoning_chain(x.reasoning_steps))

    if x.opportunities:
        lines.append("### Opportunities")
        lines.append("")
        for item in x.opportunities:
            lines.append(f"- {item}")
        lines.append("")

    if x.risks:
        lines.append("### Risks")
        lines.append("")
        for item in x.risks:
            lines.append(f"- {item}")
        lines.append("")

    lines.append(f"**Recommendation:** {x.recommendation}")
    lines.append("")
    return "\n".join(lines)


def _section_z_agent(z: ZAgentAnalysis) -> str:
    quality = getattr(z, "_inference_quality", "real")
    if quality != "real":
        return _degraded_agent_section(z.agent, "Ethics & Compliance", quality)
    conf_pct = int(z.confidence * 100)
    compliance = "Yes" if z.z_protocol_compliance else "No"
    veto = "Yes" if z.veto_triggered else "No"

    lines = [
        f"## {z.agent} — Ethics & Compliance",
        "",
        f"**Ethics Score:** {z.ethics_score:.1f}/10 | "
        f"**Z-Protocol Compliant:** {compliance} | "
        f"**Veto:** {veto} | "
        f"**Confidence:** {conf_pct}%",
        "",
    ]

    # v0.5.44: jurisdiction + framework citations (the auditable ethics layer)
    jurisdiction = getattr(z, "jurisdiction_detected", None)
    if jurisdiction:
        lines.append(f"**Jurisdictions detected:** {', '.join(jurisdiction)}")
        lines.append("")
    breakdown = getattr(z, "scoring_breakdown", None)
    if isinstance(breakdown, dict) and breakdown:
        lines.append("### Ethics Scoring Breakdown")
        lines.append("")
        lines.append("| Dimension | Score | Weight | Frameworks |")
        lines.append("|-----------|------:|-------:|------------|")
        for dim, d in breakdown.items():
            if isinstance(d, dict):
                fw = d.get("frameworks", [])
                fw_str = ", ".join(fw) if isinstance(fw, list) else str(fw)
                lines.append(f"| {dim.replace('_', ' ').title()} | {d.get('score', '?')} | {d.get('weight', '?')} | {fw_str} |")
        lines.append("")

    lines.extend(_format_reasoning_chain(z.reasoning_steps))

    if z.ethical_concerns:
        lines.append("### Ethical Concerns")
        lines.append("")
        for item in z.ethical_concerns:
            lines.append(f"- {item}")
        lines.append("")

    if z.mitigation_measures:
        lines.append("### Mitigation Measures")
        lines.append("")
        for item in z.mitigation_measures:
            lines.append(f"- {item}")
        lines.append("")

    lines.append(f"**Recommendation:** {z.recommendation}")
    lines.append("")
    return "\n".join(lines)


def _section_cs_agent(cs: CSAgentAnalysis) -> str:
    quality = getattr(cs, "_inference_quality", "real")
    if quality != "real":
        return _degraded_agent_section(
            cs.agent, "Security & Socratic Scrutiny", quality
        )
    conf_pct = int(cs.confidence * 100)

    threat = getattr(cs, "threat_level", None)
    threat_str = f" | **Threat Level:** {threat}" if threat else ""
    lines = [
        f"## {cs.agent} — Security & Socratic Scrutiny",
        "",
        f"**Security Score:** {cs.security_score:.1f}/10 | "
        f"**Confidence:** {conf_pct}%{threat_str}",
        "",
    ]

    lines.extend(_format_reasoning_chain(cs.reasoning_steps))

    if cs.vulnerabilities:
        lines.append("### Vulnerabilities")
        lines.append("")
        for item in cs.vulnerabilities:
            lines.append(f"- {item}")
        lines.append("")

    if cs.attack_vectors:
        lines.append("### Attack Vectors")
        lines.append("")
        for item in cs.attack_vectors:
            lines.append(f"- {item}")
        lines.append("")

    if cs.security_recommendations:
        lines.append("### Security Recommendations")
        lines.append("")
        for item in cs.security_recommendations:
            lines.append(f"- {item}")
        lines.append("")

    if cs.socratic_questions:
        lines.append("### Socratic Questions")
        lines.append("")
        for i, q in enumerate(cs.socratic_questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

    lines.append(f"**Recommendation:** {cs.recommendation}")
    lines.append("")
    return "\n".join(lines)


def _section_synthesis(s: TrinitySynthesis) -> str:
    lines = []

    if s.strengths:
        lines.append("## Strengths")
        lines.append("")
        for item in s.strengths:
            lines.append(f"- {item}")
        lines.append("")

    if s.concerns:
        lines.append("## Concerns")
        lines.append("")
        for item in s.concerns:
            lines.append(f"- {item}")
        lines.append("")

    if s.recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for item in s.recommendations:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def _section_footer(result: TrinityResult) -> str:
    ts = result.completed_at or result.started_at
    iso_ts = ts.isoformat() if ts.tzinfo else ts.replace(tzinfo=timezone.utc).isoformat()
    duration = ""
    if result.duration_seconds is not None:
        duration = f" | Duration: {result.duration_seconds:.1f}s"

    lines = [
        "---",
        f"*Validation ID: {result.validation_id} | Generated: {iso_ts}{duration}*",
        f"*Human decision required: This report is advisory only.*",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synthesis_confidence_display(s: TrinitySynthesis) -> str:
    if s.confidence is None or not s.confidence_valid:
        return "unavailable (degraded inference)"
    return f"{int(s.confidence * 100)}%"


def _nullable_score(value: Optional[float], yaml: bool = False) -> str:
    if value is None:
        return "null" if yaml else "unavailable"
    return f"{value:.1f}" if yaml else f"{value:.1f}/10"


def _degraded_agent_section(agent_name: str, role: str, quality: str) -> str:
    return "\n".join([
        f"## {agent_name} — {role}",
        "",
        (
            f"> ⚠️ **INCOMPLETE AGENT ANALYSIS:** inference quality was "
            f"`{quality}`. Scores, confidence, and generated findings from this "
            "stage are withheld pending a clean rerun."
        ),
        "",
    ])


def _format_reasoning_chain(steps: List[ReasoningStep]) -> List[str]:
    """Format a list of reasoning steps as a numbered Markdown list."""
    if not steps:
        return []

    lines = ["### Reasoning Chain", ""]
    for step in steps:
        conf_pct = int(step.confidence * 100)
        lines.append(f"{step.step_number}. {step.thought} *(confidence: {conf_pct}%)*")
        if step.evidence:
            lines.append(f"   - Evidence: {step.evidence}")
    lines.append("")
    return lines


def _escape_yaml(text: str) -> str:
    """Escape a string for safe inclusion in YAML double-quoted value."""
    return text.replace("\\", "\\\\").replace('"', '\\"')
