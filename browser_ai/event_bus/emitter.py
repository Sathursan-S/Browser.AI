"""
Browser.AI Event Emitter - Convenience Functions for Event Streaming

This module provides easy-to-use functions for emitting events from anywhere
in the codebase, supporting both synchronous and asynchronous contexts.

Features:
- Type-safe event emission with Pydantic validation
- Automatic topic detection from event type
- Support for different subscription levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Async iterator support for real-time streaming
- Thread-safe singleton EventManager access

Usage:
    from browser_ai.event_bus.emitter import emit, emit_async, subscribe

    # Emit an event synchronously
    emit(AgentStartedEvent(task="my task"))

    # Emit an event asynchronously
    await emit_async(AgentStartedEvent(task="my task"))

    # Subscribe to events
    subscribe("agent", my_handler)

    # Subscribe to all events
    subscribe("*", my_handler)
"""

import asyncio
import logging
from enum import Enum
from typing import AsyncIterator, Callable, Optional, Union

from browser_ai.event_bus.core import EventHandler, EventManager
from browser_ai.event_bus.events import BaseEvent

logger = logging.getLogger(__name__)


class EventLevel(str, Enum):
    """
    Event subscription levels for filtering events.

    Subscribers can filter events by importance level:
    - DEBUG: All events including detailed debugging info
    - INFO: Standard operational events
    - WARNING: Events indicating potential issues
    - ERROR: Error events and failures
    - CRITICAL: Critical system events only
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Singleton instance
_event_manager: Optional[EventManager] = None


def get_event_manager() -> EventManager:
    """
    Get the singleton EventManager instance.

    Returns:
        EventManager: The global event manager instance
    """
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager


def emit(event: BaseEvent) -> None:
    """
    Emit an event synchronously.

    The event will be published to all subscribers of its topic.
    Async handlers will be scheduled as fire-and-forget tasks.

    Args:
        event: The event to emit (must be a BaseEvent subclass)

    Example:
        from browser_ai.event_bus import emit, AgentStartedEvent

        emit(AgentStartedEvent(task="Search for Python tutorials"))
    """
    manager = get_event_manager()
    manager.publish(event.topic, event)


async def emit_async(event: BaseEvent) -> None:
    """
    Emit an event asynchronously.

    The event will be published to all subscribers of its topic.
    All handlers (sync and async) will be awaited.

    Args:
        event: The event to emit (must be a BaseEvent subclass)

    Example:
        from browser_ai.event_bus import emit_async, AgentStartedEvent

        await emit_async(AgentStartedEvent(task="Search for Python tutorials"))
    """
    manager = get_event_manager()
    await manager.publish_async(event.topic, event)


def subscribe(
    topic: str,
    handler: Union[EventHandler, Callable[[BaseEvent], None]],
) -> EventHandler:
    """
    Subscribe a handler to a topic.

    Args:
        topic: The topic to subscribe to (e.g., "agent", "browser", "llm")
               Use "*" to subscribe to all topics
        handler: Either an EventHandler instance or a callable that takes a BaseEvent

    Returns:
        EventHandler: The registered handler (useful for later unsubscription)

    Example:
        from browser_ai.event_bus import subscribe, BaseEvent

        def my_handler(event: BaseEvent):
            print(f"Received: {event.name}")

        subscribe("agent", my_handler)
        subscribe("*", my_handler)  # Subscribe to all events
    """
    manager = get_event_manager()

    # Wrap callable in an EventHandler if needed
    if not isinstance(handler, EventHandler):
        if asyncio.iscoroutinefunction(handler):
            handler = _AsyncCallableHandler(handler)
        else:
            handler = _CallableHandler(handler)

    manager.subscribe(topic, handler)
    return handler


def unsubscribe(topic: str, handler: EventHandler) -> None:
    """
    Unsubscribe a handler from a topic.

    Args:
        topic: The topic to unsubscribe from
        handler: The handler to remove

    Example:
        handler = subscribe("agent", my_handler)
        # Later...
        unsubscribe("agent", handler)
    """
    manager = get_event_manager()
    manager.unsubscribe(topic, handler)


class _CallableHandler(EventHandler):
    """Internal wrapper to convert a sync callable into an EventHandler."""

    def __init__(self, callback: Callable[[BaseEvent], None]):
        self._callback = callback

    @property
    def name(self) -> str:
        return getattr(self._callback, "__name__", "anonymous_handler")

    def handle(self, event: BaseEvent) -> None:
        """Synchronous handle."""
        self._callback(event)


class _AsyncCallableHandler(EventHandler):
    """Internal wrapper to convert an async callable into an EventHandler."""

    def __init__(self, callback: Callable[[BaseEvent], None]):
        self._callback = callback

    @property
    def name(self) -> str:
        return getattr(self._callback, "__name__", "async_handler")

    async def handle(self, event: BaseEvent) -> None:
        """Asynchronous handle."""
        await self._callback(event)


class AsyncEventHandler(EventHandler):
    """
    Async event handler that wraps an async callback.

    This is useful when you want to create an async handler from a coroutine function.
    """

    def __init__(self, callback: Callable[[BaseEvent], None]):
        self._callback = callback

    @property
    def name(self) -> str:
        return getattr(self._callback, "__name__", "async_handler")

    async def handle(self, event: BaseEvent) -> None:
        await self._callback(event)


class StreamingEventHandler(EventHandler):
    """
    A handler that collects events for streaming via async iteration.

    This handler is designed for real-time event streaming to WebSocket
    clients or Server-Sent Events (SSE) endpoints.

    Usage:
        handler = StreamingEventHandler()
        subscribe("*", handler)

        async for event in handler.stream():
            await websocket.send(event.model_dump_json())
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize the streaming handler.

        Args:
            max_queue_size: Maximum number of events to buffer
        """
        self._queue: asyncio.Queue[BaseEvent] = asyncio.Queue(maxsize=max_queue_size)
        self._closed = False

    @property
    def name(self) -> str:
        return "StreamingEventHandler"

    def handle(self, event: BaseEvent) -> None:
        """Queue the event for streaming (non-blocking)."""
        if self._closed:
            return
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop oldest event and add new one
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(event)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    async def stream(self, timeout: Optional[float] = None) -> AsyncIterator[BaseEvent]:
        """
        Async iterator that yields events as they arrive.

        Args:
            timeout: Optional timeout for waiting on new events (seconds)

        Yields:
            BaseEvent: Events as they are received

        Example:
            async for event in handler.stream():
                print(event.model_dump_json())
        """
        while not self._closed:
            try:
                if timeout:
                    event = await asyncio.wait_for(self._queue.get(), timeout=timeout)
                else:
                    event = await self._queue.get()
                yield event
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def close(self) -> None:
        """Close the streaming handler."""
        self._closed = True

    def is_closed(self) -> bool:
        """Check if the handler is closed."""
        return self._closed


class FilteredEventHandler(EventHandler):
    """
    An event handler that filters events based on level or custom predicates.

    This allows subscribers to receive only events matching certain criteria.

    Usage:
        # Filter by event level
        handler = FilteredEventHandler(
            inner_handler,
            level_filter=EventLevel.WARNING
        )

        # Filter with custom predicate
        handler = FilteredEventHandler(
            inner_handler,
            predicate=lambda e: e.topic == "agent"
        )
    """

    def __init__(
        self,
        inner_handler: EventHandler,
        level_filter: Optional[EventLevel] = None,
        predicate: Optional[Callable[[BaseEvent], bool]] = None,
    ):
        """
        Initialize the filtered handler.

        Args:
            inner_handler: The handler to delegate to if filter passes
            level_filter: Only pass events at or above this level
            predicate: Custom filter function returning True to pass event
        """
        self._inner = inner_handler
        self._level_filter = level_filter
        self._predicate = predicate

    @property
    def name(self) -> str:
        return f"FilteredEventHandler({self._inner.name})"

    def handle(self, event: BaseEvent) -> None:
        """Handle the event if it passes the filter."""
        if self._should_pass(event):
            self._inner.handle(event)

    def _should_pass(self, event: BaseEvent) -> bool:
        """Check if the event should pass through the filter."""
        # Check level filter
        if self._level_filter:
            event_level = self._get_event_level(event)
            if not self._level_meets_threshold(event_level, self._level_filter):
                return False

        # Check custom predicate
        if self._predicate and not self._predicate(event):
            return False

        return True

    def _get_event_level(self, event: BaseEvent) -> EventLevel:
        """Determine the level of an event based on its type."""
        name_lower = event.name.lower()

        if "error" in name_lower or "failed" in name_lower:
            return EventLevel.ERROR
        elif "warning" in name_lower or "limit" in name_lower:
            return EventLevel.WARNING
        elif "debug" in name_lower:
            return EventLevel.DEBUG
        else:
            return EventLevel.INFO

    def _level_meets_threshold(
        self, event_level: EventLevel, threshold: EventLevel
    ) -> bool:
        """Check if event level meets the threshold."""
        level_order = {
            EventLevel.DEBUG: 0,
            EventLevel.INFO: 1,
            EventLevel.WARNING: 2,
            EventLevel.ERROR: 3,
            EventLevel.CRITICAL: 4,
        }
        return level_order.get(event_level, 1) >= level_order.get(threshold, 0)
