"""
Unit tests for VerifiMind-PEAS Template System v0.4.0
======================================================

Tests for:
- TemplateVariable model
- PromptTemplate model
- TemplateRegistry
- Export functionality
"""

import pytest
import json

from verifimind_mcp.templates.models import (
    TemplateVariable,
    PromptTemplate,
    TemplateLibraryEntry,
    ExportFormat,
    ExportConfig,
    GenesisPhase,
)
from verifimind_mcp.templates.registry import TemplateRegistry, get_registry
from verifimind_mcp.templates.export import (
    export_template_markdown,
    export_template_json,
    export_template,
)


# ===== TemplateVariable Tests =====

@pytest.fixture
def sample_variable():
    """Create a sample template variable."""
    return TemplateVariable(
        name="concept_name",
        description="Name of the concept to analyze",
        type_hint="str",
        required=True,
        default=None,
        examples=["AI Code Review", "Blockchain Voting"]
    )


@pytest.mark.unit
def test_template_variable_creation(sample_variable):
    """Test TemplateVariable creation."""
    assert sample_variable.name == "concept_name"
    assert sample_variable.type_hint == "str"
    assert sample_variable.required is True
    assert sample_variable.default is None
    assert len(sample_variable.examples) == 2


@pytest.mark.unit
def test_template_variable_with_default():
    """Test TemplateVariable with default value."""
    var = TemplateVariable(
        name="context",
        description="Additional context",
        type_hint="str",
        required=False,
        default="No context provided"
    )
    assert var.required is False
    assert var.default == "No context provided"


@pytest.mark.unit
def test_template_variable_type_hint_validation():
    """Test type_hint validation."""
    # Valid types should work
    for valid_type in ['str', 'int', 'float', 'bool', 'list', 'dict', 'any']:
        var = TemplateVariable(
            name="test",
            description="Test variable",
            type_hint=valid_type
        )
        assert var.type_hint == valid_type.lower()

    # Invalid type should raise error
    with pytest.raises(ValueError):
        TemplateVariable(
            name="test",
            description="Test variable",
            type_hint="invalid_type"
        )


# ===== PromptTemplate Tests =====

@pytest.fixture
def sample_template():
    """Create a sample prompt template."""
    return PromptTemplate(
        template_id="test-template-001",
        name="Test Template",
        agent_id="X",
        content="Analyze {concept_name}: {concept_description}",
        variables=[
            TemplateVariable(
                name="concept_name",
                description="Concept name",
                type_hint="str",
                required=True
            ),
            TemplateVariable(
                name="concept_description",
                description="Concept description",
                type_hint="str",
                required=True
            )
        ],
        version="1.0.0",
        category="test",
        tags=["genesis:phase-1", "test"],
        description="A test template",
        author="Test Author"
    )


@pytest.mark.unit
def test_prompt_template_creation(sample_template):
    """Test PromptTemplate creation."""
    assert sample_template.template_id == "test-template-001"
    assert sample_template.name == "Test Template"
    assert sample_template.agent_id == "X"
    assert len(sample_template.variables) == 2
    assert sample_template.version == "1.0.0"


@pytest.mark.unit
def test_prompt_template_agent_validation():
    """Test agent_id validation."""
    # Valid agents
    for agent in ['X', 'Z', 'CS', 'all']:
        t = PromptTemplate(
            template_id="test",
            name="Test",
            agent_id=agent,
            content="Test content"
        )
        assert t.agent_id in ['X', 'Z', 'CS', 'all', 'ALL']

    # Invalid agent should raise
    with pytest.raises(ValueError):
        PromptTemplate(
            template_id="test",
            name="Test",
            agent_id="invalid",
            content="Test content"
        )


@pytest.mark.unit
def test_prompt_template_get_genesis_phase(sample_template):
    """Test Genesis phase extraction from tags."""
    phase = sample_template.get_genesis_phase()
    assert phase == GenesisPhase.PHASE_1


@pytest.mark.unit
def test_prompt_template_get_required_variables(sample_template):
    """Test getting required variables."""
    required = sample_template.get_required_variables()
    assert len(required) == 2
    assert all(v.required for v in required)


@pytest.mark.unit
def test_prompt_template_render(sample_template):
    """Test template rendering."""
    rendered = sample_template.render(
        concept_name="AI Assistant",
        concept_description="An AI that helps with coding"
    )
    assert "AI Assistant" in rendered
    assert "An AI that helps with coding" in rendered


@pytest.mark.unit
def test_prompt_template_render_missing_required():
    """Test rendering with missing required variable."""
    template = PromptTemplate(
        template_id="test",
        name="Test",
        agent_id="X",
        content="{required_var}",
        variables=[
            TemplateVariable(
                name="required_var",
                description="Required",
                required=True
            )
        ]
    )
    with pytest.raises(ValueError) as exc_info:
        template.render()
    assert "Missing required variables" in str(exc_info.value)


@pytest.mark.unit
def test_prompt_template_render_with_defaults():
    """Test rendering uses default values."""
    template = PromptTemplate(
        template_id="test",
        name="Test",
        agent_id="X",
        content="{optional_var}",
        variables=[
            TemplateVariable(
                name="optional_var",
                description="Optional",
                required=False,
                default="default_value"
            )
        ]
    )
    rendered = template.render()
    assert rendered == "default_value"


@pytest.mark.unit
def test_prompt_template_provider_compatibility(sample_template):
    """Test provider compatibility check."""
    assert sample_template.is_compatible_with_provider("gemini")
    assert sample_template.is_compatible_with_provider("OPENAI")
    assert sample_template.is_compatible_with_provider("Anthropic")


# ===== TemplateRegistry Tests =====

@pytest.fixture
def registry():
    """Get a fresh template registry."""
    # Create new registry instance (bypass singleton for testing)
    reg = TemplateRegistry.__new__(TemplateRegistry)
    reg._templates = {}
    reg._libraries = {}
    reg._custom_templates = {}
    reg._initialized = True
    reg._library_path = None  # Skip loading
    return reg


@pytest.mark.unit
def test_registry_singleton():
    """Test registry is a singleton."""
    reg1 = get_registry()
    reg2 = get_registry()
    assert reg1 is reg2


@pytest.mark.unit
def test_registry_register_custom_template(registry, sample_template):
    """Test registering a custom template."""
    template = registry.register_custom_template(
        name="Custom Test",
        agent_id="X",
        content="Custom content {var1}",
        variables=[{"name": "var1", "description": "Variable 1"}],
        category="custom"
    )
    assert template.template_id.startswith("custom-")
    assert template.name == "Custom Test"
    assert template.agent_id == "X"


@pytest.mark.unit
def test_registry_get_template(registry):
    """Test getting a template by ID."""
    registry.register_custom_template(
        name="Test Get",
        agent_id="Z",
        content="Test content",
        template_id="test-get-001"
    )

    retrieved = registry.get_template("test-get-001")
    assert retrieved is not None
    assert retrieved.template_id == "test-get-001"


@pytest.mark.unit
def test_registry_list_templates(registry):
    """Test listing templates with filters."""
    # Register multiple templates
    registry.register_custom_template(
        name="X Template",
        agent_id="X",
        content="X content",
        category="startup",
        tags=["innovation"]
    )
    registry.register_custom_template(
        name="Z Template",
        agent_id="Z",
        content="Z content",
        category="ethics",
        tags=["ethics"]
    )

    # List all
    all_templates = registry.list_templates()
    assert len(all_templates) == 2

    # Filter by agent
    x_templates = registry.list_templates(agent_id="X")
    assert len(x_templates) == 1
    assert x_templates[0].agent_id == "X"

    # Filter by category
    startup_templates = registry.list_templates(category="startup")
    assert len(startup_templates) == 1


@pytest.mark.unit
def test_registry_unregister_custom_template(registry):
    """Test unregistering a custom template."""
    registry.register_custom_template(
        name="To Remove",
        agent_id="CS",
        content="Will be removed",
        template_id="to-remove-001"
    )

    assert registry.get_template("to-remove-001") is not None
    result = registry.unregister_custom_template("to-remove-001")
    assert result is True
    assert registry.get_template("to-remove-001") is None


@pytest.mark.unit
def test_registry_statistics(registry):
    """Test registry statistics."""
    registry.register_custom_template(
        name="Stats Test",
        agent_id="X",
        content="Content"
    )

    stats = registry.get_statistics()
    assert "total_templates" in stats
    assert "builtin_templates" in stats
    assert "custom_templates" in stats
    assert stats["custom_templates"] == 1


# ===== Export Tests =====

@pytest.mark.unit
def test_export_markdown(sample_template):
    """Test exporting template to Markdown."""
    config = ExportConfig(format=ExportFormat.MARKDOWN)
    markdown = export_template_markdown(sample_template, config)

    assert "# Test Template" in markdown
    assert "test-template-001" in markdown
    assert "Variables" in markdown
    assert "concept_name" in markdown
    assert "VerifiMind-PEAS" in markdown


@pytest.mark.unit
def test_export_json(sample_template):
    """Test exporting template to JSON."""
    config = ExportConfig(format=ExportFormat.JSON)
    json_str = export_template_json(sample_template, config)

    # Should be valid JSON
    data = json.loads(json_str)
    assert data["template_id"] == "test-template-001"
    assert data["name"] == "Test Template"
    assert "variables" in data
    assert len(data["variables"]) == 2


@pytest.mark.unit
def test_export_json_includes_metadata(sample_template):
    """Test JSON export includes metadata."""
    config = ExportConfig(include_metadata=True)
    json_str = export_template_json(sample_template, config)
    data = json.loads(json_str)

    assert "metadata" in data
    assert data["metadata"]["author"] == "Test Author"
    assert "_export" in data
    assert data["_export"]["format"] == "verifimind-template-v1"


@pytest.mark.unit
def test_export_with_config_options(sample_template):
    """Test export with various config options."""
    # Without variables
    config = ExportConfig(include_variables=False)
    markdown = export_template_markdown(sample_template, config)
    assert "## Variables" not in markdown

    # Without compatibility
    config = ExportConfig(include_compatibility=False)
    markdown = export_template_markdown(sample_template, config)
    assert "## Provider Compatibility" not in markdown


@pytest.mark.unit
def test_export_function_dispatch(sample_template):
    """Test the unified export function."""
    # Markdown
    md = export_template(sample_template, ExportFormat.MARKDOWN)
    assert md.startswith("#")

    # JSON
    js = export_template(sample_template, ExportFormat.JSON)
    assert js.startswith("{")


# ===== GenesisPhase Tests =====

@pytest.mark.unit
def test_genesis_phase_enum():
    """Test GenesisPhase enum values."""
    assert GenesisPhase.PHASE_1.value == "genesis:phase-1"
    assert GenesisPhase.PHASE_2.value == "genesis:phase-2"
    assert GenesisPhase.PHASE_3.value == "genesis:phase-3"
    assert GenesisPhase.PHASE_4.value == "genesis:phase-4"
    assert GenesisPhase.PHASE_5.value == "genesis:phase-5"


# ===== TemplateLibraryEntry Tests =====

@pytest.mark.unit
def test_template_library_entry():
    """Test TemplateLibraryEntry creation."""
    entry = TemplateLibraryEntry(
        library_id="test_library",
        name="Test Library",
        description="A test library",
        templates=["template-1", "template-2"],
        agent_id="X",
        genesis_phase="genesis:phase-1",
        category="test"
    )

    assert entry.library_id == "test_library"
    assert len(entry.templates) == 2
    assert entry.genesis_phase == "genesis:phase-1"
