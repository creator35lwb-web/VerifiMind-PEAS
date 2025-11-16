"""
Test script for VerifiMind Iterative Code Generation System
Validates all components work correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("="*70)
    print("TEST 1: Module Imports")
    print("="*70)

    try:
        # Test agent imports
        print("  Testing agent imports...")
        from src.agents import (
            ReflectionAgent,
            ReflectionReport,
            CodeIssue,
            XIntelligentAgent,
            ZGuardianAgent,
            CSSecurityAgent,
            AgentOrchestrator
        )
        print("  ✅ All agent modules imported successfully")

        # Test generation imports
        print("  Testing generation imports...")
        from src.generation import (
            IterativeCodeGenerationEngine,
            VersionTracker,
            VersionMetadata,
            ImprovementHistory,
            CodeGenerationEngine,
            AppSpecification,
            GeneratedApp
        )
        print("  ✅ All generation modules imported successfully")

        # Test LLM import
        print("  Testing LLM import...")
        from src.llm.llm_provider import LLMProvider
        print("  ✅ LLM provider imported successfully")

        print("\n✅ All imports successful!\n")
        return True

    except ImportError as e:
        print(f"\n❌ Import failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_reflection_agent():
    """Test ReflectionAgent initialization"""
    print("="*70)
    print("TEST 2: ReflectionAgent Initialization")
    print("="*70)

    try:
        from src.agents import ReflectionAgent
        from src.llm.llm_provider import LLMProvider

        llm = LLMProvider({})
        agent = ReflectionAgent(
            agent_id="test-reflection",
            llm_provider=llm,
            config={'quality_threshold': 85, 'max_iterations': 3}
        )

        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Agent Type: {agent.agent_type}")
        print(f"  Quality Threshold: {agent.quality_threshold}")
        print(f"  Max Iterations: {agent.max_iterations}")

        print("\n✅ ReflectionAgent initialized successfully!\n")
        return True

    except Exception as e:
        print(f"\n❌ ReflectionAgent test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_version_tracker():
    """Test VersionTracker"""
    print("="*70)
    print("TEST 3: VersionTracker")
    print("="*70)

    try:
        from src.generation import VersionTracker

        tracker = VersionTracker()

        # Start tracking
        history = tracker.start_tracking(
            app_id="test-app-001",
            app_name="TestApp",
            initial_concept="A test application"
        )

        print(f"  Tracking started for: {history.app_name}")
        print(f"  App ID: {history.app_id}")
        print(f"  Iterations: {history.total_iterations}")

        # Complete tracking
        tracker.complete_tracking("test-app-001")

        if history.completed_at:
            print(f"  ✅ Tracking completed at: {history.completed_at}")

        print("\n✅ VersionTracker working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ VersionTracker test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_iterative_generator():
    """Test IterativeCodeGenerationEngine initialization"""
    print("="*70)
    print("TEST 4: IterativeCodeGenerationEngine")
    print("="*70)

    try:
        from src.generation import IterativeCodeGenerationEngine
        from src.llm.llm_provider import LLMProvider

        llm = LLMProvider({})
        generator = IterativeCodeGenerationEngine(
            config={},
            llm_provider=llm,
            max_iterations=3,
            quality_threshold=85
        )

        print(f"  Max Iterations: {generator.max_iterations}")
        print(f"  Quality Threshold: {generator.quality_threshold}")
        print(f"  Code Generator: {type(generator.code_generator).__name__}")
        print(f"  Reflection Agent: {type(generator.reflection_agent).__name__}")
        print(f"  Version Tracker: {type(generator.version_tracker).__name__}")

        print("\n✅ IterativeCodeGenerationEngine initialized successfully!\n")
        return True

    except Exception as e:
        print(f"\n❌ IterativeCodeGenerationEngine test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_code_issue():
    """Test CodeIssue dataclass"""
    print("="*70)
    print("TEST 5: CodeIssue Dataclass")
    print("="*70)

    try:
        from src.agents import CodeIssue

        issue = CodeIssue(
            severity='high',
            category='security',
            file_path='src/server.js',
            line_number=42,
            description='SQL injection vulnerability',
            suggestion='Use parameterized queries',
            code_snippet='query("SELECT * FROM users WHERE id = " + userId)'
        )

        print(f"  Severity: {issue.severity}")
        print(f"  Category: {issue.category}")
        print(f"  File: {issue.file_path}:{issue.line_number}")
        print(f"  Description: {issue.description}")
        print(f"  Suggestion: {issue.suggestion}")

        print("\n✅ CodeIssue working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ CodeIssue test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_reflection_report():
    """Test ReflectionReport dataclass"""
    print("="*70)
    print("TEST 6: ReflectionReport Dataclass")
    print("="*70)

    try:
        from src.agents import ReflectionReport, CodeIssue
        from datetime import datetime

        # Create sample issues
        security_issue = CodeIssue(
            severity='critical',
            category='security',
            file_path='auth.js',
            line_number=10,
            description='Password not hashed',
            suggestion='Use bcrypt',
            code_snippet=None
        )

        report = ReflectionReport(
            iteration=1,
            version='v1.0',
            quality_score=75.0,
            security_score=50.0,
            compliance_score=80.0,
            performance_score=70.0,
            overall_score=68.75,
            security_issues=[security_issue],
            quality_issues=[],
            compliance_gaps=[],
            performance_issues=[],
            best_practice_violations=[],
            improvement_suggestions=['Add password hashing', 'Implement rate limiting'],
            applied_improvements=[],
            timestamp=datetime.utcnow(),
            analysis_duration=2.5,
            should_iterate=True
        )

        print(f"  Version: {report.version}")
        print(f"  Overall Score: {report.overall_score}/100")
        print(f"  Total Issues: {len(report.all_issues())}")
        print(f"  Critical Issues: {len(report.critical_issues())}")
        print(f"  Should Iterate: {report.should_iterate}")

        # Test to_dict
        report_dict = report.to_dict()
        print(f"  Serialized Keys: {list(report_dict.keys())}")

        print("\n✅ ReflectionReport working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ ReflectionReport test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("VERIFIMIND ITERATIVE SYSTEM - TEST SUITE")
    print("="*70 + "\n")

    tests = [
        ("Module Imports", test_imports),
        ("ReflectionAgent", test_reflection_agent),
        ("VersionTracker", test_version_tracker),
        ("IterativeGenerator", test_iterative_generator),
        ("CodeIssue", test_code_issue),
        ("ReflectionReport", test_reflection_report),
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.\n")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.\n")
        return False


if __name__ == "__main__":
    print("\n[TEST] Running VerifiMind Iterative System Tests...\n")
    success = run_all_tests()
    sys.exit(0 if success else 1)
