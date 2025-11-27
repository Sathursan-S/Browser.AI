#!/usr/bin/env python3
"""
Example: Event Streaming with Browser.AI

This example demonstrates how to use the event bus for real-time
event streaming during agent execution. Perfect for:
- UI integration (WebSocket, SSE)
- Real-time logging dashboards
- Progress tracking
- Custom monitoring systems

Usage:
    python examples/event_streaming_example.py
"""

import asyncio
from datetime import datetime

from browser_ai.event_bus import (
    # Core functions
    subscribe,
    unsubscribe,
    emit,
    emit_async,
    EventLevel,
    # Handler classes for streaming
    StreamingEventHandler,
    FilteredEventHandler,
    # Event types
    BaseEvent,
    AgentStartedEvent,
    AgentStepStartedEvent,
    AgentStepCompletedEvent,
    AgentCompletedEvent,
    AgentFailedEvent,
    LLMRequestStartedEvent,
    LLMRequestCompletedEvent,
    ErrorOccurredEvent,
)
from browser_ai.event_bus.handlers import LoggingEventHandler, ConsoleHandler


def simple_subscriber_example():
    """Example 1: Simple event subscription with a callback function."""
    print("\n" + "=" * 60)
    print("Example 1: Simple Event Subscription")
    print("=" * 60)

    received_events = []

    def my_event_handler(event: BaseEvent):
        """Handle incoming events."""
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
        print(f"[{timestamp}] 📨 {event.topic}/{event.name}")
        received_events.append(event)

    # Subscribe to agent events
    handler = subscribe("agent", my_event_handler)

    # Emit some test events
    emit(AgentStartedEvent(task="Search for Python tutorials", use_vision=True))
    emit(AgentStepStartedEvent(step_number=1))
    emit(AgentStepCompletedEvent(step_number=1, actions_taken=[{"click": {"index": 5}}]))

    print(f"\n✅ Received {len(received_events)} events")

    # Clean up
    unsubscribe("agent", handler)


def wildcard_subscriber_example():
    """Example 2: Subscribe to all events with wildcard."""
    print("\n" + "=" * 60)
    print("Example 2: Wildcard Subscription (All Events)")
    print("=" * 60)

    event_counts = {"agent": 0, "llm": 0, "error": 0}

    def count_events(event: BaseEvent):
        topic = event.topic
        if topic in event_counts:
            event_counts[topic] += 1
        print(f"  📊 {event.topic}/{event.name}")

    # Subscribe to ALL events
    handler = subscribe("*", count_events)

    # Emit events to different topics
    emit(AgentStartedEvent(task="Test task"))
    emit(LLMRequestStartedEvent(purpose="action", model_name="gpt-4"))
    emit(LLMRequestCompletedEvent(purpose="action", response_time_ms=1500))
    emit(ErrorOccurredEvent(
        error_type="test",
        error_message="Test error",
        component="test"
    ))

    print(f"\n📈 Event counts: {event_counts}")

    unsubscribe("*", handler)


def filtered_handler_example():
    """Example 3: Filter events by level."""
    print("\n" + "=" * 60)
    print("Example 3: Filtered Event Handler (Errors Only)")
    print("=" * 60)

    from browser_ai.event_bus.core import EventHandler

    class PrintHandler(EventHandler):
        def handle(self, event: BaseEvent):
            print(f"  ⚠️ FILTERED: {event.topic}/{event.name}")

    # Create filtered handler that only receives error-level events
    inner = PrintHandler()
    filtered = FilteredEventHandler(inner, level_filter=EventLevel.ERROR)

    subscribe("agent", filtered)
    subscribe("error", filtered)

    print("Emitting info-level event (should be filtered)...")
    emit(AgentStartedEvent(task="Test"))

    print("Emitting error-level event (should pass through)...")
    emit(ErrorOccurredEvent(
        error_type="TestError",
        error_message="Something went wrong",
        component="test"
    ))

    unsubscribe("agent", filtered)
    unsubscribe("error", filtered)


async def async_streaming_example():
    """Example 4: Async streaming for real-time UI updates."""
    print("\n" + "=" * 60)
    print("Example 4: Streaming Event Handler (For WebSocket/SSE)")
    print("=" * 60)

    # Create a streaming handler for real-time event delivery
    stream_handler = StreamingEventHandler(max_queue_size=100)
    subscribe("*", stream_handler)

    # Simulate background event emission (like agent running)
    async def emit_events():
        await emit_async(AgentStartedEvent(task="Background task"))
        await asyncio.sleep(0.1)
        await emit_async(AgentStepStartedEvent(step_number=1))
        await asyncio.sleep(0.1)
        await emit_async(AgentStepCompletedEvent(step_number=1, actions_taken=[]))
        await asyncio.sleep(0.1)
        await emit_async(AgentCompletedEvent(
            task="Background task",
            total_steps=1,
            success=True,
            final_result="Done!"
        ))

    # Start event emission in background
    asyncio.create_task(emit_events())

    # Stream events as they arrive (like sending to WebSocket clients)
    print("Streaming events (timeout after 1 second):")
    count = 0
    async for event in stream_handler.stream(timeout=0.5):
        print(f"  🔄 Stream: {event.topic}/{event.name}")
        count += 1
        if count >= 4:
            break

    stream_handler.close()
    unsubscribe("*", stream_handler)
    print(f"\n✅ Streamed {count} events")


def logging_integration_example():
    """Example 5: Integrate logging with event bus."""
    print("\n" + "=" * 60)
    print("Example 5: Logging Integration")
    print("=" * 60)

    import logging

    log_events = []

    def capture_logs(event: BaseEvent):
        if hasattr(event, 'message'):
            log_events.append(event)
            # Only print if not too many (avoid recursion in output)
            if len(log_events) <= 5:
                print(f"  📝 Log: {event.message[:50]}...")

    # Subscribe to log events
    handler = subscribe("log", capture_logs)

    # Enable logging event emission for a test logger (not browser_ai to avoid noise)
    log_handler = LoggingEventHandler.enable(
        logger_name="test_app",
        level=logging.INFO
    )

    # Log something
    logger = logging.getLogger("test_app")
    logger.info("This is a test log message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    print(f"\n✅ Captured {len(log_events)} log events")

    # Clean up
    LoggingEventHandler.disable("test_app")
    unsubscribe("log", handler)


def json_serialization_example():
    """Example 6: JSON serialization for API/WebSocket."""
    print("\n" + "=" * 60)
    print("Example 6: JSON Serialization (For APIs)")
    print("=" * 60)

    # Create an event
    event = AgentStepCompletedEvent(
        step_number=5,
        agent_id="agent-123",
        actions_taken=[
            {"click": {"index": 10}},
            {"input_text": {"index": 20, "text": "Hello"}}
        ],
        result="Successfully clicked and typed"
    )

    # Serialize to JSON (perfect for WebSocket/API responses)
    json_str = event.model_dump_json(indent=2)
    print(f"JSON Output:\n{json_str}")

    # Can also get as dict
    event_dict = event.model_dump()
    print(f"\nDict keys: {list(event_dict.keys())}")


async def main():
    """Run all examples."""
    print("\n🚀 Browser.AI Event Streaming Examples")
    print("=" * 60)

    # Synchronous examples
    simple_subscriber_example()
    wildcard_subscriber_example()
    filtered_handler_example()
    json_serialization_example()
    logging_integration_example()

    # Async example
    await async_streaming_example()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
