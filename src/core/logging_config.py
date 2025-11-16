"""
Centralized Logging Configuration for VerifiMind PEAS

Provides consistent logging across all modules with:
- Console output (INFO and above)
- File output (DEBUG and above) to logs/verifimind.log
- Configurable log levels via LOG_LEVEL environment variable
- Structured log format with timestamps
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = None, log_file: str = None) -> None:
    """
    Configure the logging system for VerifiMind PEAS.

    Args:
        log_level: Override the LOG_LEVEL environment variable (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Override the default log file path

    Environment Variables:
        LOG_LEVEL: Set logging level (default: INFO)
        LOG_FILE: Set custom log file path (default: logs/verifimind.log)
    """

    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    else:
        log_level = log_level.upper()

    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        print(f"Warning: Invalid log level '{log_level}', defaulting to INFO")
        numeric_level = logging.INFO
        log_level = 'INFO'

    # Determine log file path
    if log_file is None:
        log_file = os.getenv('LOG_FILE', 'logs/verifimind.log')

    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = logging.Formatter(
        fmt='[%(levelname)s] %(message)s'
    )

    # Get root logger and clear existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, let handlers filter

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console Handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler - DEBUG and above with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        # Log the initialization
        root_logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")

    except Exception as e:
        # If file logging fails, continue with console only
        root_logger.warning(f"Failed to initialize file logging: {e}. Continuing with console only.")

    # Suppress verbose third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Starting process")
        logger.debug("Debug information")
        logger.error("An error occurred", exc_info=True)
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for temporary log level changes.

    Example:
        with LogContext(logging.DEBUG):
            # Detailed logging here
            logger.debug("This will be logged")
        # Back to normal level
    """

    def __init__(self, level: int):
        self.level = level
        self.old_level = None

    def __enter__(self):
        self.old_level = logging.root.level
        logging.root.setLevel(self.level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.root.setLevel(self.old_level)
        return False


# Convenience function for development
def enable_debug_logging():
    """Enable DEBUG level logging for all loggers"""
    logging.root.setLevel(logging.DEBUG)
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)


def disable_file_logging():
    """Disable file logging (keep console only)"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)):
            root_logger.removeHandler(handler)


if __name__ == "__main__":
    # Test the logging configuration
    setup_logging()

    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    print("\nLogging test complete. Check logs/verifimind.log for file output.")
