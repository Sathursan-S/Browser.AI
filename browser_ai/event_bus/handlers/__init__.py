"""
Browser.AI Event Bus Handlers

Pre-built event handlers for common use cases.
"""

from browser_ai.event_bus.handlers.console import ConsoleHandler
from browser_ai.event_bus.handlers.logging_handler import LogEvent, LoggingEventHandler

__all__ = [
    "ConsoleHandler",
    "LoggingEventHandler",
    "LogEvent",
]
