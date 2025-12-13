"""
Core Data Models for VerifiMind PEAS
Shared data structures across all modules.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class Verdict(Enum):
    """Validation verdict from agents or scrutinizer."""
    GO = "go"
    PIVOT = "pivot"
    NO_GO = "no_go"

    @classmethod
    def from_string(cls, value: str) -> 'Verdict':
        """Convert string to Verdict enum (handles variations)."""
        normalized = value.lower().strip().replace(' ', '_').replace('-', '_')

        if normalized in ['go', 'approve', 'approved', 'pass', 'success']:
            return cls.GO
        elif normalized in ['pivot', 'refine', 'iterate', 'improve']:
            return cls.PIVOT
        elif normalized in ['no_go', 'reject', 'rejected', 'fail', 'failure']:
            return cls.NO_GO
        else:
            # Default to pivot for unknown values
            return cls.PIVOT


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# Concept & Validation
# =============================================================================

@dataclass
class ConceptInput:
    """Input for concept validation."""
    id: str
    description: str
    category: Optional[str] = None
    user_context: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ValidationResult:
    """Complete validation result from all agents."""
    concept_id: str
    overall_decision: str  # approve, reject, pivot
    overall_confidence: float  # 0-100
    x_analysis: Dict[str, Any] = field(default_factory=dict)
    z_compliance: Dict[str, Any] = field(default_factory=dict)
    cs_security: Dict[str, Any] = field(default_factory=dict)
    synthesis: Dict[str, Any] = field(default_factory=dict)
    report_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# Scrutiny Results (from Concept Scrutinizer)
# =============================================================================

@dataclass
class ScrutinyResult:
    """Result from 4-step Socratic scrutiny process."""
    concept_id: str

    # Step 1: Clarification
    clarification: str = ""
    assumptions: List[str] = field(default_factory=list)

    # Step 2: Feasibility Analysis
    innovation_score: float = 0.0
    technical_score: float = 0.0
    market_score: float = 0.0
    risk_score: float = 0.0
    overall_score: float = 0.0

    # Step 3: Socratic Challenges
    challenges: List[str] = field(default_factory=list)
    counterexamples: List[str] = field(default_factory=list)
    biases_identified: List[str] = field(default_factory=list)

    # Step 4: Strategic Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    verdict: Verdict = Verdict.PIVOT
    reasoning: str = ""

    # Metadata
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class FeasibilityAnalysis:
    """Detailed feasibility analysis (Step 2)."""
    innovation_type: str = "unknown"  # disruptive, incremental, recombinative
    innovation_score: float = 0.0

    technical_feasibility: str = "unknown"
    technical_score: float = 0.0
    technical_bottlenecks: List[str] = field(default_factory=list)

    market_size_tam: Optional[str] = None
    market_size_sam: Optional[str] = None
    market_size_som: Optional[str] = None
    market_score: float = 0.0

    risks: List[str] = field(default_factory=list)
    risk_score: float = 0.0

    overall_score: float = 0.0


@dataclass
class StrategicRecommendation:
    """Strategic recommendation option (Step 4)."""
    option_name: str  # e.g., "Option A: MVP-First", "Option B: Enterprise-First"
    description: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    timeline: str = ""
    resources_required: str = ""
    confidence: float = 0.0  # How confident is this recommendation (0-100)


# =============================================================================
# Agent Results
# =============================================================================

@dataclass
class AgentResult:
    """Standardized result from any agent."""
    agent_id: str
    agent_name: str  # X, Z, or CS
    status: AgentStatus
    decision: str  # approve, reject, pivot
    score: float  # 0-100
    reasoning: str
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


@dataclass
class SecurityScanResult:
    """Result from CS Security Agent scan."""
    concept_id: str

    # Technical Security
    technical_risks: List[str] = field(default_factory=list)
    technical_risk_score: float = 0.0

    # Prompt Injection Detection
    injection_detected: bool = False
    injection_patterns: List[str] = field(default_factory=list)

    # Socratic Analysis (if enabled)
    socratic_analysis: Dict[str, Any] = field(default_factory=dict)

    # Overall
    overall_risk_score: float = 0.0
    verdict: Verdict = Verdict.PIVOT
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    execution_time_ms: float = 0.0
    degraded_context: bool = False  # True if scrutiny results were invalid


# =============================================================================
# Application Specification
# =============================================================================

@dataclass
class AppSpecification:
    """Application specification for code generation."""
    app_id: str
    app_name: str
    description: str
    category: str

    core_features: List[str] = field(default_factory=list)
    compliance_features: List[str] = field(default_factory=list)
    security_requirements: List[str] = field(default_factory=list)

    tech_stack: Dict[str, str] = field(default_factory=dict)
    target_users: str = ""
    business_model: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'app_id': self.app_id,
            'app_name': self.app_name,
            'description': self.description,
            'category': self.category,
            'core_features': self.core_features,
            'compliance_features': self.compliance_features,
            'security_requirements': self.security_requirements,
            'tech_stack': self.tech_stack,
            'target_users': self.target_users,
            'business_model': self.business_model,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }


# =============================================================================
# Generation History
# =============================================================================

@dataclass
class GenerationHistory:
    """Track code generation iteration history."""
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    total_iterations: int = 0
    initial_score: float = 0.0
    final_score: float = 0.0
    improvement_percentage: float = 0.0

    def add_iteration(self, iteration_data: Dict[str, Any]):
        """Add an iteration to history."""
        self.iterations.append(iteration_data)
        self.total_iterations = len(self.iterations)

        # Update scores
        if self.iterations:
            if self.total_iterations == 1:
                self.initial_score = iteration_data.get('quality_score', 0.0)
            self.final_score = iteration_data.get('quality_score', 0.0)

            if self.initial_score > 0:
                self.improvement_percentage = (
                    (self.final_score - self.initial_score) / self.initial_score
                ) * 100


# =============================================================================
# Orchestration Decision
# =============================================================================

@dataclass
class OrchestrationDecision:
    """Final decision from orchestrator after conflict resolution."""
    decision: str  # approve, reject, pivot
    confidence: float  # 0-100
    reason: str
    agent_votes: Dict[str, str]  # {agent_name: decision}
    conflicts_detected: List[str] = field(default_factory=list)
    resolution_strategy: str = ""  # consensus, z_veto, cs_critical, majority
    timestamp: datetime = field(default_factory=datetime.utcnow)
