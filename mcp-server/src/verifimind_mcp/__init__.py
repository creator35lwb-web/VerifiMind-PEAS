"""
VerifiMind MCP Server
=====================

Model Context Protocol server for VerifiMind-PEAS Genesis Methodology.

Exposes the RefleXion Trinity (X-Z-CS) validation framework through MCP primitives:
- Resources: Master Prompts, project history, validation state
- Tools: Agent consultation (X, Z, CS), full Trinity analysis
- Prompts: Standardized validation workflows

Author: Alton Lee
License: MIT
Version: 0.1.0 (Week 1-2 MVP - Genesis Context Server)
"""

__version__ = "0.1.0"
__author__ = "Alton Lee"
__license__ = "MIT"

from .server import create_server, create_http_server

# For backwards compatibility, create an app instance
app = create_server()

__all__ = ["app", "create_server", "create_http_server"]
