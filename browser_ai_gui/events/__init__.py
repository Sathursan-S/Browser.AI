"""
Browser.AI Structured Event System

A decoupled, SOLID-compliant event emission system for Browser.AI that provides
structured events for tasks, states, progress, LLM output, and more.

This module separates concerns between:
- Event emission (creating and publishing events)
- Event transport (how events are delivered)
- Event consumers (who receives events)
"""

from .emitter import EventEmitter, IEventEmitter, create_event_id, create_timestamp
from .schemas import (
    AgentActionEvent,
    AgentCompleteEvent,
    AgentErrorEvent,
    AgentProgressEvent,
    AgentStartEvent,
    AgentStateEvent,
    AgentStepEvent,
    BaseEvent,
    EventCategory,
    EventSeverity,
    LLMOutputEvent,
    TaskStateChangeEvent,
)
from .transport import EventTransport, IEventTransport, MultiTransport

__all__ = [
    # Interfaces
    "IEventEmitter",
    "IEventTransport",
    # Implementations
    "EventEmitter",
    "EventTransport",
    "MultiTransport",
    # Schemas
    "BaseEvent",
    "EventCategory",
    "EventSeverity",
    "AgentStartEvent",
    "AgentStepEvent",
    "AgentActionEvent",
    "AgentProgressEvent",
    "AgentStateEvent",
    "AgentCompleteEvent",
    "AgentErrorEvent",
    "LLMOutputEvent",
    "TaskStateChangeEvent",
    # Utilities
    "create_event_id",
    "create_timestamp",
]
