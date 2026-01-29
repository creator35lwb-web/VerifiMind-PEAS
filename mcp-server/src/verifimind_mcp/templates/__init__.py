"""
VerifiMind-PEAS Template System v0.4.0
======================================

Unified Prompt Template system for the Genesis Methodology.

Features:
- Prompt Export (Markdown/JSON)
- Template Library (Pre-built templates)
- Custom Variables (User-defined placeholders)
- Version Control (Template versioning)
- Import from URL (Community sharing)
- Provider Compatibility (Multi-LLM awareness)
- Genesis Methodology Tags (Phase alignment)

Author: Alton Lee
Version: 0.4.0
"""

from .models import (
    TemplateVariable,
    PromptTemplate,
    TemplateLibraryEntry,
    ExportFormat,
    ExportConfig,
    GenesisPhase,
)

from .registry import TemplateRegistry

from .export import (
    export_template_markdown,
    export_template_json,
)

from .import_url import (
    import_template_from_url,
    validate_template_url,
)

__all__ = [
    # Models
    "TemplateVariable",
    "PromptTemplate",
    "TemplateLibraryEntry",
    "ExportFormat",
    "ExportConfig",
    "GenesisPhase",
    # Registry
    "TemplateRegistry",
    # Export
    "export_template_markdown",
    "export_template_json",
    # Import
    "import_template_from_url",
    "validate_template_url",
]

__version__ = "0.4.0"
