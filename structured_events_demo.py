#!/usr/bin/env python3
"""
Example: Using the Browser.AI Structured Event System

This example demonstrates how to use the structured event system
to track agent execution, progress, and results.
"""

import json
from browser_ai_gui.events import (
    EventEmitter,
    EventTransport,
    EventCategory,
    EventSeverity,
    AgentActionEvent,
    AgentProgressEvent,
    LLMOutputEvent,
    create_event_id,
    create_timestamp,
)
from browser_ai_gui.events.bridge import EventBridge


def main():
    """Demonstrate structured event system usage"""
    
    print("=" * 60)
    print("Browser.AI Structured Event System Demo")
    print("=" * 60)
    print()
    
    # 1. Create event emitter and transport
    print("1. Setting up event system...")
    emitter = EventEmitter()
    transport = EventTransport()  # In-memory transport with callbacks
    bridge = EventBridge(emitter, transport)
    transport.connect()
    print("   ✓ Event system initialized")
    print()
    
    # 2. Subscribe to all events
    print("2. Subscribing to events...")
    all_events = []
    
    def log_all_events(event):
        all_events.append(event)
        print(f"   📡 Event: {event.event_type}")
        print(f"      Category: {event.category.value}")
        print(f"      Severity: {event.severity.value}")
        if hasattr(event, 'agent_id'):
            print(f"      Agent ID: {event.agent_id}")
        print()
    
    emitter.subscribe(log_all_events)
    print("   ✓ Subscribed to all events")
    print()
    
    # 3. Subscribe to specific event types
    print("3. Setting up filtered subscriptions...")
    error_events = []
    
    def log_errors(event):
        error_events.append(event)
        print(f"   ❌ ERROR: {event.error_message}")
        print(f"      Type: {event.error_type}")
        print(f"      Recoverable: {event.recoverable}")
        print()
    
    emitter.subscribe(log_errors, event_filter="agent.error")
    print("   ✓ Subscribed to error events")
    print()
    
    # 4. Subscribe to category
    print("4. Subscribing to AGENT category...")
    agent_events = []
    emitter.subscribe_category(lambda e: agent_events.append(e), EventCategory.AGENT)
    print("   ✓ Subscribed to AGENT category events")
    print()
    
    # 5. Simulate agent lifecycle with events
    print("5. Simulating agent task execution...")
    print()
    
    # Agent starts
    print("   🚀 Starting agent task...")
    event = bridge.create_agent_start_event(
        task_description="Book a movie ticket for 'Inception' in Colombo tomorrow",
        agent_id="agent-demo-001",
        session_id="session-abc123",
        task_id="task-xyz789",
        configuration={
            "use_vision": True,
            "max_steps": 50,
            "browser": "chromium"
        }
    )
    bridge.emit_structured_event(event)
    
    # Agent performs actions
    print("   🔍 Agent performing actions...")
    
    action_event = AgentActionEvent(
        event_id=create_event_id(),
        event_type="agent.action",
        category=EventCategory.AGENT,
        timestamp=create_timestamp(),
        session_id="session-abc123",
        task_id="task-xyz789",
        agent_id="agent-demo-001",
        action_type="navigate",
        action_description="Navigate to movie booking website",
        action_parameters={"url": "https://example-cinema.com"},
        action_result="success"
    )
    emitter.emit(action_event)
    
    # Progress update
    print("   📊 Reporting progress...")
    
    progress_event = AgentProgressEvent(
        event_id=create_event_id(),
        event_type="agent.progress",
        category=EventCategory.PROGRESS,
        timestamp=create_timestamp(),
        session_id="session-abc123",
        task_id="task-xyz789",
        agent_id="agent-demo-001",
        progress_percentage=45.5,
        current_step=5,
        total_steps=11,
        status_message="Filling booking form"
    )
    emitter.emit(progress_event)
    
    # LLM interaction
    print("   🤖 LLM processing...")
    
    llm_event = LLMOutputEvent(
        event_id=create_event_id(),
        event_type="llm.output",
        category=EventCategory.LLM,
        timestamp=create_timestamp(),
        session_id="session-abc123",
        task_id="task-xyz789",
        agent_id="agent-demo-001",
        llm_provider="openai",
        model_name="gpt-4o",
        prompt_tokens=1500,
        completion_tokens=300,
        total_tokens=1800,
        response_preview="I will click on the 'Book Now' button...",
        latency_ms=850.5
    )
    emitter.emit(llm_event)
    
    # Simulating an error (recoverable)
    print("   ⚠️  Encountering a recoverable error...")
    error_event = bridge.create_agent_error_event(
        agent_id="agent-demo-001",
        error_type="ElementNotFoundError",
        error_message="Could not find the 'Confirm' button",
        session_id="session-abc123",
        task_id="task-xyz789",
        error_details="Selector: button.confirm, Timeout: 5000ms",
        recoverable=True
    )
    bridge.emit_structured_event(error_event)
    
    # Agent completes successfully
    print("   ✅ Task completed...")
    complete_event = bridge.create_agent_complete_event(
        agent_id="agent-demo-001",
        success=True,
        result="Movie ticket booked successfully. Booking ID: ABC123",
        session_id="session-abc123",
        task_id="task-xyz789",
        execution_time_ms=15000.0,
        steps_executed=11
    )
    bridge.emit_structured_event(complete_event)
    
    print()
    
    # 6. Display statistics
    print("=" * 60)
    print("Event Statistics")
    print("=" * 60)
    print(f"Total events emitted: {len(all_events)}")
    print(f"Agent category events: {len(agent_events)}")
    print(f"Error events: {len(error_events)}")
    print()
    
    # 7. Show event details
    print("=" * 60)
    print("Event Details (First Event)")
    print("=" * 60)
    if all_events:
        first_event = all_events[0]
        event_dict = first_event.to_dict()
        print(json.dumps(event_dict, indent=2))
    print()
    
    # 8. Demonstrate filtering
    print("=" * 60)
    print("Filtered Events")
    print("=" * 60)
    print(f"\nError events captured: {len(error_events)}")
    for err in error_events:
        print(f"  - {err.error_type}: {err.error_message}")
    print()
    
    # 9. Cleanup
    print("=" * 60)
    print("Cleanup")
    print("=" * 60)
    emitter.clear_all_subscriptions()
    transport.disconnect()
    print("✓ Event system cleaned up")
    print()
    
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
