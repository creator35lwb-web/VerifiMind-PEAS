"""
Template Export Utilities for VerifiMind-PEAS v0.4.0
=====================================================

Export templates to Markdown and JSON formats with
full metadata and variable documentation.

Author: Alton Lee
Version: 0.4.0
"""

import json
from datetime import datetime
from typing import Optional

from .models import (
    PromptTemplate,
    ExportFormat,
    ExportConfig,
)


def export_template_markdown(
    template: PromptTemplate,
    config: Optional[ExportConfig] = None
) -> str:
    """
    Export a template to Markdown format.

    Args:
        template: Template to export
        config: Export configuration (uses defaults if None)

    Returns:
        Markdown string representation
    """
    if config is None:
        config = ExportConfig(format=ExportFormat.MARKDOWN)

    lines = []

    # Header
    lines.append(f"# {template.name}")
    lines.append("")
    lines.append(f"**Template ID:** `{template.template_id}`")
    lines.append(f"**Version:** {template.version}")
    lines.append(f"**Agent:** {template.agent_id}")
    lines.append(f"**Category:** {template.category}")
    lines.append("")

    # Description
    if template.description:
        lines.append("## Description")
        lines.append("")
        lines.append(template.description)
        lines.append("")

    # Genesis Phase
    genesis_phase = template.get_genesis_phase()
    if genesis_phase:
        lines.append(f"**Genesis Phase:** {genesis_phase.value}")
        lines.append("")

    # Tags
    if template.tags:
        lines.append("## Tags")
        lines.append("")
        lines.append(", ".join([f"`{tag}`" for tag in template.tags]))
        lines.append("")

    # Variables Documentation
    if config.include_variables and template.variables:
        lines.append("## Variables")
        lines.append("")
        lines.append("| Variable | Type | Required | Default | Description |")
        lines.append("|----------|------|----------|---------|-------------|")

        for var in template.variables:
            required = "Yes" if var.required else "No"
            default = f"`{var.default}`" if var.default is not None else "-"
            lines.append(
                f"| `{var.name}` | {var.type_hint} | {required} | {default} | {var.description} |"
            )
        lines.append("")

        # Variable Examples
        if config.include_examples:
            has_examples = any(v.examples for v in template.variables)
            if has_examples:
                lines.append("### Variable Examples")
                lines.append("")
                for var in template.variables:
                    if var.examples:
                        lines.append(f"**{var.name}:**")
                        for example in var.examples:
                            lines.append(f"- `{example}`")
                        lines.append("")

    # Template Content
    lines.append("## Template Content")
    lines.append("")
    lines.append("```")
    lines.append(template.content)
    lines.append("```")
    lines.append("")

    # Provider Compatibility
    if config.include_compatibility:
        lines.append("## Provider Compatibility")
        lines.append("")
        lines.append(f"**Compatible Providers:** {', '.join(template.compatible_providers)}")
        lines.append(f"**Min Context Length:** {template.min_context_length:,} tokens")
        lines.append(f"**Recommended Temperature:** {template.recommended_temperature}")
        lines.append(f"**Recommended Max Tokens:** {template.recommended_max_tokens:,}")
        lines.append("")

    # Changelog
    if config.include_changelog and template.changelog:
        lines.append("## Changelog")
        lines.append("")
        for entry in template.changelog:
            lines.append(f"- {entry}")
        lines.append("")

    # Metadata
    if config.include_metadata:
        lines.append("## Metadata")
        lines.append("")
        if template.author:
            lines.append(f"**Author:** {template.author}")
        lines.append(f"**Created:** {template.created_at.isoformat()}")
        lines.append(f"**Updated:** {template.updated_at.isoformat()}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Exported from VerifiMind-PEAS Template System v0.4.0*")
    lines.append(f"*Export Date: {datetime.now().isoformat()}*")

    return "\n".join(lines)


def export_template_json(
    template: PromptTemplate,
    config: Optional[ExportConfig] = None,
    indent: int = 2
) -> str:
    """
    Export a template to JSON format.

    Args:
        template: Template to export
        config: Export configuration (uses defaults if None)
        indent: JSON indentation level

    Returns:
        JSON string representation
    """
    if config is None:
        config = ExportConfig(format=ExportFormat.JSON)

    # Build export data
    data = {
        "template_id": template.template_id,
        "name": template.name,
        "agent_id": template.agent_id,
        "content": template.content,
        "version": template.version,
        "category": template.category,
        "tags": template.tags,
    }

    # Optional: description
    if template.description:
        data["description"] = template.description

    # Variables
    if config.include_variables:
        data["variables"] = []
        for var in template.variables:
            var_data = {
                "name": var.name,
                "description": var.description,
                "type_hint": var.type_hint,
                "required": var.required,
            }
            if var.default is not None:
                var_data["default"] = var.default
            if config.include_examples and var.examples:
                var_data["examples"] = var.examples
            if var.validation_pattern:
                var_data["validation_pattern"] = var.validation_pattern
            data["variables"].append(var_data)

    # Provider compatibility
    if config.include_compatibility:
        data["compatibility"] = {
            "providers": template.compatible_providers,
            "min_context_length": template.min_context_length,
            "recommended_temperature": template.recommended_temperature,
            "recommended_max_tokens": template.recommended_max_tokens,
        }

    # Changelog
    if config.include_changelog and template.changelog:
        data["changelog"] = template.changelog

    # Metadata
    if config.include_metadata:
        data["metadata"] = {
            "author": template.author,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "genesis_phase": template.get_genesis_phase().value if template.get_genesis_phase() else None,
        }

    # Export metadata
    data["_export"] = {
        "format": "verifimind-template-v1",
        "exported_at": datetime.now().isoformat(),
        "verifimind_version": "0.4.0",
    }

    return json.dumps(data, indent=indent, default=str)


def export_template(
    template: PromptTemplate,
    format: ExportFormat = ExportFormat.MARKDOWN,
    config: Optional[ExportConfig] = None
) -> str:
    """
    Export a template in the specified format.

    Args:
        template: Template to export
        format: Export format (markdown, json, yaml)
        config: Export configuration

    Returns:
        Exported template string
    """
    if config is None:
        config = ExportConfig(format=format)

    if format == ExportFormat.MARKDOWN:
        return export_template_markdown(template, config)
    elif format == ExportFormat.JSON:
        return export_template_json(template, config)
    elif format == ExportFormat.YAML:
        # YAML export uses JSON-like structure
        import yaml
        json_str = export_template_json(template, config)
        data = json.loads(json_str)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"Unsupported export format: {format}")
