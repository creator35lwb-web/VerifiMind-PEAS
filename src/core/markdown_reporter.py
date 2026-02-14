"""
VerifiMind PEAS - Markdown Report Generator v1.0
Markdown-first strategic pivot — February 2026

Generates structured Markdown validation reports with YAML frontmatter,
replacing PDF as the primary output format. PDF is retained as an
optional secondary export via pdf_generator.py.

Same interface as pdf_generator.ValidationReportGenerator for
drop-in replacement in verifimind_complete.py.
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ValidationReportGenerator:
    """Generates Markdown validation reports from Trinity agent results.

    Drop-in replacement for the PDF-based ValidationReportGenerator.
    Same ``generate()`` signature and return type (file path string).
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API (same contract as pdf_generator)
    # ------------------------------------------------------------------

    def generate(
        self,
        app_spec: Any,
        agent_results: Dict[str, Any],
        socratic_data: Dict[str, Any],
    ) -> str:
        """Generate a Markdown validation report and save to disk.

        Args:
            app_spec: Object or dict with app_name, app_id, category, description.
            agent_results: Dict keyed by agent name ('X', 'Z', 'CS') with analysis results.
            socratic_data: Dict with clarification, feasibility, challenges, security_scan, strategy.

        Returns:
            Path to the saved ``.md`` file.
        """
        app_name = self._safe_get(app_spec, "app_name", "Untitled")
        app_id = self._safe_get(app_spec, "app_id", "N/A")
        category = self._safe_get(app_spec, "category", "General")
        description = self._safe_get(app_spec, "description", "")

        now = datetime.now(timezone.utc)
        lines: list[str] = []

        # --- YAML frontmatter ---
        lines.append("---")
        lines.append(f"app_name: \"{self._escape_yaml(app_name)}\"")
        lines.append(f"app_id: {app_id}")
        lines.append(f"category: {category}")
        lines.append(f"generated: {now.isoformat()}")
        lines.append(f"generator: verifimind-peas/legacy")
        lines.append(f"format: markdown-first/1.0")
        lines.append("---")
        lines.append("")

        # --- Title ---
        lines.append(f"# Genesis Validation Report: {app_name}")
        lines.append("")
        lines.append(f"**Category:** {category}  ")
        lines.append(f"**Generated:** {now.strftime('%B %d, %Y %H:%M UTC')}")
        lines.append("")
        if description:
            lines.append(f"> {description[:500]}")
            lines.append("")

        # --- Section 1: Executive Summary ---
        lines.extend(self._trinity_matrix(agent_results))

        # --- Section 2: Socratic Concept Scrutiny ---
        lines.extend(self._socratic_section(socratic_data))

        # --- Section 3: Security Analysis ---
        lines.extend(self._security_section(socratic_data))

        # --- Section 4: Strategic Roadmap ---
        lines.extend(self._roadmap_section(socratic_data))

        # --- Section 5: IP & Attribution ---
        lines.extend(self._ip_proof(app_id, now))

        # --- Footer ---
        lines.append("---")
        lines.append("*This report is advisory only. Human decision required.*")

        content = "\n".join(lines)
        filepath = self._save(app_name, content)
        logger.info(f"Markdown report saved: {filepath}")
        return filepath

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _trinity_matrix(self, agent_results: Dict[str, Any]) -> list[str]:
        agents = [
            ("X Intelligent", "Innovation Engine", "X", "risk_score"),
            ("Z Guardian", "Ethics & Compliance", "Z", "risk_score"),
            ("CS Security", "Vulnerability Scan", "CS", "validation_score"),
        ]
        lines = ["## 1. Executive Summary: The Trinity Verdict", ""]
        lines.append("| Agent | Role | Status | Score |")
        lines.append("|-------|------|--------|-------|")

        for name, role, key, score_field in agents:
            result = agent_results.get(key, {})
            if result is None:
                result = {}
            status = self._safe_get(result, "status", "N/A")
            score = self._safe_get(result, score_field, "N/A")
            if isinstance(score, (int, float)):
                score = f"{score}/100"
            lines.append(f"| {name} | {role} | {status} | {score} |")

        lines.append("")

        for name, _, key, _ in agents:
            result = agent_results.get(key, {})
            if result is None:
                continue
            analysis = self._safe_get(result, "analysis", "")
            verdict = self._safe_get(result, "verdict", "")
            if analysis or verdict:
                lines.append(f"**{name}:** {(analysis or '')[:400]}")
                if verdict:
                    lines.append(f"  *Verdict: {verdict}*")
                lines.append("")

        return lines

    def _socratic_section(self, socratic_data: Dict[str, Any]) -> list[str]:
        lines = ["## 2. Socratic Concept Scrutiny", ""]
        clarification = socratic_data.get("clarification", "")
        if clarification:
            lines.append("### Clarification & Assumptions")
            lines.append("")
            lines.append(clarification)
            lines.append("")

        feasibility = socratic_data.get("feasibility", {})
        if feasibility:
            lines.append("### Feasibility Scores")
            lines.append("")
            for key in ["innovation_score", "tech_feasibility_score", "market_score", "risk_score"]:
                val = feasibility.get(key)
                if val is not None:
                    label = key.replace("_", " ").title()
                    lines.append(f"- **{label}:** {val}/100")
            lines.append("")

        challenges = socratic_data.get("challenges", [])
        if challenges:
            lines.append("### Socratic Challenges")
            lines.append("")
            for i, q in enumerate(challenges[:5], 1):
                lines.append(f"{i}. {q}")
            lines.append("")

        return lines

    def _security_section(self, socratic_data: Dict[str, Any]) -> list[str]:
        scan = socratic_data.get("security_scan", {})
        if not scan:
            return []

        lines = ["## 3. Security Analysis", ""]

        threats = scan.get("threats", [])
        if threats:
            lines.append("### Identified Threats")
            lines.append("")
            for t in threats[:5]:
                lines.append(f"- {t}")
            lines.append("")

        mitigations = scan.get("mitigations", [])
        if mitigations:
            lines.append("### Recommended Mitigations")
            lines.append("")
            for m in mitigations[:5]:
                lines.append(f"- {m}")
            lines.append("")

        gaps = scan.get("compliance_gaps", [])
        if gaps:
            lines.append("### Compliance Gaps")
            lines.append("")
            for g in gaps[:5]:
                lines.append(f"- {g}")
            lines.append("")

        return lines

    def _roadmap_section(self, socratic_data: Dict[str, Any]) -> list[str]:
        strategy = socratic_data.get("strategy", {})
        if not strategy:
            return []

        lines = ["## 4. Strategic Roadmap", ""]

        verdict = strategy.get("verdict", "")
        if verdict:
            lines.append(f"**Strategic Verdict:** {verdict}")
            lines.append("")

        reason = strategy.get("verdict_reason", "")
        if reason:
            lines.append(f"> {reason}")
            lines.append("")

        options = strategy.get("strategic_options", [])
        if options:
            lines.append("### Strategic Options")
            lines.append("")
            for i, opt in enumerate(options[:3], 1):
                lines.append(f"{i}. {opt}")
            lines.append("")

        milestones = strategy.get("roadmap_milestones", [])
        if milestones:
            lines.append("### Roadmap Milestones")
            lines.append("")
            for m in milestones[:5]:
                lines.append(f"- [ ] {m}")
            lines.append("")

        return lines

    def _ip_proof(self, app_id: str, now: datetime) -> list[str]:
        return [
            "## 5. IP & Attribution Proof",
            "",
            f"- **App ID:** {app_id}",
            f"- **Timestamp (UTC):** {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "- **Methodology:** Genesis Prompt Engineering v2.0",
            "- **Framework:** VerifiMind PEAS X-Z-CS Trinity",
            "- **License:** Proprietary / Creator Owned",
            "- **White Paper:** DOI 10.5281/zenodo.17645665",
            "",
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_get(self, obj: Any, attr: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def _escape_yaml(self, text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')

    def _save(self, app_name: str, content: str) -> str:
        safe_name = re.sub(r"[^\w\s-]", "", app_name).strip().replace(" ", "_")[:50]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_Validation_Report_{ts}.md"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


def generate_report(
    app_spec: Any,
    agent_results: Dict[str, Any],
    socratic_data: Dict[str, Any],
    output_dir: str = "output",
) -> str:
    """Convenience function — same as pdf_generator.generate_report."""
    gen = ValidationReportGenerator(output_dir=output_dir)
    return gen.generate(app_spec, agent_results, socratic_data)
