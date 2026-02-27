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
Version: 0.4.5 (BYOK Live — Per-Tool-Call Provider Override)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP, Context
from smithery.decorators import smithery
from pydantic import BaseModel, Field

# Initialize logger for security events
logger = logging.getLogger(__name__)

# v0.4.3 — System Notice: broadcast messages to all MCP users via env var
SYSTEM_NOTICE = os.environ.get("SYSTEM_NOTICE", "")
SERVER_VERSION = "0.4.5"


def wrap_response(response: dict) -> dict:
    """Add system notice and version metadata to every tool response."""
    if SYSTEM_NOTICE:
        response["_system_notice"] = SYSTEM_NOTICE
    response["_server_version"] = SERVER_VERSION
    return response


class VerifiMindConfig(BaseModel):
    """Session configuration for VerifiMind Genesis Server.

    BYOK v0.3.0 - Multi-Provider Support

    Allows users to bring their own API keys for any supported LLM provider.
    Free tier providers (Gemini, Groq, Ollama) are recommended for cost-free usage.
    """
    llm_provider: str = Field(
        default="mock",
        description="LLM provider: 'gemini' (FREE), 'groq' (FREE), 'openai', 'anthropic', 'mistral', 'ollama' (local), or 'mock' (testing)"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional, can also use OPENAI_API_KEY env var)"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key (optional, can also use ANTHROPIC_API_KEY env var)"
    )
    gemini_api_key: str = Field(
        default="",
        description="Gemini API key (optional, can also use GEMINI_API_KEY env var) - FREE tier available!"
    )
    groq_api_key: str = Field(
        default="",
        description="Groq API key (optional, can also use GROQ_API_KEY env var) - FREE tier available!"
    )
    mistral_api_key: str = Field(
        default="",
        description="Mistral API key (optional, can also use MISTRAL_API_KEY env var)"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness: 'standard' or 'strict'"
    )


# Constants - Use robust path resolution for Docker and local environments
def _get_master_prompt_path() -> Path:
    """Find master prompt file in Docker or local environment."""
    # Locations to check (in order of priority):
    # 1. Current working directory (Docker: /app)
    # 2. Parent of package directory
    # 3. Repository root (development)

    candidates = [
        Path.cwd() / "reflexion-master-prompts-v1.1.md",  # Docker: /app/
        Path(__file__).parent.parent.parent / "reflexion-master-prompts-v1.1.md",  # Package parent
        Path(__file__).parent.parent.parent.parent / "reflexion-master-prompts-v1.1.md",  # Repo root
    ]

    for path in candidates:
        if path.exists():
            return path

    # Return first candidate as default (will show error in load_master_prompt)
    return candidates[0]


def _get_history_path() -> Path:
    """Find or create validation history file path."""
    # Use current working directory (Docker: /app, Local: project root)
    return Path.cwd() / "verifimind_history.json"


MASTER_PROMPT_PATH = _get_master_prompt_path()
HISTORY_PATH = _get_history_path()


def load_master_prompt() -> str:
    """Load Genesis Master Prompt from repository."""
    try:
        if MASTER_PROMPT_PATH.exists():
            return MASTER_PROMPT_PATH.read_text(encoding="utf-8")
        else:
            return f"# Genesis Master Prompt v16.1\n\n(Master Prompt file not found at: {MASTER_PROMPT_PATH})\n\nSearched locations:\n- {Path.cwd()}/reflexion-master-prompts-v1.1.md\n- {Path(__file__).parent.parent.parent}/reflexion-master-prompts-v1.1.md"
    except Exception as e:
        return f"# Error Loading Master Prompt\n\nError: {str(e)}\nPath: {MASTER_PROMPT_PATH}"


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
        "mcp_server_version": "0.4.5",
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
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
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

        BYOK (v0.4.5): Pass llm_provider and api_key to use your own LLM.
        If only api_key is provided, the provider is auto-detected from the key prefix.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            llm_provider: Optional LLM provider override ('groq', 'anthropic', 'openai', 'gemini', 'mistral', 'ollama', 'mock')
            api_key: Optional API key for the provider (ephemeral, never stored)

        Returns:
            Structured analysis with reasoning chain, scores, and recommendations
        """
        try:
            from .models import Concept
            from .agents import XAgent
            from .utils import sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"X Agent input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
            )

            # v0.4.5 BYOK: Try ephemeral provider first, fall back to server default
            from .config_helper import get_agent_provider, create_ephemeral_provider
            byok_used = False
            provider = create_ephemeral_provider(llm_provider, api_key, "X")
            if provider is not None:
                byok_used = True
            else:
                provider = get_agent_provider("X", ctx)

            # Create agent and analyze
            agent = XAgent(llm_provider=provider)
            result = await agent.analyze(concept)

            return wrap_response({
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
                "confidence": result.confidence,
                "_inference_quality": getattr(result, '_inference_quality', 'unknown'),
                "_provider_used": provider.get_model_name(),
                "_byok": byok_used
            })

        except Exception as e:
            return wrap_response({
                "agent": "X Intelligent",
                "status": "error",
                "error": str(e),
                "concept": concept_name
            })


    @app.tool()
    async def consult_agent_z(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        prior_reasoning: Optional[str] = None,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
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

        BYOK (v0.4.5): Pass llm_provider and api_key to use your own LLM.
        If only api_key is provided, the provider is auto-detected from the key prefix.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            prior_reasoning: Optional reasoning from X agent to consider
            llm_provider: Optional LLM provider override ('groq', 'anthropic', 'openai', 'gemini', 'mistral', 'ollama', 'mock')
            api_key: Optional API key for the provider (ephemeral, never stored)

        Returns:
            Structured analysis with reasoning chain, ethics score, and veto status
        """
        try:
            from .models import Concept, PriorReasoning, ChainOfThought, ReasoningStep
            from .agents import ZAgent
            from .utils import sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"Z Agent input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
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

            # v0.4.5 BYOK: Try ephemeral provider first, fall back to server default
            from .config_helper import get_agent_provider, create_ephemeral_provider
            byok_used = False
            provider = create_ephemeral_provider(llm_provider, api_key, "Z")
            if provider is not None:
                byok_used = True
            else:
                provider = get_agent_provider("Z", ctx)

            # Create agent and analyze
            agent = ZAgent(llm_provider=provider)
            result = await agent.analyze(concept, prior)

            return wrap_response({
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
                "confidence": result.confidence,
                "_inference_quality": getattr(result, '_inference_quality', 'unknown'),
                "_provider_used": provider.get_model_name(),
                "_byok": byok_used
            })

        except Exception as e:
            return wrap_response({
                "agent": "Z Guardian",
                "status": "error",
                "error": str(e),
                "concept": concept_name
            })


    @app.tool()
    async def consult_agent_cs(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        prior_reasoning: Optional[str] = None,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
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

        BYOK (v0.4.5): Pass llm_provider and api_key to use your own LLM.
        If only api_key is provided, the provider is auto-detected from the key prefix.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            prior_reasoning: Optional reasoning from X and Z agents to consider
            llm_provider: Optional LLM provider override ('groq', 'anthropic', 'openai', 'gemini', 'mistral', 'ollama', 'mock')
            api_key: Optional API key for the provider (ephemeral, never stored)

        Returns:
            Structured analysis with security score, vulnerabilities, and Socratic questions
        """
        try:
            from .models import Concept, PriorReasoning, ChainOfThought, ReasoningStep
            from .agents import CSAgent
            from .utils import sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"CS Agent input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
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

            # v0.4.5 BYOK: Try ephemeral provider first, fall back to server default
            from .config_helper import get_agent_provider, create_ephemeral_provider
            byok_used = False
            provider = create_ephemeral_provider(llm_provider, api_key, "CS")
            if provider is not None:
                byok_used = True
            else:
                provider = get_agent_provider("CS", ctx)

            # Create agent and analyze
            agent = CSAgent(llm_provider=provider)
            result = await agent.analyze(concept, prior)

            return wrap_response({
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
                "confidence": result.confidence,
                "_inference_quality": getattr(result, '_inference_quality', 'unknown'),
                "_provider_used": provider.get_model_name(),
                "_byok": byok_used
            })

        except Exception as e:
            return wrap_response({
                "agent": "CS Security",
                "status": "error",
                "error": str(e),
                "concept": concept_name
            })


    @app.tool()
    async def run_full_trinity(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        save_to_history: bool = True,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        x_provider: Optional[str] = None,
        x_api_key: Optional[str] = None,
        z_provider: Optional[str] = None,
        z_api_key: Optional[str] = None,
        cs_provider: Optional[str] = None,
        cs_api_key: Optional[str] = None,
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

        BYOK (v0.4.5): Pass llm_provider/api_key for all agents, or use
        per-agent overrides (x_provider/x_api_key, z_provider/z_api_key,
        cs_provider/cs_api_key). Per-agent params take priority over global.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            save_to_history: Whether to save result to validation history (default: True)
            llm_provider: Optional global LLM provider for all agents
            api_key: Optional global API key for all agents (ephemeral, never stored)
            x_provider: Optional provider override for X agent only
            x_api_key: Optional API key override for X agent only
            z_provider: Optional provider override for Z agent only
            z_api_key: Optional API key override for Z agent only
            cs_provider: Optional provider override for CS agent only
            cs_api_key: Optional API key override for CS agent only

        Returns:
            Complete Trinity validation result with all agent analyses and synthesis
        """
        # Check Accept header for markdown content negotiation
        output_format = "json"
        if ctx and hasattr(ctx, 'request_context'):
            req_ctx = ctx.request_context
            # RequestContext may be a dict or object — handle both safely
            if isinstance(req_ctx, dict):
                accept = req_ctx.get('accept', '')
            elif hasattr(req_ctx, 'get'):
                accept = req_ctx.get('accept', '')
            else:
                accept = getattr(req_ctx, 'accept', '')
            if 'text/markdown' in str(accept):
                output_format = "markdown"
        try:
            from .models import Concept, PriorReasoning
            from .agents import XAgent, ZAgent, CSAgent
            from .utils import create_trinity_result, sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"Trinity input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
            )

            # v0.4.5 BYOK: Resolve per-agent providers with fallback to global BYOK, then server default
            from .config_helper import get_trinity_providers, create_ephemeral_provider
            byok_status = {}

            agent_byok_params = {
                "X": (x_provider or llm_provider, x_api_key or api_key),
                "Z": (z_provider or llm_provider, z_api_key or api_key),
                "CS": (cs_provider or llm_provider, cs_api_key or api_key),
            }

            resolved_providers = {}
            for agent_id, (prov, key) in agent_byok_params.items():
                ephemeral = create_ephemeral_provider(prov, key, agent_id)
                if ephemeral is not None:
                    resolved_providers[agent_id] = ephemeral
                    byok_status[agent_id] = True
                else:
                    byok_status[agent_id] = False

            # Fill in any agents that didn't get BYOK providers
            server_providers = get_trinity_providers(ctx)
            for agent_id in ("X", "Z", "CS"):
                if agent_id not in resolved_providers:
                    resolved_providers[agent_id] = server_providers[agent_id]

            # Initialize agents with their resolved providers
            x_agent = XAgent(llm_provider=resolved_providers["X"])
            z_agent = ZAgent(llm_provider=resolved_providers["Z"])
            cs_agent = CSAgent(llm_provider=resolved_providers["CS"])

            # v0.4.3.1 C-S-P State: Track inference quality across chain
            chain_status = {}

            # Step 1: X Agent analysis (no prior reasoning)
            x_result = await x_agent.analyze(concept)
            x_quality = getattr(x_result, '_inference_quality', 'unknown')
            chain_status["x_agent"] = x_quality
            logger.info(f"Trinity X stage: quality={x_quality}")
            x_cot = x_result.to_chain_of_thought(concept_name)

            # Step 2: Z Agent analysis (sees X's reasoning)
            z_prior = PriorReasoning()
            z_prior.add(x_cot)
            z_result = await z_agent.analyze(concept, z_prior)
            z_quality = getattr(z_result, '_inference_quality', 'unknown')
            chain_status["z_agent"] = z_quality
            logger.info(f"Trinity Z stage: quality={z_quality}")
            z_cot = z_result.to_chain_of_thought(concept_name)

            # Step 3: CS Agent analysis (sees X and Z reasoning)
            cs_prior = PriorReasoning()
            cs_prior.add(x_cot)
            cs_prior.add(z_cot)
            cs_result = await cs_agent.analyze(concept, cs_prior)
            cs_quality = getattr(cs_result, '_inference_quality', 'unknown')
            chain_status["cs_agent"] = cs_quality
            logger.info(f"Trinity CS stage: quality={cs_quality}")

            # v0.4.3.1 C-S-P Propagation: Compute overall quality
            quality_values = list(chain_status.values())
            if all(v == "real" for v in quality_values):
                overall_quality = "full"
            elif any(v == "fallback" for v in quality_values):
                overall_quality = "degraded"
            else:
                overall_quality = "partial"
            logger.info(f"Trinity chain complete: {chain_status} → {overall_quality}")

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

            # BYOK metadata for response
            _byok_meta = {
                "_byok": any(byok_status.values()),
                "_byok_agents": byok_status,
                "_providers_used": {
                    aid: resolved_providers[aid].get_model_name()
                    for aid in ("X", "Z", "CS")
                },
            }

            # Return result — Markdown-first if requested (v0.4.1)
            if output_format == "markdown":
                from .reporting import generate_markdown_report
                return wrap_response({
                    "format": "markdown",
                    "content": generate_markdown_report(trinity_result),
                    "validation_id": trinity_result.validation_id,
                    "saved_to_history": save_to_history,
                    "_agent_chain_status": chain_status,
                    "_overall_quality": overall_quality,
                    **_byok_meta
                })

            return wrap_response({
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
                "saved_to_history": save_to_history,
                "_agent_chain_status": chain_status,
                "_overall_quality": overall_quality,
                **_byok_meta
            })

        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e),
                "concept": concept_name
            })

    # ===== v0.4.0 TEMPLATE TOOLS =====

    @app.tool()
    async def list_prompt_templates(
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        List available prompt templates with optional filtering.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            agent_id: Filter by agent (X, Z, CS, or 'all')
            category: Filter by category (startup, security, ethics, etc.)
            tags: Comma-separated tags to filter by (e.g., 'genesis:phase-1,default')

        Returns:
            List of templates with metadata
        """
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()

            # Parse tags if provided
            tag_list = None
            if tags:
                tag_list = [t.strip() for t in tags.split(',')]

            templates = registry.list_templates(
                agent_id=agent_id,
                category=category,
                tags=tag_list
            )

            return wrap_response({
                "count": len(templates),
                "filters": {
                    "agent_id": agent_id,
                    "category": category,
                    "tags": tag_list
                },
                "templates": [
                    {
                        "template_id": t.template_id,
                        "name": t.name,
                        "agent_id": t.agent_id,
                        "category": t.category,
                        "version": t.version,
                        "tags": t.tags,
                        "description": t.description,
                        "variable_count": len(t.variables)
                    }
                    for t in templates
                ]
            })

        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })

    @app.tool()
    async def get_prompt_template(
        template_id: str,
        include_content: bool = True,
        ctx: Context = None
    ) -> dict:
        """
        Get a specific prompt template by ID.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            template_id: Unique template identifier
            include_content: Whether to include full template content

        Returns:
            Complete template with all metadata and variables
        """
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()
            template = registry.get_template(template_id)

            if not template:
                return wrap_response({
                    "status": "not_found",
                    "error": f"Template not found: {template_id}",
                    "available_templates": len(registry.list_templates())
                })

            result = {
                "template_id": template.template_id,
                "name": template.name,
                "agent_id": template.agent_id,
                "category": template.category,
                "version": template.version,
                "tags": template.tags,
                "description": template.description,
                "variables": [
                    {
                        "name": v.name,
                        "type_hint": v.type_hint,
                        "required": v.required,
                        "default": v.default,
                        "description": v.description
                    }
                    for v in template.variables
                ],
                "compatible_providers": template.compatible_providers,
                "recommended_temperature": template.recommended_temperature,
                "recommended_max_tokens": template.recommended_max_tokens,
                "changelog": template.changelog
            }

            if include_content:
                result["content"] = template.content

            return wrap_response(result)

        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })

    @app.tool()
    async def export_prompt_template(
        template_id: str,
        format: str = "markdown",
        ctx: Context = None
    ) -> dict:
        """
        Export a prompt template to Markdown or JSON format.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            template_id: Template to export
            format: Export format ('markdown' or 'json')

        Returns:
            Exported template content in specified format
        """
        try:
            from .templates import (
                TemplateRegistry,
                export_template_markdown,
                export_template_json,
            )

            registry = TemplateRegistry()
            template = registry.get_template(template_id)

            if not template:
                return wrap_response({
                    "status": "not_found",
                    "error": f"Template not found: {template_id}"
                })

            format_lower = format.lower()
            if format_lower == "markdown" or format_lower == "md":
                exported = export_template_markdown(template)
                content_type = "text/markdown"
            elif format_lower == "json":
                exported = export_template_json(template)
                content_type = "application/json"
            else:
                return wrap_response({
                    "status": "error",
                    "error": f"Unsupported format: {format}. Use 'markdown' or 'json'"
                })

            return wrap_response({
                "template_id": template_id,
                "format": format_lower,
                "content_type": content_type,
                "exported_content": exported,
                "template_name": template.name,
                "template_version": template.version
            })

        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })

    @app.tool()
    async def register_custom_template(
        name: str,
        agent_id: str,
        content: str,
        category: str = "custom",
        description: Optional[str] = None,
        tags: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Register a new custom prompt template.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            name: Template display name
            agent_id: Target agent (X, Z, CS, or 'all')
            content: Template content with {variable} placeholders
            category: Template category (default: 'custom')
            description: Template description
            tags: Comma-separated tags

        Returns:
            Registered template info with generated ID
        """
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()

            # Parse tags
            tag_list = None
            if tags:
                tag_list = [t.strip() for t in tags.split(',')]

            template = registry.register_custom_template(
                name=name,
                agent_id=agent_id.upper(),
                content=content,
                category=category,
                description=description,
                tags=tag_list
            )

            return wrap_response({
                "status": "success",
                "message": f"Template registered successfully",
                "template_id": template.template_id,
                "name": template.name,
                "agent_id": template.agent_id,
                "category": template.category,
                "tags": template.tags
            })

        except ValueError as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })
        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })

    @app.tool()
    async def import_template_from_url(
        url: str,
        validate: bool = True,
        ctx: Context = None
    ) -> dict:
        """
        Import a prompt template from a URL (GitHub Gist, raw file, etc.).

        v0.4.0 Unified Prompt Templates feature.

        Supports:
        - GitHub Gist URLs
        - Raw GitHub file URLs
        - Any HTTPS URL pointing to JSON/YAML template

        Args:
            url: URL to import template from
            validate: Whether to validate template content (default: True)

        Returns:
            Import result with template info or error details
        """
        try:
            from .templates import (
                import_template_from_url as do_import,
                validate_template_url,
                TemplateRegistry,
            )

            # Validate URL first
            is_valid, source_type, error = validate_template_url(url)
            if not is_valid:
                return {
                    "status": "error",
                    "error": f"Invalid URL: {error}"
                }

            # Import the template
            result = await do_import(url, validate=validate)

            if not result.success:
                return wrap_response({
                    "status": "error",
                    "error": result.error,
                    "warnings": result.warnings
                })

            # Register the imported template
            registry = TemplateRegistry()
            if result.template:
                registry._custom_templates[result.template.template_id] = result.template

            return wrap_response({
                "status": "success",
                "message": "Template imported and registered",
                "source_url": url,
                "source_type": source_type,
                "template_id": result.template.template_id if result.template else None,
                "template_name": result.template.name if result.template else None,
                "warnings": result.warnings
            })

        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })

    @app.tool()
    async def get_template_statistics(
        ctx: Context = None
    ) -> dict:
        """
        Get statistics about the template registry.

        v0.4.0 Unified Prompt Templates feature.

        Returns:
            Statistics including template counts by agent, phase, and type
        """
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()
            stats = registry.get_statistics()

            # Add library info
            libraries = registry.list_libraries()

            return wrap_response({
                "status": "success",
                **stats,
                "libraries": [
                    {
                        "library_id": lib.library_id,
                        "name": lib.name,
                        "template_count": len(lib.templates),
                        "genesis_phase": lib.genesis_phase
                    }
                    for lib in libraries
                ]
            })

        except Exception as e:
            return wrap_response({
                "status": "error",
                "error": str(e)
            })

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
