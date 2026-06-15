"""
Structured Logging — Rich-formatted console logging.

Usage:
    from src.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Processing document", filename="test.pdf", pages=10)
"""

import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

from src.core.config import get_settings

_console = Console(stderr=True)


def get_logger(name: str) -> logging.Logger:
    """
    Get a structured logger with Rich formatting.

    Args:
        name: Logger name, typically __name__.

    Returns:
        Configured logger instance.
    """
    settings = get_settings()

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    
    handler = RichHandler(
        console=_console,
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def setup_root_logger() -> None:
    """Configure the root logger for the application."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(message)s",
        handlers=[
            RichHandler(
                console=_console,
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            )
        ],
    )

    # Suppress noisy third-party loggers
    for noisy_logger in ["httpx", "httpcore", "chromadb", "urllib3"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
