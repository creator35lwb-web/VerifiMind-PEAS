"""
Template Data Models for VerifiMind-PEAS v0.4.0
================================================

Defines core data structures for the Unified Prompt Template system:
- TemplateVariable: Variable definition with type hints
- PromptTemplate: Template with metadata, variables, version
- TemplateLibraryEntry: Library catalog entry
- ExportFormat/ExportConfig: Export configuration

Author: Alton Lee
Version: 0.4.0
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


class GenesisPhase(str, Enum):
    """Genesis Methodology phases for template alignment."""
    PHASE_1 = "genesis:phase-1"  # Initial Conceptualization (X Agent)
    PHASE_2 = "genesis:phase-2"  # Critical Scrutiny (Z Agent)
    PHASE_3 = "genesis:phase-3"  # External Validation (CS Agent)
    PHASE_4 = "genesis:phase-4"  # Synthesis (Trinity)
    PHASE_5 = "genesis:phase-5"  # Iteration (Reflexion)


class ExportFormat(str, Enum):
    """Supported export formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


class TemplateVariable(BaseModel):
    """
    Variable definition for prompt templates.

    Represents a placeholder in a template that can be filled
    with user-provided values at runtime.
    """
    name: str = Field(
        ...,
        description="Variable name (used as {name} in template)",
        min_length=1,
        max_length=64
    )
    description: str = Field(
        ...,
        description="What this variable represents"
    )
    type_hint: str = Field(
        default="str",
        description="Python type hint: str, int, float, bool, list, dict"
    )
    required: bool = Field(
        default=True,
        description="Whether this variable must be provided"
    )
    default: Optional[Any] = Field(
        default=None,
        description="Default value if not provided"
    )
    examples: Optional[List[str]] = Field(
        default=None,
        description="Example values for documentation"
    )
    validation_pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern for validation (optional)"
    )

    @field_validator('type_hint')
    @classmethod
    def validate_type_hint(cls, v: str) -> str:
        """Validate type hint is a supported Python type."""
        valid_types = {'str', 'int', 'float', 'bool', 'list', 'dict', 'any'}
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid type_hint: {v}. Must be one of: {valid_types}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "concept_name",
                "description": "Name of the concept to analyze",
                "type_hint": "str",
                "required": True,
                "default": None,
                "examples": ["AI Code Review", "Blockchain Voting System"]
            }
        }


class PromptTemplate(BaseModel):
    """
    Prompt Template with metadata, variables, and version control.

    Represents a complete prompt template that can be customized
    with variables and exported in various formats.
    """
    template_id: str = Field(
        ...,
        description="Unique identifier for the template",
        min_length=1,
        max_length=128
    )
    name: str = Field(
        ...,
        description="Human-readable display name"
    )
    agent_id: str = Field(
        ...,
        description="Target agent: 'X', 'Z', 'CS', or 'all'"
    )
    content: str = Field(
        ...,
        description="Template content with {variable} placeholders"
    )
    variables: List[TemplateVariable] = Field(
        default_factory=list,
        description="Variables used in this template"
    )
    version: str = Field(
        default="1.0.0",
        description="Semantic version (MAJOR.MINOR.PATCH)"
    )
    category: str = Field(
        default="general",
        description="Template category (startup, security, ethics, etc.)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags including genesis:phase-N tags"
    )
    changelog: List[str] = Field(
        default_factory=list,
        description="Version history with changes"
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the template"
    )
    author: Optional[str] = Field(
        default=None,
        description="Template author or maintainer"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )

    # Provider Compatibility Matrix (BYOK v0.3.0 integration)
    compatible_providers: List[str] = Field(
        default=["gemini", "openai", "anthropic", "groq", "mistral", "ollama", "mock"],
        description="LLM providers compatible with this template"
    )
    min_context_length: int = Field(
        default=4096,
        ge=1024,
        le=128000,
        description="Minimum context window required"
    )
    recommended_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Recommended temperature for LLM calls"
    )
    recommended_max_tokens: int = Field(
        default=4096,
        ge=100,
        le=32000,
        description="Recommended max tokens for response"
    )

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validate agent_id is a valid agent or 'all'."""
        valid_agents = {'X', 'Z', 'CS', 'all'}
        if v.upper() not in valid_agents and v.lower() != 'all':
            raise ValueError(f"Invalid agent_id: {v}. Must be one of: {valid_agents}")
        return v.upper() if v.upper() in valid_agents else 'all'

    def get_genesis_phase(self) -> Optional[GenesisPhase]:
        """Extract Genesis phase from tags if present."""
        for tag in self.tags:
            if tag.startswith("genesis:phase-"):
                try:
                    return GenesisPhase(tag)
                except ValueError:
                    pass
        return None

    def get_required_variables(self) -> List[TemplateVariable]:
        """Get list of required variables."""
        return [v for v in self.variables if v.required]

    def get_optional_variables(self) -> List[TemplateVariable]:
        """Get list of optional variables."""
        return [v for v in self.variables if not v.required]

    def render(self, **kwargs: Any) -> str:
        """
        Render the template with provided variable values.

        Args:
            **kwargs: Variable name=value pairs

        Returns:
            Rendered template string

        Raises:
            ValueError: If required variables are missing
        """
        # Check required variables
        missing = []
        for var in self.get_required_variables():
            if var.name not in kwargs and var.default is None:
                missing.append(var.name)

        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Build render context with defaults
        context = {}
        for var in self.variables:
            if var.name in kwargs:
                context[var.name] = kwargs[var.name]
            elif var.default is not None:
                context[var.name] = var.default
            elif not var.required:
                context[var.name] = ""

        # Render template
        try:
            return self.content.format(**context)
        except KeyError as e:
            raise ValueError(f"Unknown variable in template: {e}")

    def is_compatible_with_provider(self, provider: str) -> bool:
        """Check if template is compatible with a provider."""
        return provider.lower() in [p.lower() for p in self.compatible_providers]

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "startup-validation-x",
                "name": "Startup Concept Validation",
                "agent_id": "X",
                "content": "Analyze {concept_name}: {concept_description}",
                "version": "1.0.0",
                "category": "startup",
                "tags": ["genesis:phase-1", "innovation", "startup"]
            }
        }


class TemplateLibraryEntry(BaseModel):
    """
    Library catalog entry for a template collection.

    Represents metadata about a template library file
    without loading the full template content.
    """
    library_id: str = Field(
        ...,
        description="Unique library identifier"
    )
    name: str = Field(
        ...,
        description="Library display name"
    )
    description: str = Field(
        default="",
        description="Library description"
    )
    templates: List[str] = Field(
        default_factory=list,
        description="List of template IDs in this library"
    )
    agent_id: str = Field(
        default="all",
        description="Primary agent for this library"
    )
    genesis_phase: Optional[str] = Field(
        default=None,
        description="Genesis phase tag (genesis:phase-N)"
    )
    category: str = Field(
        default="general",
        description="Library category"
    )
    version: str = Field(
        default="1.0.0",
        description="Library version"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Path to library YAML file"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "library_id": "startup_validation",
                "name": "Startup Validation Templates",
                "description": "Templates for validating startup concepts",
                "templates": ["startup-validation-x", "startup-quick-check"],
                "agent_id": "X",
                "genesis_phase": "genesis:phase-1",
                "category": "startup"
            }
        }


class ExportConfig(BaseModel):
    """
    Configuration for template export.
    """
    format: ExportFormat = Field(
        default=ExportFormat.MARKDOWN,
        description="Export format"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include template metadata in export"
    )
    include_variables: bool = Field(
        default=True,
        description="Include variable documentation"
    )
    include_changelog: bool = Field(
        default=False,
        description="Include version changelog"
    )
    include_compatibility: bool = Field(
        default=True,
        description="Include provider compatibility matrix"
    )
    include_examples: bool = Field(
        default=True,
        description="Include variable examples"
    )


class ImportResult(BaseModel):
    """
    Result of importing a template from URL.
    """
    success: bool = Field(
        ...,
        description="Whether import was successful"
    )
    template: Optional[PromptTemplate] = Field(
        default=None,
        description="Imported template if successful"
    )
    source_url: str = Field(
        ...,
        description="Source URL"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if import failed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings during import"
    )
    imported_at: datetime = Field(
        default_factory=datetime.now,
        description="Import timestamp"
    )
