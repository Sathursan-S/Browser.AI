#!/usr/bin/env python3
"""
Tests for the Browser.AI Event Bus / Event Streaming System

This test suite validates:
- Event emission (sync and async)
- Event subscription and filtering
- Streaming event handlers
- Logging integration
- Type safety with Pydantic models
"""

import asyncio
import logging
import pytest
from typing import List
from unittest.mock import MagicMock, AsyncMock

# Import event bus components
from browser_ai.event_bus import (
    emit,
    emit_async,
    subscribe,
    unsubscribe,
    get_event_manager,
    EventLevel,
    EventManager,
    EventHandler,
    BaseEvent,
    StreamingEventHandler,
    FilteredEventHandler,
    # Event types
    AgentStartedEvent,
    AgentCompletedEvent,
    AgentStepStartedEvent,
    AgentStepCompletedEvent,
    AgentFailedEvent,
    LLMRequestStartedEvent,
    LLMRequestCompletedEvent,
    ErrorOccurredEvent,
)
from browser_ai.event_bus.handlers import LoggingEventHandler, LogEvent


class TestEventEmission:
    """Tests for basic event emission functionality."""

    def test_emit_sync(self):
        """Test synchronous event emission."""
        received_events: List[BaseEvent] = []

        def handler(event: BaseEvent):
            received_events.append(event)

        # Subscribe and emit
        h = subscribe("agent", handler)
        emit(AgentStartedEvent(task="test task", use_vision=True))

        assert len(received_events) == 1
        assert isinstance(received_events[0], AgentStartedEvent)
        assert received_events[0].task == "test task"
        assert received_events[0].use_vision is True

        # Cleanup
        unsubscribe("agent", h)

    @pytest.mark.asyncio
    async def test_emit_async(self):
        """Test asynchronous event emission."""
        received_events: List[BaseEvent] = []

        async def async_handler(event: BaseEvent):
            received_events.append(event)

        # Subscribe and emit
        h = subscribe("agent", async_handler)
        await emit_async(AgentCompletedEvent(
            task="test task",
            total_steps=5,
            success=True,
            final_result="Task completed"
        ))

        assert len(received_events) == 1
        assert isinstance(received_events[0], AgentCompletedEvent)
        assert received_events[0].success is True
        assert received_events[0].total_steps == 5

        # Cleanup
        unsubscribe("agent", h)

    def test_emit_to_multiple_subscribers(self):
        """Test event emission to multiple subscribers."""
        received_by_1: List[BaseEvent] = []
        received_by_2: List[BaseEvent] = []

        def handler1(event: BaseEvent):
            received_by_1.append(event)

        def handler2(event: BaseEvent):
            received_by_2.append(event)

        h1 = subscribe("agent", handler1)
        h2 = subscribe("agent", handler2)

        emit(AgentStartedEvent(task="test"))

        assert len(received_by_1) == 1
        assert len(received_by_2) == 1

        # Cleanup
        unsubscribe("agent", h1)
        unsubscribe("agent", h2)

    def test_wildcard_subscription(self):
        """Test subscribing to all events with wildcard."""
        received_events: List[BaseEvent] = []

        def handler(event: BaseEvent):
            received_events.append(event)

        h = subscribe("*", handler)

        # Emit events to different topics
        emit(AgentStartedEvent(task="test"))
        emit(LLMRequestStartedEvent(purpose="action", model_name="gpt-4"))
        emit(ErrorOccurredEvent(
            error_type="test",
            error_message="test error",
            component="test"
        ))

        assert len(received_events) == 3

        # Cleanup
        unsubscribe("*", h)


class TestEventManager:
    """Tests for the EventManager singleton."""

    def test_singleton_pattern(self):
        """Test that EventManager follows singleton pattern."""
        manager1 = get_event_manager()
        manager2 = get_event_manager()
        assert manager1 is manager2

    def test_subscribe_and_unsubscribe(self):
        """Test subscription and unsubscription."""
        manager = get_event_manager()
        received: List[BaseEvent] = []

        def handler(event: BaseEvent):
            received.append(event)

        h = subscribe("test_topic", handler)
        emit(AgentStartedEvent(task="test"))  # Different topic, shouldn't receive

        assert len(received) == 0

        unsubscribe("test_topic", h)


class TestStreamingEventHandler:
    """Tests for the StreamingEventHandler."""

    @pytest.mark.asyncio
    async def test_streaming_handler(self):
        """Test streaming handler collects and yields events."""
        handler = StreamingEventHandler(max_queue_size=10)
        subscribe("agent", handler)

        # Emit some events
        emit(AgentStartedEvent(task="task1"))
        emit(AgentStepStartedEvent(step_number=1))
        emit(AgentStepCompletedEvent(step_number=1, actions_taken=[]))

        # Collect events with timeout
        collected = []
        async def collect():
            async for event in handler.stream(timeout=0.1):
                collected.append(event)
                if len(collected) >= 3:
                    break

        await asyncio.wait_for(collect(), timeout=1.0)

        assert len(collected) == 3
        assert isinstance(collected[0], AgentStartedEvent)
        assert isinstance(collected[1], AgentStepStartedEvent)
        assert isinstance(collected[2], AgentStepCompletedEvent)

        handler.close()
        unsubscribe("agent", handler)

    @pytest.mark.asyncio
    async def test_streaming_handler_overflow(self):
        """Test streaming handler handles overflow gracefully."""
        handler = StreamingEventHandler(max_queue_size=2)
        subscribe("agent", handler)

        # Emit more events than queue can hold
        for i in range(5):
            emit(AgentStepStartedEvent(step_number=i))

        # Should only have the most recent events
        # (queue drops oldest when full)
        handler.close()
        unsubscribe("agent", handler)


class TestFilteredEventHandler:
    """Tests for the FilteredEventHandler."""

    def test_level_filter(self):
        """Test filtering by event level."""
        received: List[BaseEvent] = []

        class InnerHandler(EventHandler):
            def handle(self, event: BaseEvent):
                received.append(event)

        inner = InnerHandler()
        filtered = FilteredEventHandler(
            inner,
            level_filter=EventLevel.ERROR
        )

        subscribe("agent", filtered)
        subscribe("error", filtered)

        # Info-level event (should be filtered)
        emit(AgentStartedEvent(task="test"))

        # Error-level event (should pass)
        emit(ErrorOccurredEvent(
            error_type="test",
            error_message="test error",
            component="agent"
        ))

        # Only error event should have passed
        assert len(received) == 1
        assert isinstance(received[0], ErrorOccurredEvent)

        unsubscribe("agent", filtered)
        unsubscribe("error", filtered)

    def test_predicate_filter(self):
        """Test filtering with custom predicate."""
        received: List[BaseEvent] = []

        class InnerHandler(EventHandler):
            def handle(self, event: BaseEvent):
                received.append(event)

        inner = InnerHandler()
        filtered = FilteredEventHandler(
            inner,
            predicate=lambda e: getattr(e, 'task', '') == 'important'
        )

        subscribe("agent", filtered)

        emit(AgentStartedEvent(task="unimportant"))
        emit(AgentStartedEvent(task="important"))

        assert len(received) == 1
        assert received[0].task == "important"

        unsubscribe("agent", filtered)


class TestEventTypeSafety:
    """Tests for Pydantic type safety."""

    def test_event_validation(self):
        """Test that events validate their fields."""
        # Valid event
        event = AgentStartedEvent(task="test task")
        assert event.task == "test task"
        assert event.topic == "agent"
        assert event.name == "agent_started"

    def test_event_serialization(self):
        """Test event serialization to JSON."""
        event = AgentCompletedEvent(
            task="test",
            total_steps=10,
            success=True,
            final_result="Done"
        )

        json_str = event.model_dump_json()
        assert "test" in json_str
        assert "true" in json_str.lower()

    def test_event_deserialization(self):
        """Test event deserialization from dict."""
        data = {
            "task": "my task",
            "agent_id": "abc123",
            "use_vision": False
        }
        event = AgentStartedEvent(**data)
        assert event.task == "my task"
        assert event.agent_id == "abc123"
        assert event.use_vision is False


class TestLoggingEventHandler:
    """Tests for the LoggingEventHandler."""

    def test_log_event_emission(self):
        """Test that log records are emitted as events."""
        received_events: List[LogEvent] = []

        def handler(event: BaseEvent):
            if isinstance(event, LogEvent):
                received_events.append(event)

        # Subscribe to log events
        h = subscribe("log", handler)

        # Enable logging handler
        log_handler = LoggingEventHandler.enable(
            logger_name="test_logger",
            level=logging.DEBUG
        )

        # Log something
        logger = logging.getLogger("test_logger")
        logger.info("Test log message")

        assert len(received_events) >= 1
        # Find our log message
        found = any(
            "Test log message" in e.message
            for e in received_events
        )
        assert found

        # Cleanup
        LoggingEventHandler.disable("test_logger")
        unsubscribe("log", h)


class TestEventLevels:
    """Tests for EventLevel enum."""

    def test_event_level_values(self):
        """Test EventLevel enum values."""
        assert EventLevel.DEBUG.value == "debug"
        assert EventLevel.INFO.value == "info"
        assert EventLevel.WARNING.value == "warning"
        assert EventLevel.ERROR.value == "error"
        assert EventLevel.CRITICAL.value == "critical"

    def test_event_level_ordering(self):
        """Test that event levels have logical ordering."""
        level_order = {
            EventLevel.DEBUG: 0,
            EventLevel.INFO: 1,
            EventLevel.WARNING: 2,
            EventLevel.ERROR: 3,
            EventLevel.CRITICAL: 4,
        }

        # Verify ordering is preserved
        levels = list(EventLevel)
        for i, level in enumerate(levels[:-1]):
            assert level_order[level] < level_order[levels[i + 1]]


class TestConcurrency:
    """Tests for concurrent event handling."""

    @pytest.mark.asyncio
    async def test_concurrent_emission(self):
        """Test concurrent event emission."""
        received: List[BaseEvent] = []
        lock = asyncio.Lock()

        async def handler(event: BaseEvent):
            async with lock:
                received.append(event)

        h = subscribe("agent", handler)

        # Emit events concurrently
        tasks = [
            emit_async(AgentStepStartedEvent(step_number=i))
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

        assert len(received) == 10

        unsubscribe("agent", h)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
