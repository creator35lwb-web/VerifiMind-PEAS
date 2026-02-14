"""
Template Import from URL for VerifiMind-PEAS v0.4.0
====================================================

Import templates from URLs (GitHub Gists, raw files, etc.)
for community template sharing.

Supports:
- GitHub Gist URLs
- Raw file URLs (JSON/YAML)
- Standard HTTP/HTTPS URLs

Author: Alton Lee
Version: 0.4.0
"""

import json
import logging
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import yaml

from .models import (
    PromptTemplate,
    TemplateVariable,
    ImportResult,
)

logger = logging.getLogger(__name__)

# URL patterns for different sources
GITHUB_GIST_PATTERN = re.compile(
    r'https?://gist\.github\.com/(?P<user>[^/]+)/(?P<gist_id>[a-f0-9]+)'
)
GITHUB_RAW_PATTERN = re.compile(
    r'https?://raw\.githubusercontent\.com/.*'
)


def validate_template_url(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a template URL.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, source_type, error_message)
        source_type: 'gist', 'github_raw', 'raw_url'
    """
    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ('http', 'https'):
            return False, '', f"Invalid URL scheme: {parsed.scheme}. Must be http or https."

        # Check for GitHub Gist
        if GITHUB_GIST_PATTERN.match(url):
            return True, 'gist', None

        # Check for GitHub raw content
        if GITHUB_RAW_PATTERN.match(url):
            return True, 'github_raw', None

        # Check for common file extensions
        path_lower = parsed.path.lower()
        if path_lower.endswith(('.json', '.yaml', '.yml')):
            return True, 'raw_url', None

        # Accept any HTTPS URL but warn
        if parsed.scheme == 'https':
            return True, 'raw_url', None

        return False, '', "URL must be HTTPS or a recognized template source (GitHub Gist, raw file)"

    except Exception as e:
        return False, '', f"Invalid URL format: {str(e)}"


def _convert_gist_to_raw_url(url: str) -> str:
    """Convert a GitHub Gist URL to raw content URL."""
    match = GITHUB_GIST_PATTERN.match(url)
    if match:
        gist_id = match.group('gist_id')
        # Gist raw URL format: https://gist.githubusercontent.com/{user}/{gist_id}/raw
        user = match.group('user')
        return f"https://gist.githubusercontent.com/{user}/{gist_id}/raw"
    return url


async def _fetch_url_content(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch content from a URL.

    Args:
        url: URL to fetch

    Returns:
        Tuple of (content, error_message)
    """
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None, f"HTTP {response.status}: {response.reason}"
                content = await response.text()
                return content, None

    except ImportError:
        # Fallback to synchronous request if aiohttp not available
        try:
            import urllib.request
            import ssl

            # Create SSL context that doesn't verify (for development)
            ctx = ssl.create_default_context()

            with urllib.request.urlopen(url, timeout=30, context=ctx) as response:
                content = response.read().decode('utf-8')
                return content, None

        except Exception as e:
            return None, f"Failed to fetch URL: {str(e)}"

    except Exception as e:
        return None, f"Failed to fetch URL: {str(e)}"


def _fetch_url_content_sync(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Synchronous version of URL fetch for non-async contexts.

    Args:
        url: URL to fetch

    Returns:
        Tuple of (content, error_message)
    """
    try:
        import urllib.request
        import ssl

        ctx = ssl.create_default_context()

        with urllib.request.urlopen(url, timeout=30, context=ctx) as response:
            content = response.read().decode('utf-8')
            return content, None

    except Exception as e:
        return None, f"Failed to fetch URL: {str(e)}"


def _parse_template_content(
    content: str,
    source_url: str
) -> Tuple[Optional[PromptTemplate], list, Optional[str]]:
    """
    Parse template content from JSON or YAML.

    Args:
        content: Raw content string
        source_url: Source URL for error messages

    Returns:
        Tuple of (template, warnings, error)
    """
    warnings = []
    data = None

    # Try JSON first
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try YAML if JSON failed
    if data is None:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            pass

    if data is None:
        return None, warnings, "Content is not valid JSON or YAML"

    # Validate required fields
    required_fields = ['template_id', 'name', 'content']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return None, warnings, f"Missing required fields: {missing}"

    # Parse variables
    variables = []
    for var_data in data.get('variables', []):
        try:
            var = TemplateVariable(
                name=var_data.get('name'),
                description=var_data.get('description', ''),
                type_hint=var_data.get('type_hint', 'str'),
                required=var_data.get('required', True),
                default=var_data.get('default'),
                examples=var_data.get('examples'),
                validation_pattern=var_data.get('validation_pattern')
            )
            variables.append(var)
        except Exception as e:
            warnings.append(f"Skipped invalid variable: {e}")

    # Extract compatibility info
    compatibility = data.get('compatibility', {})

    # Build template
    try:
        template = PromptTemplate(
            template_id=data['template_id'],
            name=data['name'],
            agent_id=data.get('agent_id', 'all'),
            content=data['content'],
            variables=variables,
            version=data.get('version', '1.0.0'),
            category=data.get('category', 'imported'),
            tags=data.get('tags', ['imported']),
            changelog=data.get('changelog', [f"Imported from {source_url}"]),
            description=data.get('description'),
            author=data.get('author') or data.get('metadata', {}).get('author'),
            compatible_providers=compatibility.get('providers', [
                "gemini", "openai", "anthropic", "groq", "mistral", "ollama", "mock"
            ]),
            min_context_length=compatibility.get('min_context_length', 4096),
            recommended_temperature=compatibility.get('recommended_temperature', 0.7),
            recommended_max_tokens=compatibility.get('recommended_max_tokens', 4096)
        )

        # Add import tag if not present
        if 'imported' not in template.tags:
            template.tags.append('imported')

        return template, warnings, None

    except Exception as e:
        return None, warnings, f"Failed to create template: {str(e)}"


def _validate_template(template: PromptTemplate) -> list:
    """
    Validate an imported template for safety and correctness.

    Args:
        template: Template to validate

    Returns:
        List of validation warnings
    """
    warnings = []

    # Check template content length
    if len(template.content) > 50000:
        warnings.append("Template content is very long (>50k chars)")

    # Check for potentially dangerous patterns
    dangerous_patterns = [
        ('system:', "Template contains 'system:' which may override system prompts"),
        ('ignore previous', "Template contains 'ignore previous' pattern"),
        ('disregard', "Template contains 'disregard' pattern"),
    ]

    content_lower = template.content.lower()
    for pattern, warning in dangerous_patterns:
        if pattern in content_lower:
            warnings.append(warning)

    # Check variable count
    if len(template.variables) > 20:
        warnings.append(f"Template has many variables ({len(template.variables)})")

    # Check for unmatched placeholders
    import re
    placeholders = re.findall(r'\{(\w+)\}', template.content)
    var_names = {v.name for v in template.variables}
    undefined = set(placeholders) - var_names - {'prior_reasoning', 'concept_name', 'concept_description', 'context'}
    if undefined:
        warnings.append(f"Undefined placeholders in template: {undefined}")

    return warnings


async def import_template_from_url(
    url: str,
    validate: bool = True
) -> ImportResult:
    """
    Import a template from a URL.

    Args:
        url: URL to import from (GitHub Gist, raw file, etc.)
        validate: Whether to validate the template after import

    Returns:
        ImportResult with template and status
    """
    # Validate URL
    is_valid, source_type, error = validate_template_url(url)
    if not is_valid:
        return ImportResult(
            success=False,
            source_url=url,
            error=error
        )

    # Convert Gist URLs to raw URLs
    fetch_url = url
    if source_type == 'gist':
        fetch_url = _convert_gist_to_raw_url(url)

    # Fetch content
    content, fetch_error = await _fetch_url_content(fetch_url)
    if fetch_error:
        return ImportResult(
            success=False,
            source_url=url,
            error=fetch_error
        )

    # Parse content
    template, parse_warnings, parse_error = _parse_template_content(content, url)
    if parse_error:
        return ImportResult(
            success=False,
            source_url=url,
            error=parse_error,
            warnings=parse_warnings
        )

    # Validate template
    all_warnings = parse_warnings
    if validate:
        validation_warnings = _validate_template(template)
        all_warnings.extend(validation_warnings)

    return ImportResult(
        success=True,
        template=template,
        source_url=url,
        warnings=all_warnings
    )


def import_template_from_url_sync(
    url: str,
    validate: bool = True
) -> ImportResult:
    """
    Synchronous version of import_template_from_url.

    Args:
        url: URL to import from
        validate: Whether to validate the template

    Returns:
        ImportResult with template and status
    """
    # Validate URL
    is_valid, source_type, error = validate_template_url(url)
    if not is_valid:
        return ImportResult(
            success=False,
            source_url=url,
            error=error
        )

    # Convert Gist URLs to raw URLs
    fetch_url = url
    if source_type == 'gist':
        fetch_url = _convert_gist_to_raw_url(url)

    # Fetch content
    content, fetch_error = _fetch_url_content_sync(fetch_url)
    if fetch_error:
        return ImportResult(
            success=False,
            source_url=url,
            error=fetch_error
        )

    # Parse content
    template, parse_warnings, parse_error = _parse_template_content(content, url)
    if parse_error:
        return ImportResult(
            success=False,
            source_url=url,
            error=parse_error,
            warnings=parse_warnings
        )

    # Validate template
    all_warnings = parse_warnings
    if validate:
        validation_warnings = _validate_template(template)
        all_warnings.extend(validation_warnings)

    return ImportResult(
        success=True,
        template=template,
        source_url=url,
        warnings=all_warnings
    )
