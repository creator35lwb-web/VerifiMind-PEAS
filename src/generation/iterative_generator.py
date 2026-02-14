"""
Iterative Code Generation Engine
Implements the RefleXion pattern - generate, reflect, improve, iterate
"""

from typing import Dict, List, Any, Optional
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.generation.core_generator import CodeGenerationEngine, AppSpecification, GeneratedApp
from src.agents.reflection_agent import ReflectionAgent, ReflectionReport
from src.generation.version_tracker import VersionTracker, ImprovementHistory
from pathlib import Path
import json


class IterativeCodeGenerationEngine:
    """
    Enhanced code generation engine with iterative improvement loop

    This implements the core "RefleXion" concept:
    1. Generate initial code
    2. Reflect on quality/security/compliance
    3. Identify improvements
    4. Regenerate with improvements
    5. Repeat until quality threshold met
    """

    def __init__(
        self,
        config: Dict[str, Any],
        llm_provider: Any,
        max_iterations: int = 3,
        quality_threshold: float = 85
    ):
        self.config = config
        self.llm_provider = llm_provider

        # Initialize generators
        self.code_generator = CodeGenerationEngine(config)
        self.reflection_agent = ReflectionAgent(
            agent_id="reflection-1",
            llm_provider=llm_provider,
            config={
                'max_iterations': max_iterations,
                'quality_threshold': quality_threshold
            }
        )
        self.version_tracker = VersionTracker()

        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold

    async def generate_with_iterations(
        self,
        spec: AppSpecification,
        output_dir: Optional[str] = None
    ) -> tuple[GeneratedApp, ImprovementHistory]:
        """
        Main entry point - generates application with iterative improvement

        Returns:
            (GeneratedApp, ImprovementHistory) - Final app and complete history
        """
        print(f"\n{'='*70}")
        print(f"[START] ITERATIVE CODE GENERATION - {spec.app_name}")
        print(f"{'='*70}")
        print(f"Max Iterations: {self.max_iterations}")
        print(f"Quality Threshold: {self.quality_threshold}/100")
        print(f"{'='*70}\n")

        # Start tracking
        history = self.version_tracker.start_tracking(
            app_id=spec.app_id,
            app_name=spec.app_name,
            initial_concept=spec.description
        )

        iteration = 0
        generated_app = None
        previous_report = None
        all_reports: List[ReflectionReport] = []

        # SAFEGUARD: Loop detection variables
        stuck_counter = 0
        score_history = []

        while iteration < self.max_iterations:
            iteration += 1

            print(f"\n{'-' * 70}")
            print(f"ITERATION {iteration}/{self.max_iterations}")
            print(f"{'-' * 70}\n")

            # STEP 1: Generate code (or regenerate with improvements)
            print(f"[STEP 1] Generating application code...")
            generated_app = await self.code_generator.generate_application(spec)

            # STEP 2: Reflect on generated code
            print(f"\n[STEP 2] Analyzing generated code...")
            reflection_report = await self.reflection_agent.analyze_generated_code(
                generated_app=generated_app,
                iteration=iteration,
                previous_report=previous_report
            )

            # STEP 3: Record this version
            self.version_tracker.record_version(
                app_id=spec.app_id,
                version=reflection_report.version,
                iteration=iteration,
                reflection_report=reflection_report,
                generated_app=generated_app
            )

            all_reports.append(reflection_report)
            score_history.append(reflection_report.overall_score)

            # STEP 4: Save this version to disk
            if output_dir:
                await self._save_version(
                    generated_app,
                    reflection_report,
                    output_dir,
                    spec.app_name
                )

            # SAFEGUARD 1: Check for stuck loop (no improvement)
            if len(score_history) >= 2:
                score_diff = score_history[-1] - score_history[-2]

                if abs(score_diff) < 1.0:  # Less than 1 point improvement
                    stuck_counter += 1
                    print(f"\n[WARNING] Minimal improvement detected ({score_diff:.1f} points)")

                    if stuck_counter >= 2:
                        print(f"\n[STOP] Iteration stuck - no meaningful improvement for {stuck_counter} iterations")
                        print(f"   Current score: {reflection_report.overall_score:.1f}/100")
                        print(f"   This is likely the best achievable quality with current approach.")
                        break
                else:
                    stuck_counter = 0  # Reset if we see improvement

            # SAFEGUARD 2: Check for score regression
            if len(score_history) >= 2 and score_history[-1] < score_history[-2]:
                print(f"\n[WARNING] Quality score decreased!")
                print(f"   Previous: {score_history[-2]:.1f}/100")
                print(f"   Current: {score_history[-1]:.1f}/100")
                print(f"   Consider using previous version instead.")

            # STEP 5: Check if we should iterate
            if not reflection_report.should_iterate:
                print(f"\n[OK] Quality threshold met at iteration {iteration}!")
                print(f"[COMPLETE] Final Score: {reflection_report.overall_score:.1f}/100")
                break

            # SAFEGUARD 3: Detect if same critical issues persist
            if iteration > 1 and previous_report:
                current_critical = len(reflection_report.critical_issues())
                previous_critical = len(previous_report.critical_issues())

                if current_critical > 0 and current_critical >= previous_critical:
                    print(f"\n[WARNING] Critical issues not being resolved!")
                    print(f"   Critical issues: {current_critical}")
                    print(f"   These may require manual intervention.")

            # STEP 6: Apply improvements to spec for next iteration
            if iteration < self.max_iterations:
                print(f"\n[STEP 6] Preparing improvements for next iteration...")
                spec = await self._apply_improvements_to_spec(
                    spec,
                    reflection_report
                )
                previous_report = reflection_report

                # Brief pause for readability
                await asyncio.sleep(0.5)
            else:
                print(f"\n[MAX] Reached maximum iterations ({self.max_iterations})")
                print(f"[SCORE] Final Score: {reflection_report.overall_score:.1f}/100")

        # Complete tracking
        self.version_tracker.complete_tracking(spec.app_id)

        # Print final summary
        self._print_final_summary(history, all_reports)

        # Save improvement history
        if output_dir:
            self.version_tracker.save_history(
                spec.app_id,
                f"{output_dir}/{spec.app_name}/verifimind_history.json"
            )

            # Save comparison report
            comparison_report = self.version_tracker.generate_comparison_report(spec.app_id)
            report_path = Path(output_dir) / spec.app_name / "ITERATION_HISTORY.md"
            report_path.write_text(comparison_report, encoding='utf-8')
            print(f"[SAVED] Iteration report saved: {report_path}")

        return generated_app, history

    async def _save_version(
        self,
        generated_app: GeneratedApp,
        reflection_report: ReflectionReport,
        output_dir: str,
        app_name: str
    ):
        """
        Saves a specific version of the generated app to disk
        """
        version = reflection_report.version
        version_dir = Path(output_dir) / app_name / f"versions/{version}"
        version_dir.mkdir(parents=True, exist_ok=True)

        print(f"[SAVE] Saving {version} to {version_dir}")

        # Save backend code
        for file_path, code in generated_app.backend_code.items():
            full_path = version_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(code, encoding='utf-8')

        # Save frontend code
        for file_path, code in generated_app.frontend_code.items():
            full_path = version_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(code, encoding='utf-8')

        # Save database schema
        schema_path = version_dir / "database/schema.sql"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(generated_app.database_schema, encoding='utf-8')

        # Save documentation
        (version_dir / "README.md").write_text(generated_app.readme, encoding='utf-8')
        docs_dir = version_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "API.md").write_text(generated_app.api_docs, encoding='utf-8')
        (docs_dir / "USER_GUIDE.md").write_text(generated_app.user_guide, encoding='utf-8')

        # Save reflection report
        report_path = version_dir / f"REFLECTION_REPORT_{version}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(reflection_report.to_dict(), f, indent=2)

        print(f"[OK] {version} saved successfully")

    async def _apply_improvements_to_spec(
        self,
        spec: AppSpecification,
        reflection_report: ReflectionReport
    ) -> AppSpecification:
        """
        Applies improvements from reflection report to specification for next iteration

        This is where the magic happens - we take the identified issues and
        modify the spec to address them in the next generation
        """
        print(f"[APPLY] Applying {len(reflection_report.improvement_suggestions)} improvements to spec...")

        # Copy spec for modification
        improved_spec = spec

        # Security improvements
        if reflection_report.security_issues:
            # Add security features to spec
            for issue in reflection_report.security_issues:
                if 'authentication' in issue.description.lower():
                    # Ensure auth is required
                    if 'authentication' not in improved_spec.security_features:
                        improved_spec.security_features.append('strict_authentication')

                if 'password' in issue.description.lower():
                    if 'password_hashing' not in improved_spec.security_features:
                        improved_spec.security_features.append('bcrypt_password_hashing')

                if 'sql injection' in issue.description.lower():
                    if 'parameterized_queries' not in improved_spec.security_features:
                        improved_spec.security_features.append('parameterized_queries')

        # Compliance improvements
        if reflection_report.compliance_gaps:
            for gap in reflection_report.compliance_gaps:
                if 'gdpr' in gap.description.lower():
                    if 'gdpr_compliance' not in improved_spec.compliance_features:
                        improved_spec.compliance_features.append('gdpr_data_export')
                        improved_spec.compliance_features.append('gdpr_data_deletion')
                        improved_spec.compliance_features.append('gdpr_consent')

                if 'audit' in gap.description.lower():
                    if 'audit_logging' not in improved_spec.compliance_features:
                        improved_spec.compliance_features.append('audit_logging')

        # Performance improvements
        if reflection_report.performance_issues:
            for issue in reflection_report.performance_issues:
                if 'index' in issue.description.lower():
                    # Add note to database entities to ensure indexes
                    for entity in improved_spec.database_entities:
                        for field in entity.get('fields', []):
                            if field.get('foreign_key'):
                                field['indexed'] = True

                if 'pagination' in issue.description.lower():
                    # Add pagination to API endpoints
                    for endpoint in improved_spec.api_endpoints:
                        if endpoint['method'] == 'GET' and '/all' in endpoint['path']:
                            endpoint['pagination'] = True

        # Quality improvements
        if reflection_report.quality_issues:
            # Add metadata to track improvements
            if 'metadata' not in improved_spec.metadata:
                improved_spec.metadata['improvements'] = []

            improved_spec.metadata['improvements'].extend(
                reflection_report.improvement_suggestions[:5]
            )

        print(f"[OK] Improvements applied to spec")
        return improved_spec

    def _print_final_summary(
        self,
        history: ImprovementHistory,
        reports: List[ReflectionReport]
    ):
        """
        Prints a beautiful final summary of the iteration process
        """
        print(f"\n{'='*70}")
        print(f"[COMPLETE] ITERATION COMPLETE - FINAL SUMMARY")
        print(f"{'='*70}")

        print(f"\n[PROGRESS] Overall Progress:")
        print(f"   Total Iterations: {history.total_iterations}")
        print(f"   Duration: {history.total_duration:.1f}s ({history.total_duration/60:.1f} min)")
        print(f"   Initial Score: {history.initial_score:.1f}/100")
        print(f"   Final Score: {history.final_score:.1f}/100")
        print(f"   Improvement: +{history.improvement_percentage:.1f}%")

        print(f"\n[EVOLUTION] Score Evolution:")
        for report in reports:
            marker = "[+]" if report.overall_score >= self.quality_threshold else "[-]"
            print(f"   {marker} {report.version}: {report.overall_score:.1f}/100 "
                  f"({len(report.all_issues())} issues, {len(report.critical_issues())} critical)")

        print(f"\n[METRICS] Final Quality Metrics:")
        final_report = reports[-1]
        print(f"   Overall:     {final_report.overall_score:.1f}/100")
        print(f"   Quality:     {final_report.quality_score:.1f}/100")
        print(f"   Security:    {final_report.security_score:.1f}/100")
        print(f"   Compliance:  {final_report.compliance_score:.1f}/100")
        print(f"   Performance: {final_report.performance_score:.1f}/100")

        print(f"\n[STATUS] Application Status:")
        if final_report.overall_score >= self.quality_threshold:
            print(f"   [OK] PRODUCTION READY - Quality threshold met!")
        else:
            print(f"   [REVIEW] NEEDS REVIEW - Below quality threshold")
            print(f"   Remaining issues: {len(final_report.all_issues())}")
            if final_report.critical_issues():
                print(f"   [WARNING] Critical issues: {len(final_report.critical_issues())}")

        print(f"\n[ACHIEVEMENTS] Key Achievements:")
        total_issues_fixed = sum(len(r.all_issues()) for r in reports[:-1]) - len(final_report.all_issues())
        if total_issues_fixed > 0:
            print(f"   * Fixed {total_issues_fixed} issues through iterations")

        critical_fixed = sum(len(r.critical_issues()) for r in reports[:-1]) - len(final_report.critical_issues())
        if critical_fixed > 0:
            print(f"   * Resolved {critical_fixed} critical issues")

        if history.improvement_percentage > 0:
            print(f"   * Improved overall quality by {history.improvement_percentage:.1f}%")

        print(f"\n{'='*70}")
        print(f"[DONE] Code generation complete! Check the output directory for all versions.")
        print(f"{'='*70}\n")

    def get_version_history(self, app_id: str) -> Optional[ImprovementHistory]:
        """Returns the improvement history for an application"""
        return self.version_tracker.histories.get(app_id)

    def print_version_summary(self, app_id: str):
        """Prints version summary"""
        self.version_tracker.print_version_summary(app_id)
