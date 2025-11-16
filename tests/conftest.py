"""
Pytest configuration and shared fixtures for VerifiMind PEAS tests.

This file is automatically loaded by pytest and provides:
- Shared test fixtures
- Test configuration
- Reusable test utilities
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# Placeholder for future fixtures
# Example fixtures will be added as needed:
# - Mock LLM providers
# - Test data generators
# - Database fixtures
# - etc.
