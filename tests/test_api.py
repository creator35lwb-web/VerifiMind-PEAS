"""
Quick API Test Script
Test your OpenAI/Anthropic API keys with VerifiMind
"""

import asyncio
import os
from src.llm.llm_provider import LLMProviderFactory, LLMMessage


def print_banner():
    print("\n" + "="*70)
    print("  VerifiMind™ API Connection Test")
    print("="*70 + "\n")


async def test_openai():
    """Test OpenAI API"""
    print("[TEST 1] Testing OpenAI (GPT-4)...")
    print("-" * 70)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("   To set: set OPENAI_API_KEY=sk-your-key-here")
        print("   Or use: setx OPENAI_API_KEY \"sk-your-key-here\"")
        return False

    print("✓ API Key found (redacted)")

    try:
        # Create provider
        provider = LLMProviderFactory.create_provider(
            provider_type="openai",
            model="gpt-4"
        )
        print("✓ Provider created: OpenAI GPT-4")

        # Test API call
        print("✓ Sending test message to GPT-4...")
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Respond with exactly: 'OpenAI API is working!'")
        ]

        response = await provider.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )

        print(f"✓ Response received!")
        print(f"\nGPT-4 says: {response.content}")
        print(f"\nTokens used: {response.usage['total_tokens']}")
        print(f"Model: {response.model}")

        print("\n✅ OpenAI API is working correctly!\n")
        return True

    except ImportError:
        print("❌ OpenAI library not installed")
        print("   To install: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        print("\nPossible issues:")
        print("  - Invalid API key")
        print("  - Insufficient credits")
        print("  - Network connection issue")
        print("  - Check: https://platform.openai.com/account/api-keys")
        return False


async def test_anthropic():
    """Test Anthropic API"""
    print("\n[TEST 2] Testing Anthropic (Claude 3)...")
    print("-" * 70)

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   To set: set ANTHROPIC_API_KEY=sk-ant-your-key-here")
        print("   Or use: setx ANTHROPIC_API_KEY \"sk-ant-your-key-here\"")
        return False

    print("✓ API Key found (redacted)")

    try:
        # Create provider
        provider = LLMProviderFactory.create_provider(
            provider_type="anthropic",
            model="claude-3-opus-20240229"
        )
        print("✓ Provider created: Anthropic Claude 3 Opus")

        # Test API call
        print("✓ Sending test message to Claude...")
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Respond with exactly: 'Anthropic API is working!'")
        ]

        response = await provider.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )

        print(f"✓ Response received!")
        print(f"\nClaude says: {response.content}")
        print(f"\nTokens used: {response.usage['total_tokens']}")
        print(f"Model: {response.model}")

        print("\n✅ Anthropic API is working correctly!\n")
        return True

    except ImportError:
        print("❌ Anthropic library not installed")
        print("   To install: pip install anthropic")
        return False
    except Exception as e:
        print(f"❌ Anthropic API error: {e}")
        print("\nPossible issues:")
        print("  - Invalid API key")
        print("  - Insufficient credits")
        print("  - Network connection issue")
        print("  - Check: https://console.anthropic.com/")
        return False


async def test_ollama():
    """Test Ollama (local)"""
    print("\n[TEST 3] Testing Ollama (Local Model)...")
    print("-" * 70)

    try:
        # Create provider
        provider = LLMProviderFactory.create_provider(
            provider_type="local",
            model="llama2"
        )
        print("✓ Provider created: Ollama Llama2")

        # Test API call
        print("✓ Sending test message to Llama2...")
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Say hello!")
        ]

        response = await provider.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )

        print(f"✓ Response received!")
        print(f"\nLlama2 says: {response.content}")

        print("\n✅ Ollama is working correctly!\n")
        return True

    except Exception as e:
        print(f"❌ Ollama error: {e}")
        print("\nPossible issues:")
        print("  - Ollama not installed (get from: https://ollama.ai)")
        print("  - Ollama server not running (run: ollama serve)")
        print("  - Model not pulled (run: ollama pull llama2)")
        return False


async def test_with_verifimind():
    """Test with actual VerifiMind agent"""
    print("\n[TEST 4] Testing with VerifiMind Agent...")
    print("-" * 70)

    # Check which API is available
    has_openai = os.getenv('OPENAI_API_KEY') is not None
    has_anthropic = os.getenv('ANTHROPIC_API_KEY') is not None

    if not has_openai and not has_anthropic:
        print("❌ No API keys configured")
        print("   Using intelligent mock instead")
        provider_type = "openai"  # Will fall back to mock
    elif has_openai:
        provider_type = "openai"
        print("✓ Using OpenAI GPT-4")
    else:
        provider_type = "anthropic"
        print("✓ Using Anthropic Claude")

    try:
        from src.agents.x_intelligent_agent import XIntelligentAgent
        from src.agents.base_agent import ConceptInput

        # Create LLM provider
        llm = LLMProviderFactory.create_provider(provider_type, model="gpt-4" if provider_type == "openai" else "claude-3-opus-20240229")

        # Create agent
        config = {"log_level": "INFO"}
        x_agent = XIntelligentAgent("X-TEST", llm, config)

        # Test concept
        concept = ConceptInput(
            id="test-001",
            description="A simple todo list app for personal task management",
            category="Productivity",
            user_context={"target_users": "Individuals"},
            session_id="test-session"
        )

        print("✓ Running X Agent analysis...")
        result = await x_agent.analyze(concept)

        print(f"✓ Analysis complete!")
        print(f"\n  Status: {result.status}")
        print(f"  Risk Score: {result.risk_score}/100")
        print(f"  Recommendations: {len(result.recommendations)}")

        if result.recommendations:
            print(f"\n  First recommendation:")
            print(f"    {result.recommendations[0]}")

        print("\n✅ VerifiMind agent is working with real API!\n")
        return True

    except Exception as e:
        print(f"❌ Agent test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print_banner()

    # Check API configuration
    print("API Configuration Status:")
    print("-" * 70)
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    print(f"  OpenAI:    {'✓ Configured' if openai_key else '✗ Not set'}")
    print(f"  Anthropic: {'✓ Configured' if anthropic_key else '✗ Not set'}")
    print()

    if not openai_key and not anthropic_key:
        print("⚠️  WARNING: No API keys configured!")
        print("   VerifiMind will use intelligent mock responses.")
        print("   To use real AI, set API keys (see SETUP_API_KEYS.md)")
        print()
        choice = input("Continue with mock testing? (y/n): ").lower()
        if choice != 'y':
            print("\nSetup instructions:")
            print("  1. Get API key from OpenAI or Anthropic")
            print("  2. Set environment variable:")
            print("     set OPENAI_API_KEY=sk-your-key")
            print("  3. Restart this script")
            print("\nSee SETUP_API_KEYS.md for detailed instructions.")
            return

    # Run tests
    results = []

    if openai_key:
        result = await test_openai()
        results.append(("OpenAI", result))

    if anthropic_key:
        result = await test_anthropic()
        results.append(("Anthropic", result))

    # Always test Ollama (optional)
    print("\n" + "="*70)
    choice = input("\nTest Ollama (local model)? (y/n): ").lower()
    if choice == 'y':
        result = await test_ollama()
        results.append(("Ollama", result))

    # Test with VerifiMind agent
    if openai_key or anthropic_key:
        result = await test_with_verifimind()
        results.append(("VerifiMind Agent", result))

    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name:20} {status}")

    if all(r for _, r in results):
        print("\n🎉 All tests passed! Your APIs are configured correctly.")
        print("   You can now use VerifiMind with real AI analysis!")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        print("   VerifiMind will still work with intelligent mocks.")

    print("\n" + "="*70)
    print("Next steps:")
    print("  1. Double-click VerifiMind.bat")
    print("  2. Press [2] to test enhanced agents with real API")
    print("  3. Press [1] to generate apps with AI analysis")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user.")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
