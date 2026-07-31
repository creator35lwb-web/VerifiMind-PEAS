"""
Template Import from URL for VerifiMind-PEAS v0.4.0
====================================================

Internal template-import helpers. The public mutation tool is contained while
owner-scoped storage is built; this dormant path remains hardened for a future
authenticated reintroduction.

Supports:
- GitHub Gist URLs
- Raw GitHub content URLs (JSON/YAML)

Author: Alton Lee
Version: 0.4.0
"""

import json
import ipaddress
import logging
import re
import socket
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
    r'^https://gist\.github\.com/(?P<user>[^/]+)/(?P<gist_id>[a-fA-F0-9]+)(?:/)?(?:[?#].*)?$'
)
GITHUB_RAW_PATTERN = re.compile(
    r'^https://(?:raw\.githubusercontent\.com|gist\.githubusercontent\.com)/.+'
)

ALLOWED_TEMPLATE_HOSTS = frozenset({
    "gist.github.com",
    "gist.githubusercontent.com",
    "raw.githubusercontent.com",
})
MAX_TEMPLATE_DOWNLOAD_BYTES = 256 * 1024
TEMPLATE_FETCH_TIMEOUT_SECONDS = 15


def validate_template_url(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a template URL.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, source_type, error_message)
        source_type: 'gist' or 'github_raw'
    """
    try:
        if not isinstance(url, str) or not url.strip():
            return False, '', "URL must be a non-empty string"

        parsed = urlparse(url)

        # Fail closed to a narrow HTTPS allowlist. Arbitrary URL fetching is an
        # SSRF primitive even when the response is later parsed as JSON/YAML.
        if parsed.scheme.lower() != 'https':
            return False, '', "Template URL must use HTTPS"
        if parsed.username or parsed.password:
            return False, '', "Template URL must not contain user information"
        try:
            if parsed.port not in (None, 443):
                return False, '', "Template URL must use the default HTTPS port"
        except ValueError:
            return False, '', "Template URL contains an invalid port"

        hostname = (parsed.hostname or '').lower().rstrip('.')
        if hostname not in ALLOWED_TEMPLATE_HOSTS:
            return False, '', (
                "Template URL host is not allowed; use GitHub Gist or raw GitHub content"
            )

        # Check for GitHub Gist
        if hostname == 'gist.github.com' and GITHUB_GIST_PATTERN.match(url):
            return True, 'gist', None

        # Check for GitHub raw content
        if hostname in {
            'raw.githubusercontent.com', 'gist.githubusercontent.com'
        } and GITHUB_RAW_PATTERN.match(url):
            return True, 'github_raw', None

        return False, '', "URL is not a recognized GitHub Gist or raw-content URL"

    except Exception as e:
        return False, '', f"Invalid URL format: {str(e)}"


def _validate_resolved_target(url: str) -> Optional[str]:
    """Return an error if an allowed host resolves to a non-public address."""
    is_valid, _, error = validate_template_url(url)
    if not is_valid:
        return error

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname,
                443,
                type=socket.SOCK_STREAM,
            )
        }
    except OSError:
        return "Template host could not be resolved"

    if not addresses:
        return "Template host resolved to no addresses"

    for address in addresses:
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError:
            return "Template host resolved to an invalid address"
        if not parsed_address.is_global:
            return "Template host resolved to a non-public address"

    return None


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
        import ssl

        target_error = _validate_resolved_target(url)
        if target_error:
            return None, target_error

        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        connector = aiohttp.TCPConnector(ssl=ctx)
        timeout = aiohttp.ClientTimeout(total=TEMPLATE_FETCH_TIMEOUT_SECONDS)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            async with session.get(url, allow_redirects=False) as response:
                if 300 <= response.status < 400:
                    return None, "Template URL redirects are not allowed"
                if response.status != 200:
                    return None, f"HTTP {response.status}: {response.reason}"
                if (
                    response.content_length is not None
                    and response.content_length > MAX_TEMPLATE_DOWNLOAD_BYTES
                ):
                    return None, "Template response exceeds the download limit"

                chunks = []
                total = 0
                async for chunk in response.content.iter_chunked(8192):
                    total += len(chunk)
                    if total > MAX_TEMPLATE_DOWNLOAD_BYTES:
                        return None, "Template response exceeds the download limit"
                    chunks.append(chunk)

                try:
                    return b''.join(chunks).decode('utf-8'), None
                except UnicodeDecodeError:
                    return None, "Template response is not valid UTF-8"

    except ImportError:
        # Fallback to synchronous request if aiohttp not available
        try:
            return _fetch_url_content_sync(url)
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

        target_error = _validate_resolved_target(url)
        if target_error:
            return None, target_error

        # SSL context with explicit TLS 1.2+ minimum (SonarCloud python:S4423 satisfaction).
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2

        class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx),
            _NoRedirectHandler(),
        )
        with opener.open(
            url, timeout=TEMPLATE_FETCH_TIMEOUT_SECONDS
        ) as response:
            content_length = response.headers.get('Content-Length')
            if content_length:
                try:
                    if int(content_length) > MAX_TEMPLATE_DOWNLOAD_BYTES:
                        return None, "Template response exceeds the download limit"
                except ValueError:
                    return None, "Template response has an invalid Content-Length"

            raw = response.read(MAX_TEMPLATE_DOWNLOAD_BYTES + 1)
            if len(raw) > MAX_TEMPLATE_DOWNLOAD_BYTES:
                return None, "Template response exceeds the download limit"
            try:
                return raw.decode('utf-8'), None
            except UnicodeDecodeError:
                return None, "Template response is not valid UTF-8"

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
        pass  # Not JSON — fall through to try YAML

    # Try YAML if JSON failed
    if data is None:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            pass  # Not YAML either — will return error below

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
