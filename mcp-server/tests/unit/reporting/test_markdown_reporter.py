"""
Unit tests for Markdown report generation.
"""

from datetime import datetime, timezone

from verifimind_mcp.models.reasoning import (
    ReasoningStep,
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
)
from verifimind_mcp.models.results import TrinityResult, TrinitySynthesis
from verifimind_mcp.reporting.markdown_reporter import (
    generate_yaml_frontmatter,
    generate_markdown_summary,
    generate_markdown_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_steps(n: int = 2) -> list:
    return [
        ReasoningStep(
            step_number=i + 1,
            thought=f"Reasoning step {i + 1}",
            evidence=f"Evidence for step {i + 1}" if i == 0 else None,
            confidence=0.8 + i * 0.05,
        )
        for i in range(n)
    ]


def _make_trinity_result(
    veto: bool = False,
    recommendation: str = "proceed_with_caution",
) -> TrinityResult:
    x = XAgentAnalysis(
        reasoning_steps=_make_steps(),
        innovation_score=8.1,
        strategic_value=7.5,
        opportunities=["Large market", "First-mover advantage"],
        risks=["Regulatory uncertainty"],
        recommendation="Proceed with pilot",
        confidence=0.85,
    )
    z = ZAgentAnalysis(
        reasoning_steps=_make_steps(),
        ethics_score=6.8,
        z_protocol_compliance=not veto,
        ethical_concerns=["Bias in training data", "Privacy risks"],
        mitigation_measures=["Regular audits", "Data anonymization"],
        recommendation="Proceed with safeguards" if not veto else "Reject",
        veto_triggered=veto,
        confidence=0.78,
    )
    cs = CSAgentAnalysis(
        reasoning_steps=_make_steps(),
        security_score=6.9,
        vulnerabilities=["SQL injection in API", "XSS in dashboard"],
        attack_vectors=["API abuse"],
        security_recommendations=["Input validation", "WAF deployment"],
        socratic_questions=["What happens if the model is adversarially attacked?",
                           "How is data lineage tracked?"],
        recommendation="Proceed after security hardening",
        confidence=0.80,
    )
    synthesis = TrinitySynthesis(
        summary="The concept has strong innovation potential but requires ethical and security safeguards.",
        innovation_score=8.1,
        ethics_score=6.8,
        security_score=6.9,
        overall_score=7.2,
        strengths=["Strong market fit", "Novel approach"],
        concerns=["Bias risk", "Regulatory gaps"],
        recommendations=["Implement bias auditing", "Engage legal counsel"],
        recommendation=recommendation,
        confidence=0.82,
        veto_triggered=veto,
        veto_reason="Ethical red line: consent violation" if veto else None,
    )
    started = datetime(2026, 2, 14, 8, 0, 0, tzinfo=timezone.utc)
    completed = datetime(2026, 2, 14, 8, 0, 12, tzinfo=timezone.utc)
    return TrinityResult(
        validation_id="abc12345",
        concept_name="AI-Powered Fraud Detection",
        concept_description="Real-time fraud detection using ML for banking.",
        x_analysis=x,
        z_analysis=z,
        cs_analysis=cs,
        synthesis=synthesis,
        started_at=started,
        completed_at=completed,
    )


# ---------------------------------------------------------------------------
# Tests: YAML frontmatter
# ---------------------------------------------------------------------------

class TestYAMLFrontmatter:

    def test_contains_delimiters(self):
        result = _make_trinity_result()
        fm = generate_yaml_frontmatter(result)
        assert fm.startswith("---\n")
        assert fm.endswith("\n---")

    def test_contains_validation_id(self):
        result = _make_trinity_result()
        fm = generate_yaml_frontmatter(result)
        assert "validation_id: abc12345" in fm

    def test_contains_scores(self):
        result = _make_trinity_result()
        fm = generate_yaml_frontmatter(result)
        assert "overall_score: 7.2" in fm
        assert "innovation_score: 8.1" in fm
        assert "ethics_score: 6.8" in fm
        assert "security_score: 6.9" in fm

    def test_contains_recommendation(self):
        result = _make_trinity_result()
        fm = generate_yaml_frontmatter(result)
        assert "recommendation: proceed_with_caution" in fm

    def test_veto_false(self):
        result = _make_trinity_result(veto=False)
        fm = generate_yaml_frontmatter(result)
        assert "veto_triggered: false" in fm

    def test_veto_true(self):
        result = _make_trinity_result(veto=True, recommendation="reject")
        fm = generate_yaml_frontmatter(result)
        assert "veto_triggered: true" in fm

    def test_contains_generator(self):
        result = _make_trinity_result()
        fm = generate_yaml_frontmatter(result)
        assert "generator: verifimind-peas/" in fm
        assert "format: markdown-first/1.0" in fm

    def test_concept_with_quotes_escaped(self):
        result = _make_trinity_result()
        result.concept_name = 'Concept with "quotes"'
        fm = generate_yaml_frontmatter(result)
        assert r'concept: "Concept with \"quotes\""' in fm


# ---------------------------------------------------------------------------
# Tests: Markdown summary
# ---------------------------------------------------------------------------

class TestMarkdownSummary:

    def test_contains_title(self):
        result = _make_trinity_result()
        md = generate_markdown_summary(result)
        assert "# Trinity Validation: AI-Powered Fraud Detection" in md

    def test_contains_recommendation(self):
        result = _make_trinity_result()
        md = generate_markdown_summary(result)
        assert "PROCEED WITH CAUTION" in md

    def test_contains_score_table(self):
        result = _make_trinity_result()
        md = generate_markdown_summary(result)
        assert "| X Intelligent | 8.1/10" in md
        assert "| Z Guardian | 6.8/10" in md
        assert "| CS Security | 6.9/10" in md

    def test_veto_warning_shown(self):
        result = _make_trinity_result(veto=True, recommendation="reject")
        md = generate_markdown_summary(result)
        assert "VETO TRIGGERED" in md

    def test_no_veto_warning_when_not_triggered(self):
        result = _make_trinity_result(veto=False)
        md = generate_markdown_summary(result)
        assert "VETO TRIGGERED" not in md

    def test_contains_validation_id(self):
        result = _make_trinity_result()
        md = generate_markdown_summary(result)
        assert "abc12345" in md


# ---------------------------------------------------------------------------
# Tests: Full report
# ---------------------------------------------------------------------------

class TestFullReport:

    def test_starts_with_frontmatter(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert report.startswith("---\n")

    def test_contains_all_sections(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "## Executive Summary" in report
        assert "## X Intelligent" in report
        assert "## Z Guardian" in report
        assert "## CS Security" in report
        assert "## Strengths" in report
        assert "## Concerns" in report
        assert "## Recommendations" in report

    def test_contains_reasoning_chains(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "### Reasoning Chain" in report
        assert "Reasoning step 1" in report

    def test_contains_evidence(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "Evidence for step 1" in report

    def test_contains_opportunities_and_risks(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "### Opportunities" in report
        assert "Large market" in report
        assert "### Risks" in report
        assert "Regulatory uncertainty" in report

    def test_contains_vulnerabilities(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "### Vulnerabilities" in report
        assert "SQL injection in API" in report

    def test_contains_socratic_questions(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "### Socratic Questions" in report
        assert "adversarially attacked" in report

    def test_contains_footer(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "Human decision required" in report
        assert "abc12345" in report

    def test_duration_in_footer(self):
        result = _make_trinity_result()
        report = generate_markdown_report(result)
        assert "Duration: 12.0s" in report

    def test_veto_report(self):
        result = _make_trinity_result(veto=True, recommendation="reject")
        report = generate_markdown_report(result)
        assert "VETO TRIGGERED" in report
        assert "consent violation" in report

    def test_empty_lists_handled(self):
        result = _make_trinity_result()
        result.x_analysis.opportunities = []
        result.x_analysis.risks = []
        report = generate_markdown_report(result)
        assert "### Opportunities" not in report
        assert "### Risks" not in report
