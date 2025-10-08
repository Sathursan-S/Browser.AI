# Browser.AI Structured Event System

A decoupled, SOLID-compliant event emission system for Browser.AI.

## Overview

This module provides a structured event system that replaces log-based event streaming with properly typed, rich events for tasks, states, progress, LLM output, and more.

## Quick Start

```python
from browser_ai_gui.events import EventEmitter, EventTransport
from browser_ai_gui.events.bridge import EventBridge

# Setup
emitter = EventEmitter()
transport = EventTransport(socketio=socketio, namespace="/extension")
bridge = EventBridge(emitter, transport)

# Create and emit events
event = bridge.create_agent_start_event(
    task_description="Book a movie ticket",
    agent_id="agent-123",
    configuration={"max_steps": 50}
)
bridge.emit_structured_event(event)

# Subscribe to events
emitter.subscribe(lambda e: print(e.event_type))
```

## Event Types

- **Agent Events:** start, step, action, progress, state_change, complete, error
- **LLM Events:** output (tokens, latency, model info)
- **Task Events:** state_change

## Features

✅ **Type-safe** - Full type checking with dataclasses  
✅ **Rich metadata** - Session ID, task ID, timestamps  
✅ **Event filtering** - By type, category, severity  
✅ **Multiple transports** - WebSocket, callbacks  
✅ **SOLID design** - Decoupled, extensible, testable  
✅ **Backward compatible** - Works with existing event_adapter  

## Architecture

```
events/
├── __init__.py     # Public API
├── schemas.py      # Event data structures
├── emitter.py      # Event emission (pub-sub)
├── transport.py    # Transport layer
└── bridge.py       # Integration helpers
```

## Example Event

```json
{
  "event_id": "uuid-123",
  "event_type": "agent.progress",
  "category": "progress",
  "timestamp": "2024-01-15T10:30:00Z",
  "severity": "info",
  "session_id": "session-abc",
  "task_id": "task-xyz",
  "agent_id": "agent-123",
  "progress_percentage": 45.5,
  "current_step": 5,
  "total_steps": 11,
  "status_message": "Filling form fields"
}
```

## Documentation

- [Complete Backend Guide](../../docs/STRUCTURED_EVENTS.md)
- [Frontend Integration](../../docs/FRONTEND_INTEGRATION.md)
- [Implementation Summary](../../docs/IMPLEMENTATION_SUMMARY.md)

## Demo

Run the demo: `python ../../structured_events_demo.py`

## Testing

```bash
pytest ../../tests/test_structured_events.py -v
```

## SOLID Principles

- **Single Responsibility:** Each module has one purpose
- **Open/Closed:** Extensible via new event types
- **Liskov Substitution:** Interface-based design
- **Interface Segregation:** Focused interfaces
- **Dependency Inversion:** Depends on abstractions
