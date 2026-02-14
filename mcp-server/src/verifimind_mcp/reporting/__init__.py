"""
Reporting module for VerifiMind-PEAS MCP Server.

Provides Markdown-first report generation from Trinity validation results.
PDF output is deprecated; Markdown is the canonical agent-native format.
"""

from .markdown_reporter import (
    generate_markdown_report,
    generate_markdown_summary,
    generate_yaml_frontmatter,
)

__all__ = [
    "generate_markdown_report",
    "generate_markdown_summary",
    "generate_yaml_frontmatter",
]
