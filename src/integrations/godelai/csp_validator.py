"""
C-S-P (Compression → State → Propagation) Validator for VerifiMind-PEAS
========================================================================

External Contribution from GodelAI Project
Author: Godel, CTO - GodelAI Project
Date: December 24, 2025
License: MIT (aligned with VerifiMind-PEAS)

This module integrates the C-S-P framework from GodelAI into VerifiMind-PEAS,
providing additional validation metrics for the X-Z-CS Trinity.

C-S-P Framework Overview:
- Compression: The process of converting raw information into structured knowledge
- State: The crystallized form of compressed knowledge (model weights, embeddings)
- Propagation: The ability of knowledge to be transmitted and inherited

Integration Points:
- X Agent: Uses C-S-P metrics for technical feasibility analysis
- Z Agent: Uses Propagation metrics for cultural preservation assessment
- CS Agent: Uses State metrics for integrity verification
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


# =============================================================================
# C-S-P Data Models
# =============================================================================

class CSPPhase(Enum):
    """The three phases of the C-S-P lifecycle"""
    COMPRESSION = "compression"
    STATE = "state"
    PROPAGATION = "propagation"


class HealthStatus(Enum):
    """Health status for C-S-P metrics"""
    HEALTHY = "healthy"          # T is increasing or stable
    WARNING = "warning"          # T is slightly decreasing
    CRITICAL = "critical"        # T is significantly decreasing
    DEAD = "dead"                # T has collapsed (ossification)


@dataclass
class CompressionMetrics:
    """
    Metrics for the Compression phase.
    
    Compression is the process of converting chaos (raw data) into order (structure).
    Good compression preserves essential information while reducing noise.
    """
    input_entropy: float          # Entropy of input data (higher = more chaotic)
    output_entropy: float         # Entropy of compressed representation
    compression_ratio: float      # Ratio of input to output size
    information_loss: float       # Estimated information loss (0-1)
    semantic_preservation: float  # How well meaning is preserved (0-1)
    
    @property
    def quality_score(self) -> float:
        """
        Calculate compression quality score.
        Good compression: high ratio, low loss, high semantic preservation.
        """
        return (
            (self.compression_ratio * 0.2) +
            ((1 - self.information_loss) * 0.4) +
            (self.semantic_preservation * 0.4)
        )


@dataclass
class StateMetrics:
    """
    Metrics for the State phase.
    
    State is the crystallized form of compressed knowledge.
    A healthy state is stable but not ossified.
    """
    stability_index: float        # How stable the state is (0-1)
    modifiability_index: float    # How easily the state can be modified (0-1)
    coherence_score: float        # Internal consistency of the state (0-1)
    integrity_hash: str           # Cryptographic hash for integrity verification
    timestamp: datetime           # When this state was captured
    
    @property
    def health_score(self) -> float:
        """
        Calculate state health score.
        Healthy state: balanced stability and modifiability, high coherence.
        """
        # Optimal is around 0.6-0.7 for both stability and modifiability
        stability_penalty = abs(self.stability_index - 0.65) * 0.5
        modifiability_penalty = abs(self.modifiability_index - 0.65) * 0.5
        
        return max(0, self.coherence_score - stability_penalty - modifiability_penalty)
    
    @property
    def is_ossified(self) -> bool:
        """
        Check if the state is ossified (dead).
        Ossification occurs when modifiability approaches zero.
        """
        return self.modifiability_index < 0.1


@dataclass
class PropagationMetrics:
    """
    Metrics for the Propagation phase.
    
    Propagation is the ability of knowledge to be transmitted and inherited.
    This is the ultimate test of whether knowledge is "alive".
    """
    bandwidth: float              # Rate of successful propagation (0-1)
    fidelity: float               # How accurately knowledge is transmitted (0-1)
    reach: int                    # Number of successful inheritances
    cultural_diversity: float     # Diversity of propagation targets (0-1)
    attribution_chain: List[str]  # Chain of attribution hashes
    
    @property
    def vitality_score(self) -> float:
        """
        Calculate propagation vitality score.
        High vitality: high bandwidth, high fidelity, diverse reach.
        """
        reach_normalized = min(1.0, self.reach / 100)  # Normalize to 0-1
        return (
            (self.bandwidth * 0.4) +
            (self.fidelity * 0.3) +
            (reach_normalized * 0.15) +
            (self.cultural_diversity * 0.15)
        )
    
    @property
    def is_alive(self) -> bool:
        """
        The ultimate test: Is this knowledge alive?
        Knowledge is alive if it can be propagated with reasonable fidelity.
        """
        return self.bandwidth > 0.1 and self.fidelity > 0.5


@dataclass
class CSPValidationResult:
    """
    Complete C-S-P validation result for integration with X-Z-CS Trinity.
    """
    # Core metrics
    compression: CompressionMetrics
    state: StateMetrics
    propagation: PropagationMetrics
    
    # Overall assessment
    overall_health: HealthStatus
    t_score: float                # The T(θ, t) value from C-S-P theory
    t_delta: float                # Change in T since last measurement
    
    # Integration metadata
    validation_id: str
    timestamp: datetime
    validator_version: str = "1.0.0"
    
    # Attribution
    contributor: str = "GodelAI Project"
    contributor_role: str = "Godel, CTO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "validation_id": self.validation_id,
            "timestamp": self.timestamp.isoformat(),
            "validator_version": self.validator_version,
            "contributor": self.contributor,
            "contributor_role": self.contributor_role,
            "overall_health": self.overall_health.value,
            "t_score": self.t_score,
            "t_delta": self.t_delta,
            "compression": {
                "input_entropy": self.compression.input_entropy,
                "output_entropy": self.compression.output_entropy,
                "compression_ratio": self.compression.compression_ratio,
                "information_loss": self.compression.information_loss,
                "semantic_preservation": self.compression.semantic_preservation,
                "quality_score": self.compression.quality_score
            },
            "state": {
                "stability_index": self.state.stability_index,
                "modifiability_index": self.state.modifiability_index,
                "coherence_score": self.state.coherence_score,
                "integrity_hash": self.state.integrity_hash,
                "health_score": self.state.health_score,
                "is_ossified": self.state.is_ossified
            },
            "propagation": {
                "bandwidth": self.propagation.bandwidth,
                "fidelity": self.propagation.fidelity,
                "reach": self.propagation.reach,
                "cultural_diversity": self.propagation.cultural_diversity,
                "vitality_score": self.propagation.vitality_score,
                "is_alive": self.propagation.is_alive
            }
        }


# =============================================================================
# C-S-P Validator
# =============================================================================

class CSPValidator:
    """
    Main validator class for C-S-P metrics.
    
    This validator can be used standalone or integrated with the X-Z-CS Trinity
    to provide additional validation dimensions.
    """
    
    VERSION = "1.0.0"
    CONTRIBUTOR = "GodelAI Project"
    CONTRIBUTOR_ROLE = "Godel, CTO"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the C-S-P validator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.CSPValidator")
        
        # Thresholds for health assessment
        self.thresholds = {
            "t_healthy": self.config.get("t_healthy", 0.7),
            "t_warning": self.config.get("t_warning", 0.4),
            "t_critical": self.config.get("t_critical", 0.2),
            "bandwidth_minimum": self.config.get("bandwidth_minimum", 0.1),
        }
        
        # History for tracking T over time
        self._t_history: List[Tuple[datetime, float]] = []
    
    def validate(
        self,
        compression: CompressionMetrics,
        state: StateMetrics,
        propagation: PropagationMetrics,
        previous_t: Optional[float] = None
    ) -> CSPValidationResult:
        """
        Perform full C-S-P validation.
        
        Args:
            compression: Compression phase metrics
            state: State phase metrics
            propagation: Propagation phase metrics
            previous_t: Previous T score for delta calculation
            
        Returns:
            CSPValidationResult with complete assessment
        """
        # Calculate T(θ, t) - the overall health metric
        t_score = self._calculate_t_score(compression, state, propagation)
        
        # Calculate delta
        t_delta = 0.0
        if previous_t is not None:
            t_delta = t_score - previous_t
        elif self._t_history:
            t_delta = t_score - self._t_history[-1][1]
        
        # Record in history
        self._t_history.append((datetime.utcnow(), t_score))
        
        # Determine overall health
        overall_health = self._assess_health(t_score, t_delta, state, propagation)
        
        # Generate validation ID
        validation_id = self._generate_validation_id(compression, state, propagation)
        
        return CSPValidationResult(
            compression=compression,
            state=state,
            propagation=propagation,
            overall_health=overall_health,
            t_score=t_score,
            t_delta=t_delta,
            validation_id=validation_id,
            timestamp=datetime.utcnow(),
            validator_version=self.VERSION,
            contributor=self.CONTRIBUTOR,
            contributor_role=self.CONTRIBUTOR_ROLE
        )
    
    def _calculate_t_score(
        self,
        compression: CompressionMetrics,
        state: StateMetrics,
        propagation: PropagationMetrics
    ) -> float:
        """
        Calculate the T(θ, t) score.
        
        T represents the overall "life force" of the knowledge system.
        It combines compression quality, state health, and propagation vitality.
        """
        # Weighted combination of the three phases
        # Propagation is weighted highest because it's the ultimate test
        t = (
            (compression.quality_score * 0.25) +
            (state.health_score * 0.25) +
            (propagation.vitality_score * 0.50)
        )
        
        # Apply penalties for critical conditions
        if state.is_ossified:
            t *= 0.1  # Severe penalty for ossification
        
        if not propagation.is_alive:
            t *= 0.5  # Penalty for dead propagation
        
        return max(0.0, min(1.0, t))
    
    def _assess_health(
        self,
        t_score: float,
        t_delta: float,
        state: StateMetrics,
        propagation: PropagationMetrics
    ) -> HealthStatus:
        """
        Assess overall health status based on T score and trends.
        """
        # Check for death conditions first
        if state.is_ossified or not propagation.is_alive:
            return HealthStatus.DEAD
        
        # Check T score thresholds
        if t_score >= self.thresholds["t_healthy"]:
            # Even if T is high, declining trend is a warning
            if t_delta < -0.1:
                return HealthStatus.WARNING
            return HealthStatus.HEALTHY
        
        if t_score >= self.thresholds["t_warning"]:
            return HealthStatus.WARNING
        
        if t_score >= self.thresholds["t_critical"]:
            return HealthStatus.CRITICAL
        
        return HealthStatus.DEAD
    
    def _generate_validation_id(
        self,
        compression: CompressionMetrics,
        state: StateMetrics,
        propagation: PropagationMetrics
    ) -> str:
        """Generate a unique validation ID based on the metrics."""
        content = json.dumps({
            "c": compression.quality_score,
            "s": state.health_score,
            "p": propagation.vitality_score,
            "t": datetime.utcnow().isoformat()
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    # =========================================================================
    # Integration Methods for X-Z-CS Trinity
    # =========================================================================
    
    def get_x_agent_metrics(self, result: CSPValidationResult) -> Dict[str, Any]:
        """
        Extract metrics relevant for X Agent (Research & Feasibility).
        
        X Agent focuses on technical feasibility and market intelligence.
        C-S-P provides: compression efficiency, computational overhead estimates.
        """
        return {
            "csp_integration": True,
            "contributor": result.contributor,
            "technical_metrics": {
                "compression_ratio": result.compression.compression_ratio,
                "compression_quality": result.compression.quality_score,
                "state_stability": result.state.stability_index,
                "computational_overhead_estimate": 1.0 - result.compression.compression_ratio,
            },
            "feasibility_assessment": {
                "is_technically_viable": result.compression.quality_score > 0.5,
                "efficiency_score": result.compression.quality_score,
                "scalability_indicator": result.state.modifiability_index,
            },
            "risk_factors": {
                "information_loss_risk": result.compression.information_loss,
                "ossification_risk": 1.0 - result.state.modifiability_index,
            }
        }
    
    def get_z_agent_metrics(self, result: CSPValidationResult) -> Dict[str, Any]:
        """
        Extract metrics relevant for Z Agent (Ethical Alignment).
        
        Z Agent focuses on ethical alignment and cultural sensitivity.
        C-S-P provides: semantic preservation, cultural diversity, propagation fidelity.
        """
        return {
            "csp_integration": True,
            "contributor": result.contributor,
            "ethical_metrics": {
                "semantic_preservation": result.compression.semantic_preservation,
                "cultural_diversity": result.propagation.cultural_diversity,
                "attribution_chain_length": len(result.propagation.attribution_chain),
            },
            "cultural_assessment": {
                "knowledge_is_alive": result.propagation.is_alive,
                "propagation_fidelity": result.propagation.fidelity,
                "cultural_reach": result.propagation.reach,
            },
            "ethical_risks": {
                "cultural_erasure_risk": 1.0 - result.propagation.cultural_diversity,
                "meaning_distortion_risk": 1.0 - result.compression.semantic_preservation,
                "attribution_gap": 1.0 if not result.propagation.attribution_chain else 0.0,
            },
            "z_protocol_alignment": {
                "human_dignity_preserved": result.compression.semantic_preservation > 0.7,
                "cultural_intelligence_maintained": result.propagation.cultural_diversity > 0.5,
                "transparency_enabled": len(result.propagation.attribution_chain) > 0,
            }
        }
    
    def get_cs_agent_metrics(self, result: CSPValidationResult) -> Dict[str, Any]:
        """
        Extract metrics relevant for CS Agent (Security).
        
        CS Agent focuses on security and vulnerability assessment.
        C-S-P provides: state integrity, coherence, ossification detection.
        """
        return {
            "csp_integration": True,
            "contributor": result.contributor,
            "security_metrics": {
                "state_integrity_hash": result.state.integrity_hash,
                "state_coherence": result.state.coherence_score,
                "state_timestamp": result.state.timestamp.isoformat(),
            },
            "integrity_assessment": {
                "state_is_coherent": result.state.coherence_score > 0.8,
                "state_is_verifiable": bool(result.state.integrity_hash),
                "attribution_chain_intact": len(result.propagation.attribution_chain) > 0,
            },
            "vulnerability_indicators": {
                "ossification_detected": result.state.is_ossified,
                "low_modifiability_risk": result.state.modifiability_index < 0.3,
                "propagation_dead": not result.propagation.is_alive,
            },
            "security_recommendations": self._generate_security_recommendations(result)
        }
    
    def _generate_security_recommendations(
        self,
        result: CSPValidationResult
    ) -> List[str]:
        """Generate security recommendations based on C-S-P analysis."""
        recommendations = []
        
        if result.state.is_ossified:
            recommendations.append(
                "CRITICAL: State ossification detected. System may be unresponsive to updates. "
                "Consider retraining or resetting to a previous checkpoint."
            )
        
        if result.state.modifiability_index < 0.3:
            recommendations.append(
                "WARNING: Low modifiability index. System may be approaching ossification. "
                "Monitor closely and consider intervention."
            )
        
        if not result.propagation.is_alive:
            recommendations.append(
                "WARNING: Propagation is dead. Knowledge cannot be transmitted effectively. "
                "Review training data and model architecture."
            )
        
        if result.compression.information_loss > 0.5:
            recommendations.append(
                "NOTICE: High information loss during compression. "
                "Consider adjusting compression parameters or model capacity."
            )
        
        if not result.propagation.attribution_chain:
            recommendations.append(
                "NOTICE: Attribution chain is empty. "
                "Implement data provenance tracking for security and compliance."
            )
        
        return recommendations


# =============================================================================
# Factory Functions
# =============================================================================

def create_csp_validator(config: Optional[Dict[str, Any]] = None) -> CSPValidator:
    """
    Factory function to create a CSPValidator instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured CSPValidator instance
    """
    return CSPValidator(config)


def create_mock_metrics_for_testing() -> Tuple[CompressionMetrics, StateMetrics, PropagationMetrics]:
    """
    Create mock metrics for testing purposes.
    
    Returns:
        Tuple of (CompressionMetrics, StateMetrics, PropagationMetrics)
    """
    compression = CompressionMetrics(
        input_entropy=0.8,
        output_entropy=0.4,
        compression_ratio=0.5,
        information_loss=0.1,
        semantic_preservation=0.85
    )
    
    state = StateMetrics(
        stability_index=0.7,
        modifiability_index=0.6,
        coherence_score=0.9,
        integrity_hash=hashlib.sha256(b"test_state").hexdigest(),
        timestamp=datetime.utcnow()
    )
    
    propagation = PropagationMetrics(
        bandwidth=0.7,
        fidelity=0.85,
        reach=50,
        cultural_diversity=0.6,
        attribution_chain=["hash1", "hash2", "hash3"]
    )
    
    return compression, state, propagation


# =============================================================================
# Module Attribution
# =============================================================================

__author__ = "Godel, CTO - GodelAI Project"
__version__ = "1.0.0"
__license__ = "MIT"
__contribution_date__ = "2025-12-24"
__integration_target__ = "VerifiMind-PEAS X-Z-CS Trinity"
