"""Unit tests for CS Agent (Security) - Corrected for actual code structure."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from verifimind_mcp.agents.cs_agent import CSAgent
from verifimind_mcp.models import Concept, CSAgentAnalysis, ReasoningStep
from verifimind_mcp.llm import MockProvider


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    return MockProvider()


@pytest.fixture
def cs_agent(mock_provider):
    """Create CS Agent with mock provider."""
    return CSAgent(llm_provider=mock_provider)


@pytest.fixture
def sample_concept():
    """Create a sample concept for testing."""
    return Concept(
        name="Blockchain-Based Smart Contract Platform",
        description="A platform for deploying and executing smart contracts with automated security analysis",
        category="Blockchain",
        context="Target: DeFi developers. Platform: Ethereum-compatible."
    )


@pytest.mark.unit
def test_cs_agent_initialization(cs_agent):
    """Test CS Agent initializes correctly."""
    assert cs_agent is not None
    assert cs_agent.AGENT_ID == "CS"
    assert cs_agent.OUTPUT_MODEL == CSAgentAnalysis


@pytest.mark.unit
def test_cs_agent_has_security_categories(cs_agent):
    """Test CS Agent defines security categories."""
    categories = cs_agent.get_security_categories()
    
    assert isinstance(categories, list)
    assert len(categories) == 7  # Authentication, Authorization, Data Protection, Input Validation, Error Handling, Logging, Third-Party
    
    # Verify all categories have required fields
    for category in categories:
        assert "category" in category
        assert "description" in category
        assert "weight" in category
        assert isinstance(category["weight"], float)


@pytest.mark.unit
def test_cs_agent_has_socratic_question_types(cs_agent):
    """Test CS Agent defines Socratic question types."""
    question_types = cs_agent.get_socratic_question_types()
    
    assert isinstance(question_types, list)
    assert len(question_types) == 6  # Clarification, Assumption Probing, Evidence Seeking, Perspective, Consequence, Meta
    
    # Verify all question types have required fields
    for qt in question_types:
        assert "type" in qt
        assert "purpose" in qt
        assert "example" in qt


@pytest.mark.unit
def test_cs_agent_focus_summary(cs_agent):
    """Test CS Agent provides focus summary."""
    summary = cs_agent.get_focus_summary()
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "security" in summary.lower()
    assert "socratic" in summary.lower()


@pytest.mark.unit
def test_cs_agent_security_categories_weights_sum_to_one(cs_agent):
    """Test security category weights sum to approximately 1.0."""
    categories = cs_agent.get_security_categories()
    total_weight = sum(c["weight"] for c in categories)
    
    # Allow small floating point error
    assert abs(total_weight - 1.0) < 0.01


@pytest.mark.unit
def test_cs_agent_security_categories_include_critical_areas(cs_agent):
    """Test security categories include critical security areas."""
    categories = cs_agent.get_security_categories()
    category_names = [c["category"] for c in categories]
    
    critical_areas = ["Authentication", "Authorization", "Data Protection", "Input Validation"]
    
    for area in critical_areas:
        assert area in category_names, f"Missing critical security area: {area}"


@pytest.mark.unit
def test_cs_agent_socratic_questions_include_key_types(cs_agent):
    """Test Socratic questions include key questioning types."""
    question_types = cs_agent.get_socratic_question_types()
    type_names = [qt["type"] for qt in question_types]
    
    key_types = ["Clarification", "Assumption Probing", "Evidence Seeking", "Consequence Analysis"]
    
    for qt_type in key_types:
        assert qt_type in type_names, f"Missing question type: {qt_type}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cs_agent_security_scan(cs_agent, sample_concept):
    """Test CS Agent security scan method."""
    # Mock the analyze method to return a valid result
    mock_analysis = CSAgentAnalysis(
        agent="CS Security",
        reasoning_steps=[
            ReasoningStep(
                step_number=1,
                thought="Analyzing security vulnerabilities",
                confidence=0.78
            )
        ],
        security_score=7.5,
        vulnerabilities=["Reentrancy attacks", "Integer overflow"],
        attack_vectors=["Malicious contract calls"],
        socratic_questions=["What happens if gas runs out?"],
        security_recommendations=["Implement reentrancy guards"],
        recommendation="Implement security recommendations",
        confidence=0.78
    )
    
    with patch.object(cs_agent, 'analyze', return_value=mock_analysis):
        result = await cs_agent.security_scan(sample_concept)
        
        assert isinstance(result, dict)
        assert result["agent"] == "CS Security"
        assert result["concept"] == sample_concept.name
        assert "security_score" in result
        assert "vulnerability_count" in result
        assert "attack_vector_count" in result


@pytest.mark.unit
def test_cs_agent_config_loaded(cs_agent):
    """Test CS Agent has proper configuration loaded."""
    assert cs_agent.config is not None
    assert cs_agent.config.name == "CS Security"
    assert cs_agent.config.role == "Security Analyst and Concept Scrutinizer"


@pytest.mark.unit
def test_cs_agent_llm_provider_set(cs_agent):
    """Test CS Agent has LLM provider set."""
    assert cs_agent.llm is not None
    assert isinstance(cs_agent.llm, MockProvider)
