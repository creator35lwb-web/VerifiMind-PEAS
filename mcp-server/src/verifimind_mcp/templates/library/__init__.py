"""
VerifiMind-PEAS Template Library
================================

Pre-built template collections for common use cases. The library is loaded
as YAML data files (not Python modules) — see the .yaml files in this
directory. The registry loader in ``templates/registry.py`` discovers and
loads these YAML files at runtime.

YAML files in this directory:
- startup_validation.yaml: Startup concept validation (X Agent, Phase 1)
- market_research.yaml: Market analysis templates (X Agent, Phase 1)
- ethics_review.yaml: Ethics review with Z-Protocol (Z Agent, Phase 2)
- security_audit.yaml: Security audit templates (CS Agent, Phase 3)
- technical_review.yaml: Code/architecture review (CS Agent, Phase 3)
- trinity_synthesis.yaml: Multi-agent synthesis (All Agents, Phase 4)

Author: Alton Lee
Version: 0.4.0
"""

# Intentionally no __all__ here — the template collections are YAML data files
# loaded at runtime by templates/registry.py, not Python submodules that can
# be imported. Listing them in __all__ would cause SonarCloud (and any static
# analyzer) to flag them as undefined symbols.
