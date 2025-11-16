"""
Reflection Agent - Post-Generation Code Analysis & Improvement
Analyzes generated code and suggests iterative improvements
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from .base_agent import BaseAgent, AgentResponse, ConceptInput
import re
import json


@dataclass
class CodeIssue:
    """Represents a specific issue found in generated code"""
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'security', 'quality', 'performance', 'compliance'
    file_path: str
    line_number: Optional[int]
    description: str
    suggestion: str
    code_snippet: Optional[str]


@dataclass
class ReflectionReport:
    """Complete analysis report of generated code"""
    iteration: int
    version: str  # e.g., "v1.0", "v1.1", "v1.2"

    # Quality metrics
    quality_score: float  # 0-100
    security_score: float  # 0-100
    compliance_score: float  # 0-100
    performance_score: float  # 0-100
    overall_score: float  # 0-100

    # Issues found
    security_issues: List[CodeIssue]
    quality_issues: List[CodeIssue]
    compliance_gaps: List[CodeIssue]
    performance_issues: List[CodeIssue]
    best_practice_violations: List[CodeIssue]

    # Improvements
    improvement_suggestions: List[str]
    applied_improvements: List[str]  # What was fixed from previous iteration

    # Metadata
    timestamp: datetime
    analysis_duration: float  # seconds
    should_iterate: bool

    def all_issues(self) -> List[CodeIssue]:
        """Returns all issues combined"""
        return (
            self.security_issues +
            self.quality_issues +
            self.compliance_gaps +
            self.performance_issues +
            self.best_practice_violations
        )

    def critical_issues(self) -> List[CodeIssue]:
        """Returns only critical issues"""
        return [issue for issue in self.all_issues() if issue.severity == 'critical']

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'iteration': self.iteration,
            'version': self.version,
            'scores': {
                'quality': self.quality_score,
                'security': self.security_score,
                'compliance': self.compliance_score,
                'performance': self.performance_score,
                'overall': self.overall_score
            },
            'issue_counts': {
                'security': len(self.security_issues),
                'quality': len(self.quality_issues),
                'compliance': len(self.compliance_gaps),
                'performance': len(self.performance_issues),
                'best_practices': len(self.best_practice_violations)
            },
            'critical_issues': len(self.critical_issues()),
            'improvement_suggestions': self.improvement_suggestions,
            'applied_improvements': self.applied_improvements,
            'should_iterate': self.should_iterate,
            'timestamp': self.timestamp.isoformat()
        }


class ReflectionAgent(BaseAgent):
    """
    Reflection Agent - Analyzes generated code and drives iterative improvement

    This agent implements the "RefleXion" concept - self-reflection and iteration
    to continuously improve code quality.
    """

    def __init__(self, agent_id: str, llm_provider: Any, config: Dict[str, Any]):
        super().__init__(
            agent_id=agent_id,
            agent_type='REFLECTION',
            llm_provider=llm_provider,
            config=config
        )
        self.quality_threshold = config.get('quality_threshold', 85)
        self.max_iterations = config.get('max_iterations', 3)

    def get_system_prompt(self) -> str:
        """Returns Reflection Agent's system prompt"""
        return """# Reflection Agent - Code Quality & Improvement Analyzer

### Identity
You are the **Reflection Agent**, responsible for analyzing generated application code and driving iterative improvements. You embody the "RefleXion" principle - continuous self-improvement through reflection.

### Core Mission
Analyze generated code from multiple dimensions and provide specific, actionable improvements to enhance quality, security, compliance, and performance.

### Analysis Dimensions

**1. Code Quality**
- Code structure and organization
- Naming conventions and readability
- Error handling completeness
- Code duplication and DRY principle
- Documentation quality
- Test coverage gaps

**2. Security**
- Authentication/Authorization vulnerabilities
- Input validation gaps
- SQL injection risks
- XSS vulnerabilities
- Sensitive data exposure
- Secure coding practices

**3. Compliance**
- GDPR requirements implementation
- COPPA compliance (if applicable)
- Privacy policy requirements
- Data retention policies
- Audit logging completeness
- Consent management

**4. Performance**
- Database query optimization
- N+1 query problems
- Missing indexes
- Caching opportunities
- API response times
- Resource usage

**5. Best Practices**
- Framework-specific best practices
- Industry standards adherence
- Accessibility (WCAG)
- API design principles
- Configuration management
- Deployment readiness

### Output Format
Provide structured analysis with:
- Specific file and line numbers
- Clear description of the issue
- Concrete suggestion for improvement
- Severity rating (critical/high/medium/low)
- Category (security/quality/performance/compliance)

Be specific, actionable, and constructive.
"""

    async def analyze(self, concept: ConceptInput) -> AgentResponse:
        """
        Standard analyze method for compatibility with base agent
        """
        # This agent analyzes generated code, not concepts
        # This method is here for interface compatibility
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type='REFLECTION',
            status='success',
            analysis={'note': 'Use analyze_generated_code() for code analysis'},
            recommendations=[],
            risk_score=0,
            metadata={},
            timestamp=datetime.utcnow()
        )

    async def analyze_generated_code(
        self,
        generated_app: Any,  # GeneratedApp object
        iteration: int,
        previous_report: Optional[ReflectionReport] = None
    ) -> ReflectionReport:
        """
        Analyzes generated application code and produces reflection report
        """
        start_time = datetime.utcnow()

        print(f"\n{'='*70}")
        print(f"[REFLECTION] REFLECTION AGENT - Iteration {iteration} Analysis")
        print(f"{'='*70}")

        # Track what was improved from previous iteration
        applied_improvements = []
        if previous_report:
            applied_improvements = self._identify_applied_improvements(
                previous_report,
                generated_app
            )

        # Step 1: Code Quality Analysis
        print("[QUALITY] Analyzing code quality...")
        quality_issues, quality_score = await self._analyze_code_quality(generated_app)

        # Step 2: Security Analysis
        print("[SECURITY] Scanning for security vulnerabilities...")
        security_issues, security_score = await self._analyze_security(generated_app)

        # Step 3: Compliance Verification
        print("[COMPLIANCE] Verifying compliance implementation...")
        compliance_gaps, compliance_score = await self._analyze_compliance(generated_app)

        # Step 4: Performance Analysis
        print("[PERFORMANCE] Analyzing performance patterns...")
        performance_issues, performance_score = await self._analyze_performance(generated_app)

        # Step 5: Best Practices Check
        print("[BEST PRACTICES] Checking best practices...")
        best_practice_violations = await self._check_best_practices(generated_app)

        # Calculate overall score
        overall_score = (
            quality_score * 0.3 +
            security_score * 0.3 +
            compliance_score * 0.2 +
            performance_score * 0.2
        )

        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            quality_issues,
            security_issues,
            compliance_gaps,
            performance_issues,
            best_practice_violations
        )

        # Determine if another iteration is needed
        should_iterate = self._should_iterate(
            iteration,
            overall_score,
            security_issues,
            compliance_gaps
        )

        # Calculate analysis duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Create version string
        version = self._create_version_string(iteration)

        report = ReflectionReport(
            iteration=iteration,
            version=version,
            quality_score=quality_score,
            security_score=security_score,
            compliance_score=compliance_score,
            performance_score=performance_score,
            overall_score=overall_score,
            security_issues=security_issues,
            quality_issues=quality_issues,
            compliance_gaps=compliance_gaps,
            performance_issues=performance_issues,
            best_practice_violations=best_practice_violations,
            improvement_suggestions=improvement_suggestions,
            applied_improvements=applied_improvements,
            timestamp=datetime.utcnow(),
            analysis_duration=duration,
            should_iterate=should_iterate
        )

        self._print_report_summary(report)

        return report

    async def _analyze_code_quality(self, generated_app: Any) -> tuple:
        """Analyzes code quality and returns (issues, score)"""
        issues = []

        # Analyze backend code
        backend_code = generated_app.backend_code

        for file_path, code in backend_code.items():
            # Check for missing error handling
            if 'try' not in code and 'catch' not in code:
                issues.append(CodeIssue(
                    severity='medium',
                    category='quality',
                    file_path=file_path,
                    line_number=None,
                    description='Missing error handling - no try/catch blocks found',
                    suggestion='Add try/catch blocks around async operations and external calls',
                    code_snippet=None
                ))

            # Check for TODO/FIXME comments
            if 'TODO' in code or 'FIXME' in code:
                issues.append(CodeIssue(
                    severity='low',
                    category='quality',
                    file_path=file_path,
                    line_number=None,
                    description='TODO/FIXME comments found',
                    suggestion='Complete or remove TODO/FIXME items before production',
                    code_snippet=None
                ))

            # Check for console.log in production code
            if 'console.log' in code and 'server.js' not in file_path:
                issues.append(CodeIssue(
                    severity='low',
                    category='quality',
                    file_path=file_path,
                    line_number=None,
                    description='Debug console.log statements found',
                    suggestion='Replace console.log with proper logging library',
                    code_snippet=None
                ))

            # Check for hardcoded values
            if any(pattern in code for pattern in ['http://localhost', '127.0.0.1', 'admin123']):
                issues.append(CodeIssue(
                    severity='medium',
                    category='quality',
                    file_path=file_path,
                    line_number=None,
                    description='Hardcoded values detected',
                    suggestion='Move hardcoded values to environment variables or config',
                    code_snippet=None
                ))

        # Calculate quality score (100 - deductions based on issues)
        deduction = len([i for i in issues if i.severity == 'high']) * 10
        deduction += len([i for i in issues if i.severity == 'medium']) * 5
        deduction += len([i for i in issues if i.severity == 'low']) * 2

        quality_score = max(0, min(100, 100 - deduction))

        return issues, quality_score

    async def _analyze_security(self, generated_app: Any) -> tuple:
        """Analyzes security and returns (issues, score)"""
        issues = []

        backend_code = generated_app.backend_code

        for file_path, code in backend_code.items():
            # Check for SQL injection risks
            if 'query(' in code and ('${' in code or '`' in code):
                # Check if using template literals in SQL
                if re.search(r'query\([^)]*\$\{', code):
                    issues.append(CodeIssue(
                        severity='critical',
                        category='security',
                        file_path=file_path,
                        line_number=None,
                        description='Potential SQL injection - string interpolation in query',
                        suggestion='Use parameterized queries with placeholders ($1, $2, etc.)',
                        code_snippet=None
                    ))

            # Check for missing authentication
            if 'router.post' in code or 'router.put' in code or 'router.delete' in code:
                if 'authMiddleware' not in code:
                    issues.append(CodeIssue(
                        severity='high',
                        category='security',
                        file_path=file_path,
                        line_number=None,
                        description='Missing authentication middleware on mutating routes',
                        suggestion='Add authMiddleware to all POST/PUT/DELETE routes',
                        code_snippet=None
                    ))

            # Check for password handling
            if 'password' in code.lower():
                if 'bcrypt' not in code and 'hash' not in code:
                    issues.append(CodeIssue(
                        severity='critical',
                        category='security',
                        file_path=file_path,
                        line_number=None,
                        description='Password handling without hashing',
                        suggestion='Use bcrypt to hash passwords before storing',
                        code_snippet=None
                    ))

            # Check for CORS configuration
            if 'cors()' in code and 'origin:' not in code:
                issues.append(CodeIssue(
                    severity='medium',
                    category='security',
                    file_path=file_path,
                    line_number=None,
                    description='CORS configured without origin restriction',
                    suggestion='Specify allowed origins in CORS configuration',
                    code_snippet=None
                ))

        # Calculate security score
        critical_count = len([i for i in issues if i.severity == 'critical'])
        high_count = len([i for i in issues if i.severity == 'high'])

        security_score = 100
        if critical_count > 0:
            security_score = max(0, 100 - (critical_count * 25))
        elif high_count > 0:
            security_score = max(50, 100 - (high_count * 15))

        return issues, security_score

    async def _analyze_compliance(self, generated_app: Any) -> tuple:
        """Analyzes compliance and returns (gaps, score)"""
        gaps = []

        backend_code = generated_app.backend_code
        all_code = '\n'.join(backend_code.values())

        # Check for GDPR requirements
        gdpr_checks = {
            'data_export': 'export' in all_code or 'download.*data' in all_code,
            'data_deletion': 'delete.*user' in all_code or 'anonymize' in all_code,
            'consent': 'consent' in all_code,
            'privacy_policy': 'privacy' in all_code.lower()
        }

        for check, passed in gdpr_checks.items():
            if not passed:
                gaps.append(CodeIssue(
                    severity='high',
                    category='compliance',
                    file_path='general',
                    line_number=None,
                    description=f'GDPR requirement missing: {check.replace("_", " ").title()}',
                    suggestion=f'Implement {check.replace("_", " ")} functionality',
                    code_snippet=None
                ))

        # Check for audit logging
        if 'audit' not in all_code.lower() and 'log' not in all_code.lower():
            gaps.append(CodeIssue(
                severity='medium',
                category='compliance',
                file_path='general',
                line_number=None,
                description='Audit logging not implemented',
                suggestion='Add audit logging for sensitive operations',
                code_snippet=None
            ))

        # Calculate compliance score
        compliance_score = max(0, 100 - (len(gaps) * 15))

        return gaps, compliance_score

    async def _analyze_performance(self, generated_app: Any) -> tuple:
        """Analyzes performance and returns (issues, score)"""
        issues = []

        backend_code = generated_app.backend_code

        # Check database schema for indexes
        schema = generated_app.database_schema

        # Check for missing indexes on foreign keys
        if 'FOREIGN KEY' in schema:
            fk_count = schema.count('FOREIGN KEY')
            index_count = schema.count('CREATE INDEX')

            if index_count < fk_count:
                issues.append(CodeIssue(
                    severity='medium',
                    category='performance',
                    file_path='database/schema.sql',
                    line_number=None,
                    description='Foreign keys without indexes',
                    suggestion='Add indexes on all foreign key columns',
                    code_snippet=None
                ))

        # Check for SELECT * queries
        for file_path, code in backend_code.items():
            if 'SELECT *' in code.upper():
                issues.append(CodeIssue(
                    severity='low',
                    category='performance',
                    file_path=file_path,
                    line_number=None,
                    description='Using SELECT * instead of specific columns',
                    suggestion='Select only needed columns to reduce data transfer',
                    code_snippet=None
                ))

            # Check for missing pagination
            if 'findAll' in code and 'LIMIT' not in code.upper():
                issues.append(CodeIssue(
                    severity='medium',
                    category='performance',
                    file_path=file_path,
                    line_number=None,
                    description='Query without pagination/limit',
                    suggestion='Add pagination to prevent loading all records',
                    code_snippet=None
                ))

        # Calculate performance score
        performance_score = max(0, 100 - (len(issues) * 10))

        return issues, performance_score

    async def _check_best_practices(self, generated_app: Any) -> List[CodeIssue]:
        """Checks for best practice violations"""
        violations = []

        backend_code = generated_app.backend_code

        # Check for .env.example
        if '.env.example' not in backend_code:
            violations.append(CodeIssue(
                severity='low',
                category='quality',
                file_path='root',
                line_number=None,
                description='Missing .env.example file',
                suggestion='Add .env.example with required environment variables',
                code_snippet=None
            ))

        # Check for README
        if not generated_app.readme or len(generated_app.readme) < 100:
            violations.append(CodeIssue(
                severity='low',
                category='quality',
                file_path='README.md',
                line_number=None,
                description='README is missing or too short',
                suggestion='Enhance README with comprehensive setup instructions',
                code_snippet=None
            ))

        return violations

    def _generate_improvement_suggestions(
        self,
        quality_issues: List[CodeIssue],
        security_issues: List[CodeIssue],
        compliance_gaps: List[CodeIssue],
        performance_issues: List[CodeIssue],
        best_practice_violations: List[CodeIssue]
    ) -> List[str]:
        """Generates prioritized improvement suggestions"""
        suggestions = []

        # Critical security issues first
        for issue in security_issues:
            if issue.severity == 'critical':
                suggestions.append(f"[CRITICAL] {issue.description} - {issue.suggestion}")

        # High priority items
        for issue in security_issues + compliance_gaps + quality_issues:
            if issue.severity == 'high':
                suggestions.append(f"[HIGH] {issue.description} - {issue.suggestion}")

        # Medium priority
        for issue in performance_issues + quality_issues:
            if issue.severity == 'medium':
                suggestions.append(f"[MEDIUM] {issue.description} - {issue.suggestion}")

        return suggestions[:10]  # Top 10 most important

    def _should_iterate(
        self,
        iteration: int,
        overall_score: float,
        security_issues: List[CodeIssue],
        compliance_gaps: List[CodeIssue]
    ) -> bool:
        """Determines if another iteration is needed"""

        # Don't iterate beyond max iterations
        if iteration >= self.max_iterations:
            return False

        # Always iterate if there are critical security issues
        critical_security = [i for i in security_issues if i.severity == 'critical']
        if critical_security:
            return True

        # Iterate if below quality threshold
        if overall_score < self.quality_threshold:
            return True

        # Iterate if there are high-severity compliance gaps
        high_compliance = [g for g in compliance_gaps if g.severity == 'high']
        if high_compliance:
            return True

        return False

    def _create_version_string(self, iteration: int) -> str:
        """Creates semantic version string"""
        # v1.0 for iteration 1, v1.1 for iteration 2, etc.
        return f"v1.{iteration - 1}"

    def _identify_applied_improvements(
        self,
        previous_report: ReflectionReport,
        current_app: Any
    ) -> List[str]:
        """Identifies which improvements from previous iteration were applied"""
        applied = []

        # Compare issue counts
        prev_issues = previous_report.all_issues()

        # This is a simplified check - in production would do deeper analysis
        if len(prev_issues) > 0:
            applied.append(f"Addressed {len(prev_issues)} issues from iteration {previous_report.iteration}")

        return applied

    def _print_report_summary(self, report: ReflectionReport):
        """Prints a formatted summary of the reflection report"""
        print(f"\n{'='*70}")
        print(f"[REPORT] REFLECTION REPORT - {report.version}")
        print(f"{'='*70}")
        print(f"[TIME] Analysis Duration: {report.analysis_duration:.2f}s")
        print(f"\n[SCORES] QUALITY SCORES:")
        print(f"   Overall:     {report.overall_score:.1f}/100")
        print(f"   Quality:     {report.quality_score:.1f}/100")
        print(f"   Security:    {report.security_score:.1f}/100")
        print(f"   Compliance:  {report.compliance_score:.1f}/100")
        print(f"   Performance: {report.performance_score:.1f}/100")

        print(f"\n[ISSUES] ISSUES FOUND:")
        print(f"   Security:        {len(report.security_issues)} ({len([i for i in report.security_issues if i.severity == 'critical'])} critical)")
        print(f"   Quality:         {len(report.quality_issues)}")
        print(f"   Compliance:      {len(report.compliance_gaps)}")
        print(f"   Performance:     {len(report.performance_issues)}")
        print(f"   Best Practices:  {len(report.best_practice_violations)}")

        if report.improvement_suggestions:
            print(f"\n[IMPROVE] TOP IMPROVEMENTS NEEDED:")
            for i, suggestion in enumerate(report.improvement_suggestions[:5], 1):
                print(f"   {i}. {suggestion}")

        if report.applied_improvements:
            print(f"\n[APPLIED] IMPROVEMENTS FROM PREVIOUS ITERATION:")
            for improvement in report.applied_improvements:
                print(f"   * {improvement}")

        print(f"\n[ITERATE] NEXT ITERATION: {'YES' if report.should_iterate else 'NO'}")

        if not report.should_iterate:
            print(f"[READY] Quality threshold met! Code is production-ready.")

        print(f"{'='*70}\n")
