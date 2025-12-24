"""
VerifiMind-PEAS Integrations Module
===================================

This module contains external integrations that enhance the X-Z-CS Trinity
with additional validation capabilities.

Available Integrations:
- godelai: C-S-P (Compression → State → Propagation) validation framework

Each integration is contributed by external projects and properly attributed.
"""

from . import godelai

__all__ = ["godelai"]
