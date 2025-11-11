"""
Logging configuration for AgenticCTI.
Provides centralized logging setup with file and console handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "./logs",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_format: Optional[str] = None
) -> None:
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name (generates default if None)
        log_dir: Directory for log files
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        log_format: Custom log format string
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Default log file
    if log_file is None:
        log_file = "agentic_cti.log"

    log_filepath = log_path / log_file

    # Default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_filepath,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Log startup message
    logging.info(f"Logging configured - Level: {log_level}, File: {log_filepath}")

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("stix2").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def mask_sensitive_data(data: str, mask_char: str = "*", show_chars: int = 4) -> str:
    """
    Mask sensitive data for logging.

    Args:
        data: Data to mask
        mask_char: Character to use for masking
        show_chars: Number of characters to show at end

    Returns:
        Masked string
    """
    if not data or len(data) <= show_chars:
        return mask_char * 8

    visible = data[-show_chars:]
    masked = mask_char * (len(data) - show_chars)
    return masked + visible
