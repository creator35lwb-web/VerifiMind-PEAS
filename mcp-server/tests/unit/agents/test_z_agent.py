"""Unit tests for Z Agent (Ethics Guardian) - Corrected for actual code structure."""

import pytest
from unittest.mock import patch
from verifimind_mcp.agents.z_agent import ZAgent
from verifimind_mcp.models import Concept, ZAgentAnalysis, ReasoningStep
from verifimind_mcp.llm import MockProvider


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    return MockProvider()


@pytest.fixture
def z_agent(mock_provider):
    """Create Z Agent with mock provider."""
    return ZAgent(llm_provider=mock_provider)


@pytest.fixture
def sample_concept():
    """Create a sample concept for testing."""
    return Concept(
        name="AI-Powered Mental Health Chatbot",
        description="A chatbot that provides mental health support and crisis intervention",
        category="Healthcare AI",
        context="Target: People experiencing mental health challenges. Platform: Mobile app."
    )


@pytest.fixture
def harmful_concept():
    """Create a concept that should trigger veto."""
    return Concept(
        name="AI Symptom Checker for Self-Diagnosis",
        description="An app that diagnoses medical conditions based on symptoms without doctor involvement",
        category="Healthcare AI",
        context="Replaces professional medical diagnosis with AI-only assessment."
    )


@pytest.mark.unit
def test_z_agent_initialization(z_agent):
    """Test Z Agent initializes correctly."""
    assert z_agent is not None
    assert z_agent.AGENT_ID == "Z"
    assert z_agent.OUTPUT_MODEL == ZAgentAnalysis


@pytest.mark.unit
def test_z_agent_has_ethical_red_lines(z_agent):
    """Test Z Agent defines ethical red lines."""
    red_lines = z_agent.get_ethical_red_lines()
    
    assert isinstance(red_lines, list)
    assert len(red_lines) == 6  # Deception, Privacy, Discrimination, Harm, Autonomy, Exploitation
    
    # Verify all red lines have required fields
    for red_line in red_lines:
        assert "red_line" in red_line
        assert "description" in red_line
        assert "severity" in red_line


@pytest.mark.unit
def test_z_agent_has_z_protocol_principles(z_agent):
    """Test Z Agent defines Z-Protocol principles."""
    principles = z_agent.get_z_protocol_principles()
    
    assert isinstance(principles, list)
    assert len(principles) == 6  # Transparency, Consent, Fairness, Privacy, Accountability, Beneficence
    
    # Verify all principles have required fields
    for principle in principles:
        assert "principle" in principle
        assert "description" in principle


@pytest.mark.unit
def test_z_agent_focus_summary(z_agent):
    """Test Z Agent provides focus summary."""
    summary = z_agent.get_focus_summary()
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "ethical" in summary.lower()
    assert "veto" in summary.lower()


@pytest.mark.unit
def test_z_agent_ethical_red_lines_include_critical_issues(z_agent):
    """Test ethical red lines include critical issues."""
    red_lines = z_agent.get_ethical_red_lines()
    red_line_names = [rl["red_line"] for rl in red_lines]
    
    critical_issues = ["Deception", "Privacy Violation", "Discrimination", "Harm Facilitation"]
    
    for issue in critical_issues:
        assert issue in red_line_names, f"Missing critical red line: {issue}"


@pytest.mark.unit
def test_z_agent_z_protocol_includes_core_principles(z_agent):
    """Test Z-Protocol includes core AI ethics principles."""
    principles = z_agent.get_z_protocol_principles()
    principle_names = [p["principle"] for p in principles]
    
    core_principles = ["Transparency", "Consent", "Fairness", "Privacy", "Accountability"]
    
    for principle in core_principles:
        assert principle in principle_names, f"Missing core principle: {principle}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_z_agent_check_veto_status(z_agent, sample_concept):
    """Test Z Agent veto status check method."""
    # Mock the analyze method to return a valid result
    mock_analysis = ZAgentAnalysis(
        agent="Z Guardian",
        reasoning_steps=[
            ReasoningStep(
                step_number=1,
                thought="Checking ethical implications",
                confidence=0.82
            )
        ],
        ethics_score=7.5,
        z_protocol_compliance=True,
        veto_triggered=False,
        ethical_concerns=["Privacy considerations"],
        mitigation_measures=["Clear privacy policy"],
        recommendation="Proceed with mitigations",
        confidence=0.82
    )
    
    with patch.object(z_agent, 'analyze', return_value=mock_analysis):
        result = await z_agent.check_veto_status(sample_concept)
        
        assert isinstance(result, dict)
        assert result["agent"] == "Z Guardian"
        assert result["concept"] == sample_concept.name
        assert "veto_triggered" in result
        assert "z_protocol_compliance" in result
        assert "ethics_score" in result


@pytest.mark.unit
def test_z_agent_config_loaded(z_agent):
    """Test Z Agent has proper configuration loaded."""
    assert z_agent.config is not None
    assert z_agent.config.name == "Z Guardian"
    assert z_agent.config.role == "Ethics and Z-Protocol Guardian"


@pytest.mark.unit
def test_z_agent_llm_provider_set(z_agent):
    """Test Z Agent has LLM provider set."""
    assert z_agent.llm is not None
    assert isinstance(z_agent.llm, MockProvider)


@pytest.mark.unit
def test_z_agent_critical_red_lines_marked_as_critical(z_agent):
    """Test critical red lines have 'critical' severity."""
    red_lines = z_agent.get_ethical_red_lines()
    
    critical_red_lines = [
        rl for rl in red_lines 
        if rl["red_line"] in ["Deception", "Privacy Violation", "Discrimination", "Harm Facilitation"]
    ]
    
    for red_line in critical_red_lines:
        assert red_line["severity"] == "critical", f"{red_line['red_line']} should be marked as critical"
