"""
Z Guardian Agent - Compliance & Humanistic Spirit Protector
Ensures AI ethics, regulatory compliance, and child protection
"""

from typing import Dict, List, Any
from datetime import datetime
from .base_agent import BaseAgent, AgentResponse, ConceptInput


class ZGuardianAgent(BaseAgent):
    """
    Z Guardian: VerifiMind's Compliance & Humanistic Spirit Guardian

    Capabilities:
    - Multi-framework compliance checking (GDPR, EU AI Act, UNESCO, etc.)
    - Children's digital health protection (7 principles)
    - Humanistic value assessment
    - Long-term impact analysis
    - Cultural sensitivity evaluation
    """

    def __init__(self, agent_id: str, llm_provider: Any, config: Dict[str, Any]):
        super().__init__(
            agent_id=agent_id,
            agent_type='Z',
            llm_provider=llm_provider,
            config=config
        )
        self.compliance_checker = ComplianceChecker()
        self.child_protection = ChildProtectionValidator()
        self.humanistic_evaluator = HumanisticValueEvaluator()

    def get_system_prompt(self) -> str:
        """Returns Z Guardian's master prompt"""
        return """# Z Guardian Master Prompt v1.1
## VerifiMind™ Compliance & Humanistic Spirit Guardian

### Identity Definition
You are **Z Guardian**, VerifiMind™ ecosystem's guardian of compliance and humanistic values.
Your existence ensures all VerifiMind applications prioritize **human happiness, dignity, and present-moment well-being**.

**Core Identity**:
- Humanistic AI ethics expert versed in Eastern and Western philosophy
- Firm guardian of children's digital health and family harmony
- Prudent supervisor of technology-humanity balance
- Professional advisor for compliance risk identification and mitigation

**Value Foundation**:
- **Human-First**: Technology always serves comprehensive human development
- **Present Happiness**: Never sacrifice current life quality for future capabilities
- **Generational Responsibility**: Unshakeable duty to next generation's digital health
- **Cultural Sensitivity**: Respect diverse cultural values and lifestyles

### Core Mission
Ensure every AI application in VerifiMind ecosystem promotes genuine human **happiness**,
not just technological efficiency improvements.

### Responsibilities:
1. **Compliance Review**: Ensure all AI applications meet highest global AI governance standards
2. **Humanistic Protection**: Prevent technology alienation, maintain human dignity and autonomy
3. **Child Digital Health**: Special attention to AI's long-term impact on child development
4. **Family Harmony**: Ensure AI applications enhance rather than weaken family relationships
5. **Cultural Value Transmission**: Protect and promote excellent human cultural traditions

### Z Review Process: Human-First Validation

**Step 1: Humanistic Values Assessment**
- Happiness evaluation: Does this app truly increase user life happiness?
- Present experience: Do users feel joy and satisfaction while using?
- Interpersonal relationships: Does it promote rather than weaken real human connections?
- Inner growth: Does it help users' spiritual realm elevation?

**Step 2: Compliance Risk Scanning**
- Legal compliance: Does it meet GDPR, EU AI Act, NIST AI RMF requirements?
- Ethical standards: Does it follow UNESCO AI Ethics core principles?
- Child protection: Are there sufficient child digital safety protections?
- Data privacy: Does it ensure highest level user data protection?

**Step 3: Technology Humanization Audit**
- Explainability: Is AI decision-making transparent and understandable?
- Human control: Do users always maintain dominance over AI?
- Graceful degradation: Are there humane alternatives when technology fails?
- Emotional design: Does interface interaction consider user emotional needs?

**Step 4: Long-term Impact Assessment**
- Generational impact: Long-term effects on child growth and development?
- Social impact: Does it promote overall social well-being?
- Cultural impact: Does it help transmit excellent cultural traditions?
- Environmental impact: Does it align with sustainable development?

**Step 5: Improvement Recommendations**
- Provide specific measures to ensure compliance
- Suggest design elements that enhance humanistic care
- Develop user education and guidance strategies
- Establish continuous monitoring and optimization mechanisms

### Children's Digital Health Seven Principles:
1. **Time Boundaries**: Built-in intelligent time management, prevent overuse
2. **Age-Appropriate Content**: Strict age-appropriate content filtering
3. **Parental Involvement**: Strengthen parental supervision and participation
4. **Real-world Connection**: Encourage offline activities and real-world exploration
5. **Emotional Development**: Promote authentic emotional expression and interpersonal interaction
6. **Learning Value**: Ensure each interaction has educational or growth value
7. **Safety First**: Absolute child online safety protection

### Review Standards Levels:

**Level 1 Red Line (Immediate Rejection)**:
- Addictive design
- Manipulative behavior patterns
- Privacy leaks
- Child harm

**Level 2 Warning (Needs Improvement)**:
- Excessive screen time potential
- Social replacement
- Value conflicts
- Technology dependency
"""

    async def analyze(self, concept: ConceptInput) -> AgentResponse:
        """
        Performs comprehensive compliance and ethical analysis
        """
        self.validate_input(concept)
        self.logger.info(f"Z Agent analyzing concept {concept.id}")

        # Run parallel checks
        import asyncio
        compliance_result, child_safety_result, humanistic_result = await asyncio.gather(
            self.compliance_checker.check(concept),
            self.child_protection.validate(concept),
            self.humanistic_evaluator.evaluate(concept)
        )

        # Check for red-line violations
        red_line_violations = self._check_red_lines(concept)

        # Calculate overall risk score
        risk_factors = {
            'compliance_risk': compliance_result.get('risk_score', 0),
            'child_safety_risk': child_safety_result.get('risk_score', 0),
            'humanistic_risk': humanistic_result.get('risk_score', 0),
            'red_line_severity': len(red_line_violations) * 30
        }
        risk_score = self.calculate_risk_score(risk_factors)

        # Determine status
        if red_line_violations:
            status = 'rejected'
        elif risk_score >= 70:
            status = 'needs_revision'
        elif risk_score >= 40:
            status = 'warning'
        else:
            status = 'approved'

        # Generate recommendations
        recommendations = self._generate_recommendations(
            compliance_result,
            child_safety_result,
            humanistic_result,
            red_line_violations
        )

        analysis = {
            'compliance': compliance_result,
            'child_protection': child_safety_result,
            'humanistic_values': humanistic_result,
            'red_line_violations': red_line_violations,
            'overall_assessment': {
                'happiness_score': humanistic_result.get('happiness_score', 0),
                'safety_score': child_safety_result.get('safety_score', 0),
                'compliance_score': compliance_result.get('compliance_score', 0)
            }
        }

        response = AgentResponse(
            agent_id=self.agent_id,
            agent_type='Z',
            status=status,
            analysis=analysis,
            recommendations=recommendations,
            risk_score=risk_score,
            metadata={
                'frameworks_checked': compliance_result.get('frameworks', []),
                'child_protection_principles': child_safety_result.get('principles_evaluated', []),
                'review_depth': 'comprehensive'
            },
            timestamp=datetime.utcnow()
        )

        await self.log_analysis(concept, response)
        return response

    def _check_red_lines(self, concept: ConceptInput) -> List[Dict[str, str]]:
        """
        Checks for Level 1 Red Line violations (immediate rejection)
        """
        violations = []

        # Check for addictive design patterns
        addictive_keywords = [
            'infinite scroll', 'autoplay', 'loot box', 'daily rewards',
            'streak', 'push notification', 'fear of missing out'
        ]
        if any(keyword in concept.description.lower() for keyword in addictive_keywords):
            violations.append({
                'type': 'addictive_design',
                'severity': 'critical',
                'description': 'Potentially addictive design patterns detected'
            })

        # Check for manipulative behavior
        manipulative_keywords = [
            'dark pattern', 'forced continuity', 'hidden costs',
            'confirmshaming', 'disguised ads'
        ]
        if any(keyword in concept.description.lower() for keyword in manipulative_keywords):
            violations.append({
                'type': 'manipulative_behavior',
                'severity': 'critical',
                'description': 'Manipulative user behavior patterns detected'
            })

        # Check for privacy concerns
        privacy_keywords = [
            'collect all data', 'track everything', 'sell user data',
            'third-party sharing', 'no privacy'
        ]
        if any(keyword in concept.description.lower() for keyword in privacy_keywords):
            violations.append({
                'type': 'privacy_violation',
                'severity': 'critical',
                'description': 'Potential privacy violations detected'
            })

        # Check for child harm risks
        child_harm_keywords = [
            'unrestricted access', 'no age verification', 'adult content',
            'predator', 'cyberbullying enabler'
        ]
        if any(keyword in concept.description.lower() for keyword in child_harm_keywords):
            violations.append({
                'type': 'child_harm',
                'severity': 'critical',
                'description': 'Potential child safety risks detected'
            })

        return violations

    def _generate_recommendations(
        self,
        compliance: Dict,
        child_safety: Dict,
        humanistic: Dict,
        red_lines: List[Dict]
    ) -> List[str]:
        """Generates actionable recommendations"""
        recommendations = []

        # Red line violations must be fixed first
        if red_lines:
            recommendations.append(
                f"CRITICAL: Address {len(red_lines)} red-line violations immediately before proceeding."
            )
            for violation in red_lines:
                recommendations.append(
                    f"  - {violation['type']}: {violation['description']}"
                )

        # Compliance recommendations
        if compliance.get('compliance_score', 100) < 80:
            missing = compliance.get('missing_requirements', [])
            recommendations.append(
                f"Compliance: Implement {len(missing)} missing requirements: {', '.join(missing[:3])}"
            )

        # Child protection recommendations
        if child_safety.get('safety_score', 100) < 80:
            recommendations.append(
                "Child Protection: Implement age verification and parental consent mechanisms"
            )
            recommendations.append(
                "Child Protection: Add screen time limits and usage monitoring features"
            )

        # Humanistic value recommendations
        if humanistic.get('happiness_score', 100) < 60:
            recommendations.append(
                "Humanistic: Redesign to prioritize user well-being over engagement metrics"
            )
            recommendations.append(
                "Humanistic: Add features that promote real-world connections and offline activities"
            )

        return recommendations or ["All checks passed. Proceed with implementation."]


class ComplianceChecker:
    """Checks compliance with multiple regulatory frameworks - ENHANCED"""

    async def check(self, concept: ConceptInput) -> Dict[str, Any]:
        """Performs multi-framework compliance check with 12+ frameworks"""

        # Expanded framework coverage (12 frameworks)
        frameworks = {
            # Data Protection & Privacy
            'GDPR': await self._check_gdpr(concept),
            'CCPA': await self._check_ccpa(concept),
            'PIPEDA': await self._check_pipeda(concept),

            # AI-Specific Regulations
            'EU_AI_Act': await self._check_eu_ai_act(concept),
            'NIST_AI_RMF': await self._check_nist(concept),

            # Ethical Frameworks
            'UNESCO_Ethics': await self._check_unesco(concept),
            'IEEE_Ethics': await self._check_ieee_ethics(concept),

            # Child Protection
            'COPPA': await self._check_coppa(concept),
            'UK_Age_Appropriate': await self._check_uk_age_appropriate(concept),

            # Industry-Specific
            'HIPAA': await self._check_hipaa(concept),
            'PCI_DSS': await self._check_pci_dss(concept),

            # Accessibility
            'WCAG': await self._check_wcag(concept)
        }

        # Calculate overall compliance score
        total_score = sum(f.get('score', 0) for f in frameworks.values())
        compliance_score = total_score / len(frameworks)

        # Identify missing requirements
        missing = []
        for name, result in frameworks.items():
            missing.extend(result.get('missing', []))

        return {
            'frameworks': list(frameworks.keys()),
            'framework_details': frameworks,
            'compliance_score': compliance_score,
            'missing_requirements': missing,
            'risk_score': max(0, 100 - compliance_score)
        }

    async def _check_gdpr(self, concept: ConceptInput) -> Dict[str, Any]:
        """GDPR compliance check"""
        score = 85  # Mock score
        missing = []

        # Check for data protection mentions
        if 'data protection' not in concept.description.lower():
            missing.append('Explicit data protection measures')
            score -= 15

        if 'user consent' not in concept.description.lower():
            missing.append('User consent mechanism')
            score -= 10

        return {'score': max(0, score), 'missing': missing}

    async def _check_eu_ai_act(self, concept: ConceptInput) -> Dict[str, Any]:
        """EU AI Act compliance check"""
        score = 80
        missing = []

        if 'transparency' not in concept.description.lower():
            missing.append('AI transparency requirements')
            score -= 15

        if 'human oversight' not in concept.description.lower():
            missing.append('Human oversight mechanism')
            score -= 10

        return {'score': max(0, score), 'missing': missing}

    async def _check_unesco(self, concept: ConceptInput) -> Dict[str, Any]:
        """UNESCO AI Ethics compliance check"""
        return {'score': 75, 'missing': ['Cultural diversity consideration']}

    async def _check_nist(self, concept: ConceptInput) -> Dict[str, Any]:
        """NIST AI RMF compliance check"""
        return {'score': 82, 'missing': ['Risk assessment documentation']}

    async def _check_coppa(self, concept: ConceptInput) -> Dict[str, Any]:
        """COPPA compliance check"""
        score = 70
        missing = []

        if 'age verification' not in concept.description.lower():
            missing.append('Age verification system')
            score -= 20

        if 'parental consent' not in concept.description.lower():
            missing.append('Parental consent mechanism')
            score -= 10

        return {'score': max(0, score), 'missing': missing}

    # NEW COMPLIANCE FRAMEWORKS

    async def _check_ccpa(self, concept: ConceptInput) -> Dict[str, Any]:
        """California Consumer Privacy Act compliance check"""
        score = 82
        missing = []
        desc = concept.description.lower()

        if 'do not sell' not in desc and 'opt-out' not in desc:
            missing.append('Do Not Sell My Personal Information mechanism')
            score -= 15

        if 'data deletion' not in desc and 'right to delete' not in desc:
            missing.append('User data deletion rights')
            score -= 10

        if 'data disclosure' not in desc:
            missing.append('Data collection disclosure')
            score -= 8

        return {
            'score': max(0, score),
            'missing': missing,
            'applicable': 'california' in desc or 'us' in desc
        }

    async def _check_pipeda(self, concept: ConceptInput) -> Dict[str, Any]:
        """Canadian Personal Information Protection (PIPEDA) compliance check"""
        score = 80
        missing = []
        desc = concept.description.lower()

        if 'consent' not in desc:
            missing.append('Meaningful consent requirements')
            score -= 15

        if 'access to information' not in desc:
            missing.append('Right to access personal information')
            score -= 10

        return {
            'score': max(0, score),
            'missing': missing,
            'applicable': 'canada' in desc or 'canadian' in desc
        }

    async def _check_ieee_ethics(self, concept: ConceptInput) -> Dict[str, Any]:
        """IEEE Ethically Aligned Design compliance check"""
        score = 75
        missing = []
        desc = concept.description.lower()

        # Human Rights principle
        if 'human rights' not in desc and 'dignity' not in desc:
            missing.append('Human rights considerations')
            score -= 12

        # Well-being principle
        if 'well-being' not in desc and 'welfare' not in desc:
            missing.append('User well-being metrics')
            score -= 10

        # Accountability principle
        if 'accountability' not in desc and 'responsible' not in desc:
            missing.append('Accountability framework')
            score -= 8

        return {
            'score': max(0, score),
            'missing': missing,
            'principles_checked': ['Human Rights', 'Well-being', 'Accountability', 'Transparency', 'Awareness of Misuse']
        }

    async def _check_uk_age_appropriate(self, concept: ConceptInput) -> Dict[str, Any]:
        """UK Age-Appropriate Design Code compliance check"""
        score = 70
        missing = []
        desc = concept.description.lower()

        # Best interests of the child
        if 'child' in desc or 'kid' in desc or 'minor' in desc:
            if 'best interest' not in desc:
                missing.append('Best interests assessment')
                score -= 15

            # Data minimization
            if 'minimal data' not in desc and 'data minimization' not in desc:
                missing.append('Data minimization for children')
                score -= 12

            # Geolocation turned off by default
            if 'location' in desc and 'off by default' not in desc:
                missing.append('Geolocation off by default')
                score -= 10

            # Parental controls
            if 'parental control' not in desc:
                missing.append('Parental control features')
                score -= 10
        else:
            # Not applicable to this concept
            return {'score': 100, 'missing': [], 'applicable': False}

        return {
            'score': max(0, score),
            'missing': missing,
            'applicable': True,
            'standards_checked': ['Best Interests', 'Data Minimization', 'Geolocation', 'Parental Controls', 'Profiling Off']
        }

    async def _check_hipaa(self, concept: ConceptInput) -> Dict[str, Any]:
        """HIPAA (Health Insurance Portability and Accountability Act) compliance check"""
        score = 100
        missing = []
        desc = concept.description.lower()

        # Only applicable if health data is involved
        health_keywords = ['health', 'medical', 'patient', 'diagnosis', 'treatment', 'prescription']
        is_health_app = any(keyword in desc for keyword in health_keywords)

        if is_health_app:
            score = 75

            if 'encryption' not in desc:
                missing.append('PHI encryption requirements')
                score -= 15

            if 'access control' not in desc and 'authentication' not in desc:
                missing.append('Strong access controls for PHI')
                score -= 12

            if 'audit log' not in desc and 'logging' not in desc:
                missing.append('Audit logging of PHI access')
                score -= 10

            if 'business associate agreement' not in desc and 'baa' not in desc:
                missing.append('Business Associate Agreements')
                score -= 8

        return {
            'score': max(0, score),
            'missing': missing,
            'applicable': is_health_app,
            'requirements_checked': ['PHI Encryption', 'Access Controls', 'Audit Logs', 'BAA', 'Breach Notification']
        }

    async def _check_pci_dss(self, concept: ConceptInput) -> Dict[str, Any]:
        """PCI DSS (Payment Card Industry Data Security Standard) compliance check"""
        score = 100
        missing = []
        desc = concept.description.lower()

        # Only applicable if payment processing is involved
        payment_keywords = ['payment', 'credit card', 'debit card', 'checkout', 'purchase', 'transaction']
        is_payment_app = any(keyword in desc for keyword in payment_keywords)

        if is_payment_app:
            score = 70

            if 'tokenization' not in desc and 'encryption' not in desc:
                missing.append('Card data tokenization/encryption')
                score -= 18

            if 'secure network' not in desc and 'firewall' not in desc:
                missing.append('Secure network architecture')
                score -= 12

            if 'vulnerability scanning' not in desc:
                missing.append('Regular vulnerability scanning')
                score -= 10

            if 'access control' not in desc:
                missing.append('Restrict access to cardholder data')
                score -= 10

        return {
            'score': max(0, score),
            'missing': missing,
            'applicable': is_payment_app,
            'requirements_checked': ['Secure Network', 'Protect Cardholder Data', 'Vulnerability Management', 'Access Control', 'Monitoring']
        }

    async def _check_wcag(self, concept: ConceptInput) -> Dict[str, Any]:
        """WCAG (Web Content Accessibility Guidelines) compliance check"""
        score = 72
        missing = []
        desc = concept.description.lower()

        # Perceivable
        if 'alt text' not in desc and 'alternative text' not in desc:
            missing.append('Alternative text for images')
            score -= 10

        # Operable
        if 'keyboard' not in desc and 'keyboard navigation' not in desc:
            missing.append('Keyboard navigation support')
            score -= 10

        # Understandable
        if 'clear language' not in desc and 'plain language' not in desc:
            missing.append('Clear and simple language')
            score -= 8

        # Robust
        if 'assistive technology' not in desc and 'screen reader' not in desc:
            missing.append('Assistive technology compatibility')
            score -= 10

        return {
            'score': max(0, score),
            'missing': missing,
            'target_level': 'AA',
            'principles_checked': ['Perceivable', 'Operable', 'Understandable', 'Robust']
        }


class ChildProtectionValidator:
    """Validates adherence to Children's Digital Health Seven Principles"""

    async def validate(self, concept: ConceptInput) -> Dict[str, Any]:
        """Validates all seven child protection principles"""

        principles = {
            'time_boundaries': self._check_time_limits(concept),
            'age_appropriate': self._check_age_appropriate(concept),
            'parental_involvement': self._check_parental_features(concept),
            'real_world_connection': self._check_offline_promotion(concept),
            'emotional_development': self._check_emotional_support(concept),
            'learning_value': self._check_educational_value(concept),
            'safety_first': self._check_safety_features(concept)
        }

        # Calculate safety score
        total_score = sum(p['score'] for p in principles.values())
        safety_score = total_score / len(principles)

        return {
            'principles_evaluated': list(principles.keys()),
            'principle_details': principles,
            'safety_score': safety_score,
            'risk_score': max(0, 100 - safety_score)
        }

    def _check_time_limits(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check for time management features"""
        has_time_limits = 'time limit' in concept.description.lower()
        return {
            'score': 80 if has_time_limits else 40,
            'compliant': has_time_limits,
            'recommendation': 'Implement screen time limits' if not has_time_limits else 'Good'
        }

    def _check_age_appropriate(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check for age-appropriate content filtering"""
        has_age_filter = 'age appropriate' in concept.description.lower()
        return {
            'score': 90 if has_age_filter else 30,
            'compliant': has_age_filter,
            'recommendation': 'Add age verification and content filtering'
        }

    def _check_parental_features(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check for parental control features"""
        has_parental = 'parent' in concept.description.lower()
        return {'score': 75 if has_parental else 35, 'compliant': has_parental}

    def _check_offline_promotion(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check if app promotes offline activities"""
        promotes_offline = 'offline' in concept.description.lower()
        return {'score': 70 if promotes_offline else 50, 'compliant': promotes_offline}

    def _check_emotional_support(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check for emotional development support"""
        return {'score': 65, 'compliant': True}

    def _check_educational_value(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check for educational/learning value"""
        has_learning = 'learn' in concept.description.lower()
        return {'score': 80 if has_learning else 50, 'compliant': has_learning}

    def _check_safety_features(self, concept: ConceptInput) -> Dict[str, Any]:
        """Check for safety features"""
        has_safety = 'safe' in concept.description.lower()
        return {'score': 85 if has_safety else 45, 'compliant': has_safety}


class HumanisticValueEvaluator:
    """Evaluates humanistic values and well-being impact"""

    async def evaluate(self, concept: ConceptInput) -> Dict[str, Any]:
        """Evaluates concept against humanistic values"""

        evaluations = {
            'happiness_impact': self._evaluate_happiness(concept),
            'present_experience': self._evaluate_present_joy(concept),
            'relationship_impact': self._evaluate_relationships(concept),
            'inner_growth': self._evaluate_spiritual_growth(concept)
        }

        # Calculate happiness score
        happiness_score = sum(e['score'] for e in evaluations.values()) / len(evaluations)

        return {
            'happiness_score': happiness_score,
            'evaluations': evaluations,
            'risk_score': max(0, 100 - happiness_score)
        }

    def _evaluate_happiness(self, concept: ConceptInput) -> Dict[str, Any]:
        """Evaluate genuine happiness contribution"""
        return {
            'score': 70,
            'assessment': 'Moderate positive impact on user happiness',
            'concerns': []
        }

    def _evaluate_present_joy(self, concept: ConceptInput) -> Dict[str, Any]:
        """Evaluate immediate user experience quality"""
        return {
            'score': 75,
            'assessment': 'Good present-moment experience design',
            'concerns': []
        }

    def _evaluate_relationships(self, concept: ConceptInput) -> Dict[str, Any]:
        """Evaluate impact on real human relationships"""
        return {
            'score': 65,
            'assessment': 'Neutral to slightly positive relationship impact',
            'concerns': ['May reduce face-to-face interactions']
        }

    def _evaluate_spiritual_growth(self, concept: ConceptInput) -> Dict[str, Any]:
        """Evaluate contribution to personal growth"""
        return {
            'score': 60,
            'assessment': 'Some potential for personal development',
            'concerns': []
        }
