#!/usr/bin/env python3
"""
Simple Gemini API Test

Tests if Gemini API key works and has quota available.
"""

import asyncio
import sys
from pathlib import Path

# Add mcp-server to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))

from verifimind_mcp.llm.provider import GeminiProvider


async def test_gemini():
    """Test Gemini API connection and quota."""
    print("🧪 Testing Gemini API...")
    print("=" * 60)
    
    try:
        # Initialize Gemini provider
        provider = GeminiProvider(model="gemini-2.0-flash-exp")
        print(f"✅ Gemini provider initialized")
        print(f"   Model: {provider.get_model_name()}")
        
        # Test simple generation
        print("\n📝 Testing simple generation...")
        response = await provider.generate(
            prompt="Say 'Hello from Gemini!' in JSON format with a 'message' field.",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ Generation successful!")
        print(f"   Content: {response.get('content', {})}")
        print(f"   Tokens: {response.get('usage', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gemini())
    sys.exit(0 if success else 1)
