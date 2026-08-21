"""
Logging configuration for the Crime Analysis project.

This module provides a reusable logger configuration function that sets up
structured logging with file and console handlers.

TODO:
    - Add log rotation support.
    - Add JSON-formatted logging for production.
    - Add remote log aggregation (e.g., ELK, Datadog).
    - Add correlation ID injection for request tracing.
"""

from typing import Dict, Any
import logging
import logging.config


def get_logging_config(log_level: str = "INFO", log_file: str = "logs/app.log") -> Dict[str, Any]:
    """
    Return a logging configuration dictionary.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to the log file.

    Returns:
        Dict[str, Any]: Logging configuration compatible with logging.config.dictConfig.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
            "detailed": {
                "format": (
                    "%(asctime)s [%(levelname)s] %(name)s "
                    "(%(filename)s:%(lineno)d): %(message)s"
                ),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": log_file,
                "mode": "a",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
    }


def setup_logging(log_level: str = "INFO", log_file: str = "logs/app.log") -> None:
    """
    Configure logging for the application.

    Args:
        log_level: The logging level to use.
        log_file: Path to the log file.
    """
    config: Dict[str, Any] = get_logging_config(log_level, log_file)
    logging.config.dictConfig(config)