"""
Input Sanitization Module for VerifiMind-PEAS

Security hardening to protect against:
- Prompt injection attacks
- SQL/NoSQL injection (future-proofing)
- XSS attacks
- Malformed input data

Author: Team YSenseAI
Version: 1.0.0
"""

import re
import html
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Maximum lengths for input fields
MAX_CONCEPT_NAME_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 10000
MAX_CATEGORY_LENGTH = 100
MAX_CONTEXT_LENGTH = 5000

# Patterns that might indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)",
    r"disregard\s+(previous|above|all)\s+(instructions?|prompts?)",
    r"disregard\s+all\s+previous\s+(prompts?|instructions?)",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"user\s*:\s*",
    r"\[INST\]",
    r"\[/INST\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"###\s*(Human|Assistant|System)",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
]

# Compiled patterns for efficiency
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS
]

# Characters that should be escaped or removed
DANGEROUS_CHARS = {
    '\x00': '',  # Null byte
    '\x0b': '',  # Vertical tab
    '\x0c': '',  # Form feed
    '\x1b': '',  # Escape character
}


class SanitizationError(Exception):
    """Raised when input fails sanitization checks."""
    pass


class SanitizationResult:
    """Result of sanitization operation."""
    
    def __init__(
        self,
        sanitized_value: str,
        was_modified: bool = False,
        warnings: Optional[List[str]] = None
    ):
        self.sanitized_value = sanitized_value
        self.was_modified = was_modified
        self.warnings = warnings or []
    
    def __str__(self) -> str:
        return self.sanitized_value


def remove_dangerous_chars(text: str) -> str:
    """Remove potentially dangerous control characters."""
    for char, replacement in DANGEROUS_CHARS.items():
        text = text.replace(char, replacement)
    return text


def detect_prompt_injection(text: str) -> List[str]:
    """
    Detect potential prompt injection patterns in text.
    
    Returns list of detected patterns (empty if none found).
    """
    detected = []
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
    return detected


def sanitize_html(text: str) -> str:
    """
    Escape HTML entities to prevent XSS.
    
    Converts: < > & " ' to HTML entities
    """
    return html.escape(text, quote=True)


def normalize_whitespace(text: str) -> str:
    """
    Normalize excessive whitespace while preserving structure.
    
    - Collapses multiple spaces to single space
    - Preserves single newlines
    - Collapses multiple newlines to double newline
    """
    # Collapse multiple spaces (not newlines) to single space
    text = re.sub(r'[^\S\n]+', ' ', text)
    # Collapse 3+ newlines to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def truncate_with_notice(text: str, max_length: int, field_name: str) -> tuple[str, bool]:
    """
    Truncate text if it exceeds max length.
    
    Returns (truncated_text, was_truncated)
    """
    if len(text) <= max_length:
        return text, False
    
    # Truncate and add notice
    truncated = text[:max_length - 50] + f"\n\n[Truncated: {field_name} exceeded {max_length} chars]"
    logger.warning(f"Input truncated: {field_name} was {len(text)} chars, max is {max_length}")
    return truncated, True


def sanitize_concept_name(name: str) -> SanitizationResult:
    """
    Sanitize concept name input.
    
    - Removes dangerous characters
    - Escapes HTML
    - Checks for prompt injection
    - Enforces length limit
    """
    warnings = []
    was_modified = False
    
    # Remove dangerous chars
    cleaned = remove_dangerous_chars(name)
    if cleaned != name:
        was_modified = True
        warnings.append("Removed control characters from name")
    
    # Normalize whitespace
    cleaned = normalize_whitespace(cleaned)
    
    # Check for prompt injection
    injections = detect_prompt_injection(cleaned)
    if injections:
        warnings.append(f"Potential prompt injection detected: {len(injections)} patterns")
        logger.warning(f"Prompt injection patterns in concept name: {injections}")
        # We log but don't block - the LLM should handle this with proper system prompts
    
    # Escape HTML
    cleaned = sanitize_html(cleaned)
    if cleaned != normalize_whitespace(remove_dangerous_chars(name)):
        was_modified = True
    
    # Truncate if needed
    cleaned, truncated = truncate_with_notice(cleaned, MAX_CONCEPT_NAME_LENGTH, "concept_name")
    if truncated:
        was_modified = True
        warnings.append(f"Name truncated to {MAX_CONCEPT_NAME_LENGTH} characters")
    
    return SanitizationResult(cleaned, was_modified, warnings)


def sanitize_description(description: str) -> SanitizationResult:
    """
    Sanitize concept description input.
    
    - Removes dangerous characters
    - Escapes HTML
    - Checks for prompt injection
    - Enforces length limit
    """
    warnings = []
    was_modified = False
    
    # Remove dangerous chars
    cleaned = remove_dangerous_chars(description)
    if cleaned != description:
        was_modified = True
        warnings.append("Removed control characters from description")
    
    # Normalize whitespace
    cleaned = normalize_whitespace(cleaned)
    
    # Check for prompt injection
    injections = detect_prompt_injection(cleaned)
    if injections:
        warnings.append(f"Potential prompt injection detected: {len(injections)} patterns")
        logger.warning(f"Prompt injection patterns in description: {injections}")
    
    # Escape HTML
    cleaned = sanitize_html(cleaned)
    if cleaned != normalize_whitespace(remove_dangerous_chars(description)):
        was_modified = True
    
    # Truncate if needed
    cleaned, truncated = truncate_with_notice(cleaned, MAX_DESCRIPTION_LENGTH, "description")
    if truncated:
        was_modified = True
        warnings.append(f"Description truncated to {MAX_DESCRIPTION_LENGTH} characters")
    
    return SanitizationResult(cleaned, was_modified, warnings)


def sanitize_category(category: str) -> SanitizationResult:
    """
    Sanitize category input.
    
    Categories should be simple text labels.
    """
    warnings = []
    was_modified = False
    
    # Remove dangerous chars
    cleaned = remove_dangerous_chars(category)
    
    # Normalize - categories should be single line
    cleaned = ' '.join(cleaned.split())
    
    # Escape HTML
    cleaned = sanitize_html(cleaned)
    
    if cleaned != category:
        was_modified = True
    
    # Truncate if needed
    cleaned, truncated = truncate_with_notice(cleaned, MAX_CATEGORY_LENGTH, "category")
    if truncated:
        was_modified = True
        warnings.append(f"Category truncated to {MAX_CATEGORY_LENGTH} characters")
    
    return SanitizationResult(cleaned, was_modified, warnings)


def sanitize_context(context: str) -> SanitizationResult:
    """
    Sanitize context input.
    
    Context provides additional information about the concept.
    """
    warnings = []
    was_modified = False
    
    # Remove dangerous chars
    cleaned = remove_dangerous_chars(context)
    if cleaned != context:
        was_modified = True
        warnings.append("Removed control characters from context")
    
    # Normalize whitespace
    cleaned = normalize_whitespace(cleaned)
    
    # Check for prompt injection
    injections = detect_prompt_injection(cleaned)
    if injections:
        warnings.append(f"Potential prompt injection detected: {len(injections)} patterns")
        logger.warning(f"Prompt injection patterns in context: {injections}")
    
    # Escape HTML
    cleaned = sanitize_html(cleaned)
    if cleaned != normalize_whitespace(remove_dangerous_chars(context)):
        was_modified = True
    
    # Truncate if needed
    cleaned, truncated = truncate_with_notice(cleaned, MAX_CONTEXT_LENGTH, "context")
    if truncated:
        was_modified = True
        warnings.append(f"Context truncated to {MAX_CONTEXT_LENGTH} characters")
    
    return SanitizationResult(cleaned, was_modified, warnings)


def sanitize_concept_input(
    name: str,
    description: str,
    category: Optional[str] = None,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sanitize all concept input fields.
    
    Returns dict with sanitized values and metadata.
    
    Example:
        result = sanitize_concept_input(
            name="My AI Concept",
            description="A detailed description...",
            category="Healthcare",
            context="Additional context..."
        )
        
        # Access sanitized values
        clean_name = result['name']
        clean_desc = result['description']
        
        # Check if any modifications were made
        if result['was_modified']:
            print(f"Warnings: {result['warnings']}")
    """
    all_warnings = []
    was_modified = False
    
    # Sanitize name
    name_result = sanitize_concept_name(name)
    all_warnings.extend([f"name: {w}" for w in name_result.warnings])
    was_modified = was_modified or name_result.was_modified
    
    # Sanitize description
    desc_result = sanitize_description(description)
    all_warnings.extend([f"description: {w}" for w in desc_result.warnings])
    was_modified = was_modified or desc_result.was_modified
    
    # Sanitize category if provided
    clean_category = None
    if category:
        cat_result = sanitize_category(category)
        clean_category = cat_result.sanitized_value
        all_warnings.extend([f"category: {w}" for w in cat_result.warnings])
        was_modified = was_modified or cat_result.was_modified
    
    # Sanitize context if provided
    clean_context = None
    if context:
        ctx_result = sanitize_context(context)
        clean_context = ctx_result.sanitized_value
        all_warnings.extend([f"context: {w}" for w in ctx_result.warnings])
        was_modified = was_modified or ctx_result.was_modified
    
    return {
        'name': name_result.sanitized_value,
        'description': desc_result.sanitized_value,
        'category': clean_category,
        'context': clean_context,
        'was_modified': was_modified,
        'warnings': all_warnings
    }


# Convenience function for quick validation
def is_safe_input(text: str) -> bool:
    """
    Quick check if input appears safe.
    
    Returns True if no obvious issues detected.
    """
    if not text or not text.strip():
        return False
    
    # Check for prompt injection
    if detect_prompt_injection(text):
        return False
    
    # Check for null bytes or other dangerous chars
    for char in DANGEROUS_CHARS:
        if char in text:
            return False
    
    return True
