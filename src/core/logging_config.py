"""
VerifiMind Logging Configuration

Centralized logging setup for the entire application.
Configurable via LOG_LEVEL environment variable.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = None, log_file: str = None) -> None:
    """
    Configure the root logger for VerifiMind.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, reads from LOG_LEVEL environment variable (default: INFO)
        log_file: Path to log file. If None, uses 'logs/verifimind.log'
    """
    # Determine log level from parameter or environment variable
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    else:
        log_level = log_level.upper()

    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        print(f"Warning: Invalid log level '{log_level}', defaulting to INFO")

    # Determine log file path
    if log_file is None:
        log_file = 'logs/verifimind.log'

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Define log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create file handler with rotation (max 10MB, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log the initialization
    root_logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
