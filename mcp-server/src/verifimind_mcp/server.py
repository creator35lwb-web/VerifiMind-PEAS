"""
Genesis Context Server - Week 1-2 MVP
======================================

MCP server exposing VerifiMind-PEAS Genesis Methodology context as Resources.

This MVP focuses on solving the "Linkage Point" problem: enabling multiple AI models
to reference the exact same context without human re-transmission.

Resources Exposed:
- genesis://config/master_prompt - Genesis Master Prompt v16.1
- genesis://history/latest - Most recent validation result
- genesis://history/all - Complete validation history
- genesis://state/project_info - Current project information

Author: Alton Lee
Version: 0.1.0 (MVP - Resources only)
"""

import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
app = FastMCP("verifimind-genesis")

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
        "agents": {
            "X": {
                "name": "X Intelligent",
                "role": "Innovation and Strategy Engine",
                "model": "Gemini"
            },
            "Z": {
                "name": "Z Guardian",
                "role": "Ethical Review and Z-Protocol Enforcement",
                "model": "Claude"
            },
            "CS": {
                "name": "CS Security",
                "role": "Security Validation and Socratic Interrogation",
                "model": "Perplexity"
            }
        },
        "master_prompt_version": "v16.1",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "documentation": "https://github.com/creator35lwb-web/VerifiMind-PEAS/docs",
        "white_paper": "https://github.com/creator35lwb-web/VerifiMind-PEAS/docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md"
    }


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


# Note: FastMCP automatically handles list_resources() based on @app.resource() decorators
# No need to manually implement list_resources()


# Entry point for direct execution
if __name__ == "__main__":
    # For local testing
    import asyncio
    
    print("=" * 60)
    print("Genesis Context Server - Week 1-2 MVP")
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
    
    print("\n" + "=" * 60)
    print("All tests passed! Server is ready.")
    print("=" * 60)
    print("\nTo run the MCP server:")
    print("  python -m verifimind_mcp.server")
    print("\nTo configure Claude Desktop:")
    print("  See examples/claude_desktop_config.json")
    print("=" * 60)
