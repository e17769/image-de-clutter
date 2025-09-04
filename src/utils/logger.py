"""
Logging configuration and utilities for Photo Archivist.

Provides centralized logging setup with file rotation and formatting.
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_level=logging.INFO):
    """
    Set up application logging with file rotation.

    Args:
        log_level: Logging level (default: INFO)
    """
    # Create logs directory
    log_dir = Path.home() / ".photo_archivist" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file path
    log_file = log_dir / "photo_archivist.log"

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler with rotation (max 10MB, keep 5 files)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Photo Archivist logging initialized")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info("=" * 50)


def get_logger(name):
    """
    Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_exception(logger, message="An exception occurred"):
    """
    Log an exception with full traceback.

    Args:
        logger: Logger instance
        message: Custom message to include
    """
    logger.error(message, exc_info=True)


def log_performance(logger, operation_name, start_time, end_time, **kwargs):
    """
    Log performance metrics for an operation.

    Args:
        logger: Logger instance
        operation_name: Name of the operation
        start_time: Start timestamp
        end_time: End timestamp
        **kwargs: Additional metrics to log
    """
    duration = end_time - start_time
    metrics = f"Operation: {operation_name}, Duration: {duration:.2f}s"

    for key, value in kwargs.items():
        metrics += f", {key}: {value}"

    logger.info(f"PERFORMANCE: {metrics}")


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def logger(self):
        """Get logger instance for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger
