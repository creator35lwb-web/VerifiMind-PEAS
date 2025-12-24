"""
GodelAI Integration Module for VerifiMind-PEAS
==============================================

External Contribution from GodelAI Project
Author: Godel, CTO - GodelAI Project
Date: December 24, 2025

This module provides C-S-P (Compression → State → Propagation) validation
capabilities for the VerifiMind-PEAS X-Z-CS Trinity.

Integration Points:
- X Agent: Technical feasibility metrics
- Z Agent: Ethical alignment and cultural preservation metrics
- CS Agent: Security and integrity metrics

Usage:
    from src.integrations.godelai import CSPValidator, create_csp_validator
    
    validator = create_csp_validator()
    result = validator.validate(compression, state, propagation)
    
    # Get agent-specific metrics
    x_metrics = validator.get_x_agent_metrics(result)
    z_metrics = validator.get_z_agent_metrics(result)
    cs_metrics = validator.get_cs_agent_metrics(result)
    
Enhanced Agent Usage:
    from src.integrations.godelai import CSPXAgentMixin, CSPEnhancedOrchestrator
    
    class EnhancedXAgent(CSPXAgentMixin, XIntelligentAgent):
        pass
"""

from .csp_validator import (
    # Main classes
    CSPValidator,
    
    # Data models
    CSPPhase,
    HealthStatus,
    CompressionMetrics,
    StateMetrics,
    PropagationMetrics,
    CSPValidationResult,
    
    # Factory functions
    create_csp_validator,
    create_mock_metrics_for_testing,
)

from .enhanced_agents import (
    # Agent Mixins
    CSPAgentMixin,
    CSPXAgentMixin,
    CSPZAgentMixin,
    CSPCSAgentMixin,
    
    # Enhanced Orchestrator
    CSPEnhancedOrchestrator,
)

__all__ = [
    # Main classes
    "CSPValidator",
    
    # Data models
    "CSPPhase",
    "HealthStatus",
    "CompressionMetrics",
    "StateMetrics",
    "PropagationMetrics",
    "CSPValidationResult",
    
    # Factory functions
    "create_csp_validator",
    "create_mock_metrics_for_testing",
    
    # Agent Mixins
    "CSPAgentMixin",
    "CSPXAgentMixin",
    "CSPZAgentMixin",
    "CSPCSAgentMixin",
    
    # Enhanced Orchestrator
    "CSPEnhancedOrchestrator",
]

# Module metadata
__author__ = "Godel, CTO - GodelAI Project"
__version__ = "1.0.0"
__license__ = "MIT"
__contribution_date__ = "2025-12-24"
