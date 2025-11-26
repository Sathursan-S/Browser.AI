"""
Browser.AI Event Bus Logging Handler

This module provides a logging handler that emits log records as events
through the event bus, enabling real-time log streaming to UI components.

Usage:
    from browser_ai.event_bus.handlers.logging_handler import LoggingEventHandler
    from browser_ai.event_bus import subscribe

    # Enable log event emission
    handler = LoggingEventHandler.enable()

    # Subscribe to log events
    subscribe("log", my_handler)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from browser_ai.event_bus.events import BaseEvent


class LogEvent(BaseEvent):
    """
    Event emitted for each log record.

    Attributes:
        topic: Always "log" for log events
        name: Log level name (e.g., "log_info", "log_error")
        level: Numeric log level
        level_name: String log level name
        logger_name: Name of the logger
        message: Formatted log message
        module: Module where the log was emitted
        function: Function where the log was emitted
        line_number: Line number where the log was emitted
        exception_info: Exception information if present
        metadata: Additional metadata
    """

    topic: str = "log"
    name: str = "log_record"
    level: int
    level_name: str
    logger_name: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    exception_info: Optional[str] = None
    metadata: Dict[str, Any] = {}


class LoggingEventHandler(logging.Handler):
    """
    A logging handler that emits log records as events through the event bus.

    This allows UI components and other subscribers to receive real-time
    log updates through the event streaming system.

    Usage:
        # Enable globally for browser_ai logger
        handler = LoggingEventHandler.enable()

        # Or attach to specific logger
        handler = LoggingEventHandler()
        logging.getLogger("my_logger").addHandler(handler)
    """

    _instance: Optional["LoggingEventHandler"] = None

    def __init__(self, level: int = logging.DEBUG):
        """
        Initialize the logging event handler.

        Args:
            level: Minimum log level to emit as events
        """
        super().__init__(level)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record as an event.

        Args:
            record: The log record to emit
        """
        try:
            # Import here to avoid circular imports
            from browser_ai.event_bus.emitter import emit

            # Format exception info if present
            exception_info = None
            if record.exc_info:
                exception_info = self.formatter.formatException(record.exc_info) if self.formatter else str(record.exc_info)

            # Create log event
            event = LogEvent(
                name=f"log_{record.levelname.lower()}",
                level=record.levelno,
                level_name=record.levelname,
                logger_name=record.name,
                message=self.format(record),
                module=record.module,
                function=record.funcName,
                line_number=record.lineno,
                exception_info=exception_info,
                metadata={
                    "pathname": record.pathname,
                    "process": record.process,
                    "thread": record.thread,
                },
            )

            # Emit the event
            emit(event)

        except Exception:
            # Don't let event emission errors break logging
            self.handleError(record)

    @classmethod
    def enable(
        cls,
        logger_name: str = "browser_ai",
        level: int = logging.DEBUG,
    ) -> "LoggingEventHandler":
        """
        Enable log event emission for a logger.

        Args:
            logger_name: Name of the logger to attach to
            level: Minimum log level to emit

        Returns:
            LoggingEventHandler: The handler instance
        """
        if cls._instance is not None:
            return cls._instance

        handler = cls(level=level)
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        cls._instance = handler
        return handler

    @classmethod
    def disable(cls, logger_name: str = "browser_ai") -> None:
        """
        Disable log event emission.

        Args:
            logger_name: Name of the logger to detach from
        """
        if cls._instance is None:
            return

        logger = logging.getLogger(logger_name)
        logger.removeHandler(cls._instance)
        cls._instance = None
