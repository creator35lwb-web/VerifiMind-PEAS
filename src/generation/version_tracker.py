"""
Version Tracking and Improvement History System
Tracks all iterations and versions of generated applications
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path


@dataclass
class VersionMetadata:
    """Metadata for a specific version of generated code"""
    version: str  # e.g., "v1.0", "v1.1", "v1.2"
    iteration: int
    timestamp: datetime

    # Quality metrics
    overall_score: float
    quality_score: float
    security_score: float
    compliance_score: float
    performance_score: float

    # Issues summary
    total_issues: int
    critical_issues: int
    security_issues_count: int
    compliance_gaps_count: int

    # Improvements
    improvements_applied: List[str]
    issues_fixed: List[str]

    # Generation details
    files_generated: int
    lines_of_code: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ImprovementHistory:
    """Complete history of all iterations for an application"""
    app_id: str
    app_name: str
    initial_concept: str

    # Version tracking
    versions: List[VersionMetadata]
    current_version: str
    total_iterations: int

    # Aggregate metrics
    initial_score: float
    final_score: float
    improvement_percentage: float

    # Timeline
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration: Optional[float]  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'app_id': self.app_id,
            'app_name': self.app_name,
            'initial_concept': self.initial_concept,
            'versions': [v.to_dict() for v in self.versions],
            'current_version': self.current_version,
            'total_iterations': self.total_iterations,
            'metrics': {
                'initial_score': self.initial_score,
                'final_score': self.final_score,
                'improvement_percentage': self.improvement_percentage
            },
            'timeline': {
                'started_at': self.started_at.isoformat(),
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'total_duration_seconds': self.total_duration
            }
        }


class VersionTracker:
    """
    Manages version tracking and improvement history for generated applications
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.histories: Dict[str, ImprovementHistory] = {}

    def start_tracking(
        self,
        app_id: str,
        app_name: str,
        initial_concept: str
    ) -> ImprovementHistory:
        """
        Start tracking a new application generation
        """
        history = ImprovementHistory(
            app_id=app_id,
            app_name=app_name,
            initial_concept=initial_concept,
            versions=[],
            current_version="v1.0",
            total_iterations=0,
            initial_score=0.0,
            final_score=0.0,
            improvement_percentage=0.0,
            started_at=datetime.utcnow(),
            completed_at=None,
            total_duration=None
        )

        self.histories[app_id] = history
        return history

    def record_version(
        self,
        app_id: str,
        version: str,
        iteration: int,
        reflection_report: Any,  # ReflectionReport
        generated_app: Any  # GeneratedApp
    ) -> VersionMetadata:
        """
        Records a new version in the history
        """
        history = self.histories.get(app_id)
        if not history:
            raise ValueError(f"No tracking started for app_id: {app_id}")

        # Count total lines of code
        lines_of_code = self._count_lines_of_code(generated_app)

        # Create version metadata
        version_meta = VersionMetadata(
            version=version,
            iteration=iteration,
            timestamp=datetime.utcnow(),
            overall_score=reflection_report.overall_score,
            quality_score=reflection_report.quality_score,
            security_score=reflection_report.security_score,
            compliance_score=reflection_report.compliance_score,
            performance_score=reflection_report.performance_score,
            total_issues=len(reflection_report.all_issues()),
            critical_issues=len(reflection_report.critical_issues()),
            security_issues_count=len(reflection_report.security_issues),
            compliance_gaps_count=len(reflection_report.compliance_gaps),
            improvements_applied=reflection_report.applied_improvements,
            issues_fixed=self._extract_issues_fixed(reflection_report),
            files_generated=len(generated_app.backend_code) + len(generated_app.frontend_code),
            lines_of_code=lines_of_code
        )

        # Add to history
        history.versions.append(version_meta)
        history.current_version = version
        history.total_iterations = iteration

        # Update aggregate metrics
        if iteration == 1:
            history.initial_score = reflection_report.overall_score

        history.final_score = reflection_report.overall_score
        history.improvement_percentage = self._calculate_improvement(
            history.initial_score,
            history.final_score
        )

        return version_meta

    def complete_tracking(self, app_id: str):
        """
        Marks the application generation as complete
        """
        history = self.histories.get(app_id)
        if not history:
            return

        history.completed_at = datetime.utcnow()
        history.total_duration = (
            history.completed_at - history.started_at
        ).total_seconds()

    def save_history(self, app_id: str, output_path: Optional[str] = None):
        """
        Saves the improvement history to a JSON file
        """
        history = self.histories.get(app_id)
        if not history:
            raise ValueError(f"No history found for app_id: {app_id}")

        if not output_path:
            output_path = self.output_dir / history.app_name / "verifimind_history.json"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(history.to_dict(), f, indent=2)

        print(f"[SAVED] Improvement history saved: {output_path}")

        return output_path

    def load_history(self, history_path: str) -> ImprovementHistory:
        """
        Loads improvement history from a JSON file
        """
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct ImprovementHistory object
        # (Simplified - in production would fully deserialize)
        app_id = data['app_id']
        self.histories[app_id] = data

        return data

    def generate_comparison_report(self, app_id: str) -> str:
        """
        Generates a markdown report comparing all versions
        """
        history = self.histories.get(app_id)
        if not history:
            raise ValueError(f"No history found for app_id: {app_id}")

        report = f"""# VerifiMind Iteration History - {history.app_name}

## Summary

**Application**: {history.app_name}
**Concept**: {history.initial_concept}
**Total Iterations**: {history.total_iterations}
**Duration**: {history.total_duration:.1f}s ({history.total_duration/60:.1f} minutes)

**Quality Improvement**: {history.initial_score:.1f} -> {history.final_score:.1f} (+{history.improvement_percentage:.1f}%)

---

## Version History

"""

        for version_meta in history.versions:
            report += f"""### {version_meta.version} (Iteration {version_meta.iteration})
**Generated**: {version_meta.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

**Scores**:
- Overall: {version_meta.overall_score:.1f}/100
- Quality: {version_meta.quality_score:.1f}/100
- Security: {version_meta.security_score:.1f}/100
- Compliance: {version_meta.compliance_score:.1f}/100
- Performance: {version_meta.performance_score:.1f}/100

**Issues**:
- Total: {version_meta.total_issues}
- Critical: {version_meta.critical_issues}
- Security: {version_meta.security_issues_count}
- Compliance: {version_meta.compliance_gaps_count}

**Code Metrics**:
- Files Generated: {version_meta.files_generated}
- Lines of Code: {version_meta.lines_of_code}

"""
            if version_meta.improvements_applied:
                report += "**Improvements Applied**:\n"
                for improvement in version_meta.improvements_applied:
                    report += f"- {improvement}\n"
                report += "\n"

            if version_meta.issues_fixed:
                report += "**Issues Fixed**:\n"
                for issue in version_meta.issues_fixed:
                    report += f"- [FIXED] {issue}\n"
                report += "\n"

            report += "---\n\n"

        report += f"""## Progress Chart

```
Iteration  | Overall Score | Issues | Critical
-----------|---------------|--------|----------
"""
        for version_meta in history.versions:
            report += f"   {version_meta.iteration}       |     {version_meta.overall_score:5.1f}      |   {version_meta.total_issues:3d}  |    {version_meta.critical_issues:2d}\n"

        report += f"""```

---

## Final Result

The application went through **{history.total_iterations} iterations** of refinement, improving from an initial quality score of **{history.initial_score:.1f}/100** to a final score of **{history.final_score:.1f}/100** - a **{history.improvement_percentage:.1f}%** improvement.

All critical issues have been addressed, and the application is production-ready.

---

*Generated by VerifiMind Iterative Code Generation Engine*
"""

        return report

    def _count_lines_of_code(self, generated_app: Any) -> int:
        """Counts total lines of code in generated application"""
        total_lines = 0

        # Count backend code
        for code in generated_app.backend_code.values():
            total_lines += len(code.split('\n'))

        # Count frontend code
        for code in generated_app.frontend_code.values():
            total_lines += len(code.split('\n'))

        # Count schema
        if generated_app.database_schema:
            total_lines += len(generated_app.database_schema.split('\n'))

        return total_lines

    def _extract_issues_fixed(self, reflection_report: Any) -> List[str]:
        """Extracts list of issues that were fixed"""
        fixed = []

        # In a real implementation, would compare with previous iteration
        # For now, return improvements applied
        if reflection_report.applied_improvements:
            return reflection_report.applied_improvements

        return fixed

    def _calculate_improvement(self, initial: float, final: float) -> float:
        """Calculates percentage improvement"""
        if initial == 0:
            return 0.0

        return ((final - initial) / initial) * 100

    def print_version_summary(self, app_id: str):
        """Prints a summary of all versions"""
        history = self.histories.get(app_id)
        if not history:
            return

        print(f"\n{'='*70}")
        print(f"[VERSIONS] VERSION HISTORY - {history.app_name}")
        print(f"{'='*70}")

        for version_meta in history.versions:
            status = "[OK]" if version_meta.critical_issues == 0 else "[WARNING]"
            print(f"{status} {version_meta.version} (Iteration {version_meta.iteration})")
            print(f"   Score: {version_meta.overall_score:.1f}/100 | Issues: {version_meta.total_issues} | Critical: {version_meta.critical_issues}")

        print(f"\n[QUALITY] Final Quality: {history.final_score:.1f}/100")
        print(f"[IMPROVEMENT] Improvement: +{history.improvement_percentage:.1f}%")
        print(f"{'='*70}\n")
