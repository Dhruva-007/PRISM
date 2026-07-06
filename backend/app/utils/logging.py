"""
Structured logging configuration for PRISM.

In development: human-readable colored output.
In production (Cloud Run): JSON structured output compatible with Cloud Logging.

All application modules should use:
    from app.utils.logging import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys
from app.config import get_settings


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured Logger instance.
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    if settings.is_production:
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger