"""
Retry Logic with Exponential Backoff and Jitter

Provides robust retry mechanisms for API calls to handle transient errors,
rate limits, and service overloads gracefully.

Author: VerifiMind PEAS Team
Date: December 21, 2025
Version: 1.0.0
"""

import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

from verifimind_mcp.config.standard_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

T = TypeVar('T')


class APIError(Exception):
    """Custom exception for API errors that should trigger retries."""
    
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


async def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = None,
    retry_on_errors: list = None
) -> T:
    """
    Retry an async function with exponential backoff and jitter.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries (uses DEFAULT_CONFIG if None)
        retry_on_errors: List of error codes to retry on (uses DEFAULT_CONFIG if None)
        
    Returns:
        Result from successful function call
        
    Raises:
        APIError: If all retries are exhausted
    """
    if max_retries is None:
        max_retries = DEFAULT_CONFIG.retry.max_retries
    
    if retry_on_errors is None:
        retry_on_errors = DEFAULT_CONFIG.retry.retry_on_errors
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await func()
            
        except APIError as e:
            last_error = e
            
            # Check if this error should trigger a retry
            if e.status_code not in retry_on_errors:
                logger.error(f"❌ Non-retryable error {e.status_code}: {e.message}")
                raise
            
            # Don't retry on last attempt
            if attempt == max_retries - 1:
                break
            
            # Calculate delay with exponential backoff and jitter
            delay = DEFAULT_CONFIG.retry.calculate_delay(attempt)
            
            logger.warning(
                f"⚠️  API error {e.status_code} ({e.message}), "
                f"retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
            )
            
            await asyncio.sleep(delay)
            
        except Exception as e:
            # Non-API errors should not be retried
            logger.error(f"❌ Unexpected error: {e}")
            raise
    
    # All retries exhausted
    logger.error(f"❌ All {max_retries} retries exhausted")
    if last_error:
        raise last_error
    else:
        raise APIError(500, "All retries exhausted with unknown error")


def with_retry(func: Callable) -> Callable:
    """
    Decorator to add retry logic to an async function.
    
    Usage:
        @with_retry
        async def call_api():
            # API call here
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async def _call():
            return await func(*args, **kwargs)
        
        return await retry_with_backoff(_call)
    
    return wrapper
