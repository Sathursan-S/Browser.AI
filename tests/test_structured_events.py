"""
Tests for the structured event system
"""

import pytest
from datetime import datetime

from browser_ai_gui.events import (
    EventEmitter,
    EventTransport,
    AgentStartEvent,
    AgentCompleteEvent,
    AgentErrorEvent,
    EventCategory,
    EventSeverity,
    create_event_id,
    create_timestamp,
)
from browser_ai_gui.events.bridge import EventBridge


class TestEventEmitter:
    """Test EventEmitter functionality"""

    def test_emit_and_receive(self):
        """Test basic event emission and reception"""
        emitter = EventEmitter()
        received_events = []

        def handler(event):
            received_events.append(event)

        emitter.subscribe(handler)

        event = AgentStartEvent(
            event_id=create_event_id(),
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            task_description="Test task",
            agent_id="test-agent",
        )

        emitter.emit(event)

        assert len(received_events) == 1
        assert received_events[0].event_type == "agent.start"
        assert received_events[0].agent_id == "test-agent"

    def test_event_filtering(self):
        """Test event type filtering"""
        emitter = EventEmitter()
        start_events = []
        complete_events = []

        def start_handler(event):
            start_events.append(event)

        def complete_handler(event):
            complete_events.append(event)

        emitter.subscribe(start_handler, event_filter="agent.start")
        emitter.subscribe(complete_handler, event_filter="agent.complete")

        # Emit start event
        start_event = AgentStartEvent(
            event_id=create_event_id(),
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            task_description="Test",
            agent_id="agent-1",
        )
        emitter.emit(start_event)

        # Emit complete event
        complete_event = AgentCompleteEvent(
            event_id=create_event_id(),
            event_type="agent.complete",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            agent_id="agent-1",
            success=True,
        )
        emitter.emit(complete_event)

        assert len(start_events) == 1
        assert len(complete_events) == 1
        assert start_events[0].event_type == "agent.start"
        assert complete_events[0].event_type == "agent.complete"

    def test_category_filtering(self):
        """Test event category filtering"""
        emitter = EventEmitter()
        agent_events = []

        def handler(event):
            agent_events.append(event)

        emitter.subscribe_category(handler, EventCategory.AGENT)

        # This should be received
        event1 = AgentStartEvent(
            event_id=create_event_id(),
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            task_description="Test",
            agent_id="agent-1",
        )
        emitter.emit(event1)

        # This should also be received (same category)
        event2 = AgentCompleteEvent(
            event_id=create_event_id(),
            event_type="agent.complete",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            agent_id="agent-1",
            success=True,
        )
        emitter.emit(event2)

        assert len(agent_events) == 2

    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        emitter = EventEmitter()
        received_events = []

        def handler(event):
            received_events.append(event)

        sub_id = emitter.subscribe(handler)

        event = AgentStartEvent(
            event_id=create_event_id(),
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            task_description="Test",
            agent_id="agent-1",
        )

        emitter.emit(event)
        assert len(received_events) == 1

        # Unsubscribe
        emitter.unsubscribe(sub_id)

        # Emit again
        emitter.emit(event)
        assert len(received_events) == 1  # Should still be 1


class TestEventTransport:
    """Test EventTransport functionality"""

    def test_callback_transport(self):
        """Test callback-based transport"""
        transport = EventTransport()
        received_events = []

        def callback(event):
            received_events.append(event)

        transport.add_callback(callback)
        transport.connect()

        event = AgentStartEvent(
            event_id=create_event_id(),
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            task_description="Test",
            agent_id="agent-1",
        )

        transport.send(event)

        assert len(received_events) == 1
        assert received_events[0].agent_id == "agent-1"

    def test_connection_state(self):
        """Test transport connection state"""
        transport = EventTransport()

        assert not transport.is_connected()

        transport.connect()
        assert transport.is_connected()

        transport.disconnect()
        assert not transport.is_connected()


class TestEventBridge:
    """Test EventBridge functionality"""

    def test_create_agent_start_event(self):
        """Test creating agent start event via bridge"""
        emitter = EventEmitter()
        bridge = EventBridge(emitter)

        event = bridge.create_agent_start_event(
            task_description="Test task",
            agent_id="agent-123",
            session_id="session-456",
            configuration={"max_steps": 50},
        )

        assert event.event_type == "agent.start"
        assert event.task_description == "Test task"
        assert event.agent_id == "agent-123"
        assert event.session_id == "session-456"
        assert event.configuration["max_steps"] == 50

    def test_create_agent_complete_event(self):
        """Test creating agent complete event via bridge"""
        emitter = EventEmitter()
        bridge = EventBridge(emitter)

        event = bridge.create_agent_complete_event(
            agent_id="agent-123",
            success=True,
            result="Task completed successfully",
            execution_time_ms=5000.0,
            steps_executed=10,
        )

        assert event.event_type == "agent.complete"
        assert event.success is True
        assert event.result == "Task completed successfully"
        assert event.execution_time_ms == 5000.0
        assert event.steps_executed == 10

    def test_create_agent_error_event(self):
        """Test creating agent error event via bridge"""
        emitter = EventEmitter()
        bridge = EventBridge(emitter)

        event = bridge.create_agent_error_event(
            agent_id="agent-123",
            error_type="RuntimeError",
            error_message="Something went wrong",
            error_details="Stack trace here",
            recoverable=True,
        )

        assert event.event_type == "agent.error"
        assert event.error_type == "RuntimeError"
        assert event.error_message == "Something went wrong"
        assert event.recoverable is True
        assert event.severity == EventSeverity.ERROR

    def test_emit_through_bridge(self):
        """Test emitting events through bridge"""
        emitter = EventEmitter()
        transport = EventTransport()
        bridge = EventBridge(emitter, transport)

        received_events = []
        transport.add_callback(lambda e: received_events.append(e))
        transport.connect()

        event = bridge.create_agent_start_event(
            task_description="Test",
            agent_id="agent-1",
        )
        bridge.emit_structured_event(event)

        assert len(received_events) == 1
        assert received_events[0].agent_id == "agent-1"


class TestEventSchemas:
    """Test event schema serialization"""

    def test_agent_start_event_to_dict(self):
        """Test AgentStartEvent serialization"""
        event = AgentStartEvent(
            event_id="test-id",
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp="2024-01-15T10:00:00Z",
            severity=EventSeverity.INFO,
            session_id="session-1",
            task_id="task-1",
            task_description="Test task",
            agent_id="agent-1",
            configuration={"key": "value"},
        )

        data = event.to_dict()

        assert data["event_id"] == "test-id"
        assert data["event_type"] == "agent.start"
        assert data["category"] == "agent"
        assert data["severity"] == "info"
        assert data["task_description"] == "Test task"
        assert data["agent_id"] == "agent-1"
        assert data["configuration"]["key"] == "value"

    def test_agent_error_event_severity(self):
        """Test that error events have ERROR severity by default"""
        event = AgentErrorEvent(
            event_id="test-id",
            event_type="agent.error",
            category=EventCategory.AGENT,
            timestamp="2024-01-15T10:00:00Z",
            agent_id="agent-1",
            error_type="TestError",
            error_message="Test error",
        )

        assert event.severity == EventSeverity.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
