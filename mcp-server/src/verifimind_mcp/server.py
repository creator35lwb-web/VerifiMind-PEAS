"""
Genesis Context Server - Phase 2 (Core Tools)
==============================================

MCP server exposing VerifiMind-PEAS Genesis Methodology context as Resources
and agent consultation as Tools.

Resources Exposed:
- genesis://config/master_prompt - Genesis Master Prompt v16.1
- genesis://history/latest - Most recent validation result
- genesis://history/all - Complete validation history
- genesis://state/project_info - Current project information

Tools Exposed:
- consult_agent_x - Consult X Intelligent for innovation analysis
- consult_agent_z - Consult Z Guardian for ethical review
- consult_agent_cs - Consult CS Security for security validation
- run_full_trinity - Run complete X → Z → CS validation

Author: Alton Lee
Version: 0.2.0 (Phase 2 - Core Tools)
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP, Context
from smithery.decorators import smithery
from pydantic import BaseModel, Field


class VerifiMindConfig(BaseModel):
    """Session configuration for VerifiMind Genesis Server.

    Allows users to customize their validation experience.
    """
    llm_provider: str = Field(
        default="mock",
        description="LLM provider to use: 'openai', 'anthropic', or 'mock' (for testing)"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional, can also use OPENAI_API_KEY env var)"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key (optional, can also use ANTHROPIC_API_KEY env var)"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness: 'standard' or 'strict'"
    )


# Constants
REPO_ROOT = Path(__file__).parent.parent.parent.parent
MASTER_PROMPT_PATH = REPO_ROOT / "reflexion-master-prompts-v1.1.md"
HISTORY_PATH = REPO_ROOT / "verifimind_history.json"


def load_master_prompt() -> str:
    """Load Genesis Master Prompt from repository."""
    try:
        if MASTER_PROMPT_PATH.exists():
            return MASTER_PROMPT_PATH.read_text(encoding="utf-8")
        else:
            return "# Genesis Master Prompt v16.1\n\n(Master Prompt file not found. Please ensure reflexion-master-prompts-v1.1.md exists in repository root.)"
    except Exception as e:
        return f"# Error Loading Master Prompt\n\nError: {str(e)}"


def load_validation_history() -> dict[str, Any]:
    """Load validation history from JSON file."""
    try:
        if HISTORY_PATH.exists():
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "validations": [],
                "metadata": {
                    "total_validations": 0,
                    "last_updated": None,
                    "note": "No validation history found. Run verifimind_complete.py to generate validation data."
                }
            }
    except Exception as e:
        return {
            "error": f"Failed to load validation history: {str(e)}",
            "validations": []
        }


def save_validation_history(history: dict[str, Any]) -> None:
    """Save validation history to JSON file."""
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Failed to save validation history: {e}")


def get_latest_validation() -> dict[str, Any]:
    """Get most recent validation result."""
    history = load_validation_history()
    validations = history.get("validations", [])
    
    if validations:
        return validations[-1]
    else:
        return {
            "status": "no_validations",
            "message": "No validation history available. Run verifimind_complete.py to generate validation data."
        }


def get_project_info() -> dict[str, Any]:
    """Get current project information."""
    return {
        "project_name": "VerifiMind-PEAS",
        "methodology": "Genesis Methodology",
        "version": "2.0.1",
        "architecture": "RefleXion Trinity (X-Z-CS)",
        "mcp_server_version": "0.2.0",
        "agents": {
            "X": {
                "name": "X Intelligent",
                "role": "Innovation and Strategy Engine",
                "focus": ["Innovation potential", "Strategic value", "Market opportunities"]
            },
            "Z": {
                "name": "Z Guardian",
                "role": "Ethical Review and Z-Protocol Enforcement",
                "focus": ["Ethics", "Privacy", "Bias", "Social impact"],
                "has_veto_power": True
            },
            "CS": {
                "name": "CS Security",
                "role": "Security Validation and Socratic Interrogation",
                "focus": ["Security vulnerabilities", "Attack vectors", "Socratic questioning"]
            }
        },
        "master_prompt_version": "v16.1",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "documentation": "https://github.com/creator35lwb-web/VerifiMind-PEAS/docs",
        "white_paper": "https://github.com/creator35lwb-web/VerifiMind-PEAS/docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md"
    }


def _create_mcp_instance():
    """Internal function to create the raw FastMCP instance.

    This is used by both create_server() (Smithery playground) and
    create_http_server() (HTTP deployment).

    Returns:
        FastMCP: Raw FastMCP server instance with all tools and resources registered.
    """
    # Initialize MCP server
    app = FastMCP("verifimind-genesis")

    # ===== RESOURCES =====

    @app.resource("genesis://config/master_prompt")
    def get_master_prompt() -> str:
        """
        Genesis Master Prompt v16.1

        Returns the complete Genesis Master Prompt defining roles for X Intelligent,
        Z Guardian, and CS Security agents. This prompt ensures consistent agent
        behavior across all validation workflows.

        URI: genesis://config/master_prompt
        Format: Markdown
        Version: v16.1
        """
        return load_master_prompt()


    @app.resource("genesis://history/latest")
    def get_latest_validation_resource() -> str:
        """
        Latest Validation Result

        Returns the most recent validation result from VerifiMind-PEAS validation
        history. Includes agent perspectives (X, Z, CS), conflict resolution, and
        final verdict.

        URI: genesis://history/latest
        Format: JSON
        """
        latest = get_latest_validation()
        return json.dumps(latest, indent=2)


    @app.resource("genesis://history/all")
    def get_all_validations() -> str:
        """
        Complete Validation History

        Returns the complete validation history including all past validations,
        metadata, and statistics. Useful for analyzing validation trends and
        decision patterns over time.

        URI: genesis://history/all
        Format: JSON
        """
        history = load_validation_history()
        return json.dumps(history, indent=2)


    @app.resource("genesis://state/project_info")
    def get_project_info_resource() -> str:
        """
        Project Information

        Returns metadata about the VerifiMind-PEAS project including architecture,
        agent roles, version information, and documentation links.

        URI: genesis://state/project_info
        Format: JSON
        """
        info = get_project_info()
        return json.dumps(info, indent=2)


    # ===== TOOLS =====

    @app.tool()
    async def consult_agent_x(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Consult X Intelligent agent for innovation and strategy analysis.

        X Intelligent specializes in:
        - Innovation potential assessment
        - Strategic value analysis
        - Market opportunity identification
        - Competitive positioning
        - Growth potential evaluation

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background

        Returns:
            Structured analysis with reasoning chain, scores, and recommendations
        """
        try:
            from .models import Concept
            from .agents import XAgent
            from .llm import get_provider

            # Create concept
            concept = Concept(
                name=concept_name,
                description=concept_description,
                context=context
            )

            # Get LLM provider (use session config if available, fallback to env vars)
            try:
                if ctx and ctx.session_config:
                    config = ctx.session_config

                    # Use session config to select provider
                    if config.llm_provider == "openai" and config.openai_api_key:
                        from .llm import OpenAIProvider
                        provider = OpenAIProvider(api_key=config.openai_api_key)
                    elif config.llm_provider == "anthropic" and config.anthropic_api_key:
                        from .llm import AnthropicProvider
                        provider = AnthropicProvider(api_key=config.anthropic_api_key)
                    else:
                        # Fallback to mock provider if no keys provided
                        from .llm import MockProvider
                        provider = MockProvider()
                else:
                    # No session config - use environment variables
                    provider = get_provider()

            except ValueError:
                # No API key configured - return mock response for testing
                from .llm import MockProvider
                provider = MockProvider()

            # Create agent and analyze
            agent = XAgent(llm_provider=provider)
            result = await agent.analyze(concept)

            return {
                "agent": "X Intelligent",
                "concept": concept_name,
                "reasoning_steps": [
                    {"step": s.step_number, "thought": s.thought, "confidence": s.confidence}
                    for s in result.reasoning_steps
                ],
                "innovation_score": result.innovation_score,
                "strategic_value": result.strategic_value,
                "opportunities": result.opportunities,
                "risks": result.risks,
                "recommendation": result.recommendation,
                "confidence": result.confidence
            }

        except Exception as e:
            return {
                "agent": "X Intelligent",
                "status": "error",
                "error": str(e),
                "concept": concept_name
            }


    @app.tool()
    async def consult_agent_z(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        prior_reasoning: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Consult Z Guardian agent for ethical review and Z-Protocol enforcement.

        Z Guardian specializes in:
        - Ethical implications assessment
        - Privacy and data protection review
        - Bias and fairness analysis
        - Social impact evaluation
        - Z-Protocol compliance verification

        Z Guardian has VETO POWER. If veto_triggered is True, the concept
        should not proceed as it crosses ethical red lines.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            prior_reasoning: Optional reasoning from X agent to consider

        Returns:
            Structured analysis with reasoning chain, ethics score, and veto status
        """
        try:
            from .models import Concept, PriorReasoning, ChainOfThought, ReasoningStep
            from .agents import ZAgent
            from .llm import get_provider

            # Create concept
            concept = Concept(
                name=concept_name,
                description=concept_description,
                context=context
            )

            # Parse prior reasoning if provided
            prior = None
            if prior_reasoning:
                # Create a simple prior reasoning object
                prior = PriorReasoning()
                prior.add(ChainOfThought(
                    agent_id="X",
                    agent_name="X Intelligent",
                    concept_name=concept_name,
                    reasoning_steps=[ReasoningStep(step_number=1, thought=prior_reasoning)],
                    final_conclusion="See prior reasoning above",
                    overall_confidence=0.8
                ))

            # Get LLM provider (use session config if available, fallback to env vars)
            try:
                if ctx and ctx.session_config:
                    config = ctx.session_config

                    # Use session config to select provider
                    if config.llm_provider == "openai" and config.openai_api_key:
                        from .llm import OpenAIProvider
                        provider = OpenAIProvider(api_key=config.openai_api_key)
                    elif config.llm_provider == "anthropic" and config.anthropic_api_key:
                        from .llm import AnthropicProvider
                        provider = AnthropicProvider(api_key=config.anthropic_api_key)
                    else:
                        # Fallback to mock provider if no keys provided
                        from .llm import MockProvider
                        provider = MockProvider()
                else:
                    # No session config - use environment variables
                    provider = get_provider()

            except ValueError:
                # No API key configured - return mock response for testing
                from .llm import MockProvider
                provider = MockProvider()

            # Create agent and analyze
            agent = ZAgent(llm_provider=provider)
            result = await agent.analyze(concept, prior)

            return {
                "agent": "Z Guardian",
                "concept": concept_name,
                "reasoning_steps": [
                    {"step": s.step_number, "thought": s.thought, "confidence": s.confidence}
                    for s in result.reasoning_steps
                ],
                "ethics_score": result.ethics_score,
                "z_protocol_compliance": result.z_protocol_compliance,
                "ethical_concerns": result.ethical_concerns,
                "mitigation_measures": result.mitigation_measures,
                "recommendation": result.recommendation,
                "veto_triggered": result.veto_triggered,
                "confidence": result.confidence
            }

        except Exception as e:
            return {
                "agent": "Z Guardian",
                "status": "error",
                "error": str(e),
                "concept": concept_name
            }


    @app.tool()
    async def consult_agent_cs(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        prior_reasoning: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Consult CS Security agent for security validation and Socratic interrogation.

        CS Security specializes in:
        - Security vulnerability assessment
        - Attack vector identification
        - Data security review
        - System integrity analysis
        - Socratic questioning (challenging assumptions)

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            prior_reasoning: Optional reasoning from X and Z agents to consider

        Returns:
            Structured analysis with security score, vulnerabilities, and Socratic questions
        """
        try:
            from .models import Concept, PriorReasoning, ChainOfThought, ReasoningStep
            from .agents import CSAgent
            from .llm import get_provider

            # Create concept
            concept = Concept(
                name=concept_name,
                description=concept_description,
                context=context
            )

            # Parse prior reasoning if provided
            prior = None
            if prior_reasoning:
                prior = PriorReasoning()
                prior.add(ChainOfThought(
                    agent_id="XZ",
                    agent_name="X Intelligent & Z Guardian",
                    concept_name=concept_name,
                    reasoning_steps=[ReasoningStep(step_number=1, thought=prior_reasoning)],
                    final_conclusion="See prior reasoning above",
                    overall_confidence=0.8
                ))

            # Get LLM provider (use session config if available, fallback to env vars)
            try:
                if ctx and ctx.session_config:
                    config = ctx.session_config

                    # Use session config to select provider
                    if config.llm_provider == "openai" and config.openai_api_key:
                        from .llm import OpenAIProvider
                        provider = OpenAIProvider(api_key=config.openai_api_key)
                    elif config.llm_provider == "anthropic" and config.anthropic_api_key:
                        from .llm import AnthropicProvider
                        provider = AnthropicProvider(api_key=config.anthropic_api_key)
                    else:
                        # Fallback to mock provider if no keys provided
                        from .llm import MockProvider
                        provider = MockProvider()
                else:
                    # No session config - use environment variables
                    provider = get_provider()

            except ValueError:
                # No API key configured - return mock response for testing
                from .llm import MockProvider
                provider = MockProvider()

            # Create agent and analyze
            agent = CSAgent(llm_provider=provider)
            result = await agent.analyze(concept, prior)

            return {
                "agent": "CS Security",
                "concept": concept_name,
                "reasoning_steps": [
                    {"step": s.step_number, "thought": s.thought, "confidence": s.confidence}
                    for s in result.reasoning_steps
                ],
                "security_score": result.security_score,
                "vulnerabilities": result.vulnerabilities,
                "attack_vectors": result.attack_vectors,
                "security_recommendations": result.security_recommendations,
                "socratic_questions": result.socratic_questions,
                "recommendation": result.recommendation,
                "confidence": result.confidence
            }

        except Exception as e:
            return {
                "agent": "CS Security",
                "status": "error",
                "error": str(e),
                "concept": concept_name
            }


    @app.tool()
    async def run_full_trinity(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        save_to_history: bool = True,
        ctx: Context = None
    ) -> dict:
        """
        Run complete X → Z → CS Trinity validation with Chain of Thought.

        This tool orchestrates all three agents in sequence:
        1. X Intelligent analyzes innovation and strategy
        2. Z Guardian reviews ethics (sees X's reasoning)
        3. CS Security validates security (sees X and Z reasoning)
        4. Results are synthesized into a unified assessment

        Each agent sees the reasoning of previous agents, enabling
        true collaborative analysis with full transparency.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            save_to_history: Whether to save result to validation history (default: True)

        Returns:
            Complete Trinity validation result with all agent analyses and synthesis
        """
        try:
            from .models import Concept, PriorReasoning
            from .agents import XAgent, ZAgent, CSAgent
            from .llm import get_provider
            from .utils import create_trinity_result

            # Create concept
            concept = Concept(
                name=concept_name,
                description=concept_description,
                context=context
            )

            # Get LLM provider (use session config if available, fallback to env vars)
            try:
                if ctx and ctx.session_config:
                    config = ctx.session_config

                    # Use session config to select provider
                    if config.llm_provider == "openai" and config.openai_api_key:
                        from .llm import OpenAIProvider
                        provider = OpenAIProvider(api_key=config.openai_api_key)
                    elif config.llm_provider == "anthropic" and config.anthropic_api_key:
                        from .llm import AnthropicProvider
                        provider = AnthropicProvider(api_key=config.anthropic_api_key)
                    else:
                        # Fallback to mock provider if no keys provided
                        from .llm import MockProvider
                        provider = MockProvider()
                else:
                    # No session config - use environment variables
                    provider = get_provider()

            except ValueError:
                # No API key configured - return mock response for testing
                from .llm import MockProvider
                provider = MockProvider()

            # Initialize agents
            x_agent = XAgent(llm_provider=provider)
            z_agent = ZAgent(llm_provider=provider)
            cs_agent = CSAgent(llm_provider=provider)

            # Step 1: X Agent analysis (no prior reasoning)
            x_result = await x_agent.analyze(concept)
            x_cot = x_result.to_chain_of_thought(concept_name)

            # Step 2: Z Agent analysis (sees X's reasoning)
            z_prior = PriorReasoning()
            z_prior.add(x_cot)
            z_result = await z_agent.analyze(concept, z_prior)
            z_cot = z_result.to_chain_of_thought(concept_name)

            # Step 3: CS Agent analysis (sees X and Z reasoning)
            cs_prior = PriorReasoning()
            cs_prior.add(x_cot)
            cs_prior.add(z_cot)
            cs_result = await cs_agent.analyze(concept, cs_prior)

            # Step 4: Create Trinity result
            trinity_result = create_trinity_result(
                concept_name=concept_name,
                concept_description=concept_description,
                x_result=x_result,
                z_result=z_result,
                cs_result=cs_result
            )

            # Save to history if requested
            if save_to_history:
                history = load_validation_history()
                history["validations"].append(trinity_result.model_dump())
                history["metadata"]["total_validations"] = len(history["validations"])
                history["metadata"]["last_updated"] = str(trinity_result.completed_at)
                save_validation_history(history)

            # Return result
            return {
                "validation_id": trinity_result.validation_id,
                "concept_name": concept_name,
                "x_analysis": {
                    "innovation_score": x_result.innovation_score,
                    "strategic_value": x_result.strategic_value,
                    "recommendation": x_result.recommendation,
                    "confidence": x_result.confidence
                },
                "z_analysis": {
                    "ethics_score": z_result.ethics_score,
                    "z_protocol_compliance": z_result.z_protocol_compliance,
                    "veto_triggered": z_result.veto_triggered,
                    "recommendation": z_result.recommendation,
                    "confidence": z_result.confidence
                },
                "cs_analysis": {
                    "security_score": cs_result.security_score,
                    "vulnerability_count": len(cs_result.vulnerabilities),
                    "recommendation": cs_result.recommendation,
                    "confidence": cs_result.confidence
                },
                "synthesis": {
                    "overall_score": trinity_result.synthesis.overall_score,
                    "recommendation": trinity_result.synthesis.recommendation,
                    "veto_triggered": trinity_result.synthesis.veto_triggered,
                    "strengths": trinity_result.synthesis.strengths[:3],
                    "concerns": trinity_result.synthesis.concerns[:3],
                    "confidence": trinity_result.synthesis.confidence
                },
                "human_decision_required": True,
                "saved_to_history": save_to_history
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "concept": concept_name
            }

    return app


def create_http_server():
    """Create MCP server for HTTP deployment.

    Returns raw FastMCP instance without Smithery wrapper.
    This allows using .http_app() for HTTP/SSE transport.

    Returns:
        FastMCP: Server instance that can be mounted in FastAPI.
    """
    return _create_mcp_instance()


@smithery.server(config_schema=VerifiMindConfig)
def create_server():
    """Create MCP server for Smithery playground/CLI.

    This is wrapped with @smithery.server decorator for session configuration.
    Returns SmitheryFastMCP instance for Smithery's playground mode.

    Returns:
        SmitheryFastMCP: Wrapped server instance for Smithery.
    """
    return _create_mcp_instance()


# Entry point for direct execution
if __name__ == "__main__":
    # For local testing
    import asyncio
    
    print("=" * 60)
    print("Genesis Context Server - Phase 2 (Core Tools)")
    print("=" * 60)
    print("\nTesting resource loading...\n")
    
    # Test Master Prompt loading
    print("1. Testing Master Prompt loading...")
    prompt = load_master_prompt()
    print(f"   ✓ Loaded {len(prompt)} characters")
    print(f"   First 100 chars: {prompt[:100]}...")
    
    # Test validation history loading
    print("\n2. Testing validation history loading...")
    history = load_validation_history()
    print(f"   ✓ Loaded {len(history.get('validations', []))} validations")
    
    # Test latest validation
    print("\n3. Testing latest validation retrieval...")
    latest = get_latest_validation()
    print(f"   ✓ Latest validation status: {latest.get('status', 'N/A')}")
    
    # Test project info
    print("\n4. Testing project info retrieval...")
    info = get_project_info()
    print(f"   ✓ Project: {info['project_name']}")
    print(f"   ✓ Methodology: {info['methodology']}")
    print(f"   ✓ Version: {info['version']}")
    print(f"   ✓ MCP Server Version: {info['mcp_server_version']}")
    
    print("\n" + "=" * 60)
    print("Resources and Tools available:")
    print("=" * 60)
    print("\nResources:")
    print("  - genesis://config/master_prompt")
    print("  - genesis://history/latest")
    print("  - genesis://history/all")
    print("  - genesis://state/project_info")
    print("\nTools:")
    print("  - consult_agent_x(concept_name, concept_description, context)")
    print("  - consult_agent_z(concept_name, concept_description, context, prior_reasoning)")
    print("  - consult_agent_cs(concept_name, concept_description, context, prior_reasoning)")
    print("  - run_full_trinity(concept_name, concept_description, context, save_to_history)")
    print("\n" + "=" * 60)
    print("All tests passed! Server is ready.")
    print("=" * 60)
    print("\nTo run the MCP server:")
    print("  python -m verifimind_mcp.server")
    print("\nTo configure Claude Desktop:")
    print("  See examples/claude_desktop_config.json")
    print("=" * 60)
