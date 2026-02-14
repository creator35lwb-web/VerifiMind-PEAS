"""
Markdown-first report generation for VerifiMind-PEAS.

Converts TrinityResult validation output into structured Markdown
with YAML frontmatter, aligned with the Markdown-first strategic pivot
and agent-native communication standards (Cloudflare, A2A, MCP).

v0.4.1 — February 2026
"""

from datetime import datetime, timezone
from typing import List, Optional

from ..models.results import TrinityResult, TrinitySynthesis
from ..models.reasoning import (
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    ReasoningStep,
)

SERVER_VERSION = "0.4.1"
FORMAT_VERSION = "markdown-first/1.0"


def generate_yaml_frontmatter(result: TrinityResult) -> str:
    """Generate YAML frontmatter block from a TrinityResult.

    Returns the frontmatter string including opening/closing ``---`` delimiters.
    """
    ts = result.completed_at or result.started_at
    iso_ts = ts.isoformat() if ts.tzinfo else ts.replace(tzinfo=timezone.utc).isoformat()

    lines = [
        "---",
        f"validation_id: {result.validation_id}",
        f'concept: "{_escape_yaml(result.concept_name)}"',
        f"recommendation: {result.synthesis.recommendation}",
        f"overall_score: {result.synthesis.overall_score:.1f}",
        f"innovation_score: {result.synthesis.innovation_score:.1f}",
        f"ethics_score: {result.synthesis.ethics_score:.1f}",
        f"security_score: {result.synthesis.security_score:.1f}",
        f"veto_triggered: {'true' if result.synthesis.veto_triggered else 'false'}",
        f"confidence: {result.synthesis.confidence:.2f}",
        f"timestamp: {iso_ts}",
        f"generator: verifimind-peas/{SERVER_VERSION}",
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
    conf_pct = int(s.confidence * 100)

    lines = [
        f"# Trinity Validation: {result.concept_name}",
        "",
        f"**Recommendation:** {rec_display} | "
        f"**Score:** {s.overall_score:.1f}/10 | "
        f"**Confidence:** {conf_pct}%",
        "",
    ]

    if s.veto_triggered:
        lines.append(f"> **VETO TRIGGERED** by Z Guardian: {s.veto_reason or 'Ethical red line crossed'}")
        lines.append("")

    lines.extend([
        "| Agent | Score | Role |",
        "|-------|-------|------|",
        f"| X Intelligent | {s.innovation_score:.1f}/10 | Innovation & Strategy |",
        f"| Z Guardian | {s.ethics_score:.1f}/10 | Ethics & Compliance |",
        f"| CS Security | {s.security_score:.1f}/10 | Security & Socratic Scrutiny |",
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
    conf_pct = int(s.confidence * 100)

    lines = [
        "## Executive Summary",
        "",
        s.summary,
        "",
        f"**Recommendation:** {rec_display} | "
        f"**Score:** {s.overall_score:.1f}/10 | "
        f"**Confidence:** {conf_pct}%",
        "",
    ]

    if s.veto_triggered:
        lines.extend([
            f"> **VETO TRIGGERED** by Z Guardian: {s.veto_reason or 'Ethical red line crossed'}",
            "",
        ])

    lines.extend([
        "| Agent | Score | Role |",
        "|-------|-------|------|",
        f"| X Intelligent | {s.innovation_score:.1f}/10 | Innovation & Strategy |",
        f"| Z Guardian | {s.ethics_score:.1f}/10 | Ethics & Compliance |",
        f"| CS Security | {s.security_score:.1f}/10 | Security & Socratic Scrutiny |",
        "",
    ])

    return "\n".join(lines)


def _section_x_agent(x: XAgentAnalysis) -> str:
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
    conf_pct = int(cs.confidence * 100)

    lines = [
        f"## {cs.agent} — Security & Socratic Scrutiny",
        "",
        f"**Security Score:** {cs.security_score:.1f}/10 | "
        f"**Confidence:** {conf_pct}%",
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
