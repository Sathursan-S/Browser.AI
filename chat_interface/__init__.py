"""
Chat Interface for Browser AI Library

This module provides chat-based interfaces (web and desktop) for the Browser AI library,
allowing users to interact with browser automation through a conversational interface.
"""

__version__ = "0.1.0"

from .event_listener import LogEventListener
from .config_manager import ConfigManager

__all__ = ['LogEventListener', 'ConfigManager']