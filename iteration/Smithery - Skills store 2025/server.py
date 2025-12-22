"""
Genesis Context Server - Phase 2 (Core Tools)
==============================================
MCP server exposing VerifiMind-PEAS Genesis Methodology context.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field

class VerifiMindConfig(BaseModel):
    llm_provider: str = Field(default="mock")
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    validation_mode: str = Field(default="standard")

# CRITICAL FIX: Resolves to the project root (/app in Docker)
REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_PROMPT_PATH = REPO_ROOT / "reflexion-master-prompts-v1.1.md"
HISTORY_PATH = REPO_ROOT / "verifimind_history.json"

def load_master_prompt() -> str:
    try:
        if MASTER_PROMPT_PATH.exists():
            return MASTER_PROMPT_PATH.read_text(encoding="utf-8")
        return f"# Genesis Master Prompt v16.1\n\n(File not found at {MASTER_PROMPT_PATH})"
    except Exception as e:
        return f"# Error\n\n{str(e)}"

def load_validation_history() -> dict[str, Any]:
    try:
        if HISTORY_PATH.exists():
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"validations": [], "metadata": {"total_validations": 0}}
    except Exception as e:
        return {"error": str(e), "validations": []}

@smithery.server(config_schema=VerifiMindConfig)
def create_server():
    app = FastMCP("verifimind-genesis")

    @app.resource("genesis://config/master_prompt")
    def get_master_prompt() -> str:
        return load_master_prompt()

    @app.resource("genesis://history/latest")
    def get_latest_validation_resource() -> str:
        history = load_validation_history()
        validations = history.get("validations", [])
        latest = validations[-1] if validations else {"status": "no_validations"}
        return json.dumps(latest, indent=2)

    @app.tool()
    async def consult_agent_x(concept_name: str, concept_description: str) -> dict:
        return {"agent": "X Intelligent", "concept": concept_name, "status": "Ready"}

    return app

if __name__ == "__main__":
    # CRITICAL FIX: Actually starts the server process
    mcp_app = create_server()
    mcp_app.run()
