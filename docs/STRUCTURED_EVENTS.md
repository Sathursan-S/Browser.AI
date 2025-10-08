# Structured Event System

## Overview

The Browser.AI Structured Event System is a decoupled, SOLID-compliant event emission module that provides structured events for tasks, states, progress, LLM output, and more. It replaces the previous log-streaming approach with a clean event-driven architecture.

## Architecture

### Core Principles

The event system follows SOLID principles:

- **Single Responsibility**: Each module has one clear purpose
  - `schemas.py`: Event data structures
  - `emitter.py`: Event emission logic
  - `transport.py`: Event delivery mechanisms
  - `bridge.py`: Integration with existing systems

- **Open/Closed**: Extensible through new event types without modifying existing code

- **Liskov Substitution**: Interface-based design allows component substitution

- **Interface Segregation**: Clean, focused interfaces (`IEventEmitter`, `IEventTransport`)

- **Dependency Inversion**: Components depend on abstractions, not concrete implementations

### Components

```
browser_ai_gui/events/
├── __init__.py          # Public API
├── schemas.py           # Event data structures
├── emitter.py           # Event emission (pub-sub)
├── transport.py         # Event transport layer
└── bridge.py            # Integration bridge
```

## Event Types

### Base Event Structure

All events inherit from `BaseEvent` and include:

```python
@dataclass
class BaseEvent:
    event_id: str              # Unique event ID
    event_type: str            # Event type (e.g., "agent.start")
    category: EventCategory    # High-level category
    timestamp: str             # ISO 8601 timestamp
    severity: EventSeverity    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    session_id: Optional[str]  # Session tracking
    task_id: Optional[str]     # Task tracking
    metadata: Dict[str, Any]   # Additional data
```

### Event Categories

- **AGENT**: Agent lifecycle and execution events
- **TASK**: Task management events
- **LLM**: LLM interaction events
- **BROWSER**: Browser control events
- **PROGRESS**: Progress tracking events
- **SYSTEM**: System-level events

### Specific Event Types

#### Agent Events

- `AgentStartEvent`: Agent starts a task
- `AgentStepEvent`: Agent executes a step
- `AgentActionEvent`: Agent performs an action
- `AgentProgressEvent`: Progress update
- `AgentStateEvent`: State change
- `AgentCompleteEvent`: Task completion
- `AgentErrorEvent`: Error occurrence

#### LLM Events

- `LLMOutputEvent`: LLM interaction details (tokens, latency, etc.)

#### Task Events

- `TaskStateChangeEvent`: Task state transitions

## Usage

### Basic Usage

```python
from browser_ai_gui.events import (
    EventEmitter,
    EventTransport,
    AgentStartEvent,
    create_event_id,
    create_timestamp,
)

# 1. Create emitter and transport
emitter = EventEmitter()
transport = EventTransport(socketio=socketio, namespace="/extension")

# 2. Subscribe to events
def handle_event(event):
    print(f"Received: {event.event_type}")

subscription_id = emitter.subscribe(handle_event)

# 3. Emit events
event = AgentStartEvent(
    event_id=create_event_id(),
    event_type="agent.start",
    category=EventCategory.AGENT,
    timestamp=create_timestamp(),
    task_description="Search for Python tutorials",
    agent_id="agent-123",
    configuration={"use_vision": True}
)

emitter.emit(event)
```

### Using the Bridge

The bridge simplifies event creation:

```python
from browser_ai_gui.events import EventEmitter, EventTransport
from browser_ai_gui.events.bridge import EventBridge

# Create emitter, transport, and bridge
emitter = EventEmitter()
transport = EventTransport(socketio=socketio, namespace="/extension")
bridge = EventBridge(emitter, transport)

# Create and emit events easily
event = bridge.create_agent_start_event(
    task_description="Book a movie ticket",
    agent_id="agent-456",
    session_id="session-789",
    configuration={"max_steps": 50}
)
bridge.emit_structured_event(event)
```

### Filtering Events

```python
# Subscribe to specific event type
emitter.subscribe(callback, event_filter="agent.start")

# Subscribe to event category
emitter.subscribe_category(callback, EventCategory.AGENT)

# Subscribe to all events
emitter.subscribe(callback)
```

### Multiple Transports

```python
from browser_ai_gui.events import MultiTransport, EventTransport

# Create multiple transports
ws_transport = EventTransport(socketio=socketio, namespace="/extension")
callback_transport = EventTransport()
callback_transport.add_callback(my_logging_function)

# Combine them
multi = MultiTransport()
multi.add_transport(ws_transport)
multi.add_transport(callback_transport)

# Events sent to all transports
emitter.subscribe(multi.send)
```

## Integration

### WebSocket Integration

The event system integrates with Flask-SocketIO:

```python
# In websocket_server.py
self.event_emitter = EventEmitter()
self.event_transport = EventTransport(
    socketio=socketio,
    namespace="/extension",
    event_name="structured_event"
)
self.event_transport.connect()
```

Events are sent to clients as `structured_event` on the `/extension` namespace.

### Frontend Consumption

TypeScript/JavaScript clients receive structured events:

```typescript
socket.on('structured_event', (event) => {
  console.log(`Event: ${event.event_type}`);
  console.log(`Category: ${event.category}`);
  console.log(`Severity: ${event.severity}`);
  
  // Type-specific handling
  if (event.event_type === 'agent.progress') {
    updateProgressBar(event.progress_percentage);
  }
});
```

## Event Schema Examples

### Agent Start Event

```json
{
  "event_id": "uuid-1234",
  "event_type": "agent.start",
  "category": "agent",
  "timestamp": "2024-01-15T10:30:00Z",
  "severity": "info",
  "session_id": "session-abc",
  "task_id": "task-xyz",
  "task_description": "Book movie ticket",
  "agent_id": "agent-123",
  "configuration": {
    "use_vision": true,
    "max_steps": 50
  },
  "metadata": {}
}
```

### Agent Progress Event

```json
{
  "event_id": "uuid-5678",
  "event_type": "agent.progress",
  "category": "progress",
  "timestamp": "2024-01-15T10:31:00Z",
  "severity": "info",
  "session_id": "session-abc",
  "task_id": "task-xyz",
  "agent_id": "agent-123",
  "progress_percentage": 45.5,
  "current_step": 5,
  "total_steps": 11,
  "status_message": "Filling form fields",
  "metadata": {}
}
```

### LLM Output Event

```json
{
  "event_id": "uuid-9012",
  "event_type": "llm.output",
  "category": "llm",
  "timestamp": "2024-01-15T10:31:30Z",
  "severity": "info",
  "session_id": "session-abc",
  "task_id": "task-xyz",
  "agent_id": "agent-123",
  "llm_provider": "openai",
  "model_name": "gpt-4o",
  "prompt_tokens": 1500,
  "completion_tokens": 300,
  "total_tokens": 1800,
  "response_preview": "I will click on the movie...",
  "latency_ms": 850.5,
  "metadata": {}
}
```

## Migration from Old System

The event bridge provides backward compatibility:

```python
# Old way (still works)
event_adapter.emit_custom_event(
    EventType.AGENT_START,
    "Starting task",
    LogLevel.INFO,
    {"task": "demo"}
)

# New way (recommended)
event = bridge.create_agent_start_event(
    task_description="demo",
    agent_id="agent-123"
)
bridge.emit_structured_event(event)
```

Both methods work during the migration period. The bridge can also convert old `LogEvent` instances to structured events.

## Testing

```python
import pytest
from browser_ai_gui.events import EventEmitter, AgentStartEvent

def test_event_emission():
    emitter = EventEmitter()
    received_events = []
    
    def handler(event):
        received_events.append(event)
    
    emitter.subscribe(handler)
    
    event = AgentStartEvent(...)
    emitter.emit(event)
    
    assert len(received_events) == 1
    assert received_events[0].event_type == "agent.start"
```

## Best Practices

1. **Always use structured events** for new code
2. **Include session_id and task_id** for event correlation
3. **Set appropriate severity levels** for filtering and alerting
4. **Use metadata sparingly** - prefer typed fields when possible
5. **Handle transport failures gracefully** - events should never break the app
6. **Subscribe with filters** to reduce noise
7. **Clean up subscriptions** when components unmount

## Future Enhancements

- Event persistence and replay
- Event aggregation and analytics
- Rate limiting and throttling
- Event validation schemas
- Binary serialization for performance
- Event sourcing patterns
