# Event System Quick Reference

## 📋 Event Topics & Count

| Topic | Events | Purpose |
|-------|--------|---------|
| `agent` | 7 | Agent lifecycle and execution |
| `browser` | 12 | Browser and page operations |
| `dom` | 5 | DOM tree processing |
| `controller` | 6 | Action registration and execution |
| `llm` | 5 | Language model interactions |
| `messages` | 6 | Message history management |
| `validation` | 4 | Output validation |
| `planning` | 4 | Task planning |
| `state` | 4 | State snapshots and memory |
| `error` | 4 | Error handling and recovery |
| `metrics` | 4 | Performance metrics |
| `user_interaction` | 3 | User input/help |
| `extension` | 6 | Browser extension and WebSocket |

**Total: 60+ Events**

## 🚀 Quick Start

### 1. Import Events
```python
from browser_ai.event_bus.core import EventManager, EventHandler
from browser_ai.event_bus.events import AgentStartedEvent, ActionExecutionCompletedEvent
```

### 2. Create Handler
```python
class MyHandler(EventHandler):
    def handle(self, event):
        print(f"Event: {event.name}")
```

### 3. Subscribe
```python
event_manager = EventManager()
event_manager.subscribe("agent", MyHandler())
```

### 4. Publish
```python
event = AgentStartedEvent(task="My task", use_vision=True)
await event_manager.publish_async("agent", event)
```

## 🎯 Most Common Events

### Agent Tracking
- `AgentStartedEvent` - When agent starts
- `AgentStepCompletedEvent` - After each step
- `AgentCompletedEvent` - When agent finishes

### Performance Monitoring
- `ActionExecutionCompletedEvent` - Action timing
- `StepDurationEvent` - Step timing
- `PerformanceMetricEvent` - Generic metrics

### LLM Cost Tracking
- `LLMRequestCompletedEvent` - Track tokens and cost

### Error Monitoring
- `ErrorOccurredEvent` - Any error
- `AgentStepFailedEvent` - Step failures

## 📊 Example Handlers

### Performance Metrics
```python
class MetricsCollector(EventHandler):
    def __init__(self):
        self.action_times = []
    
    def handle(self, event):
        if isinstance(event, ActionExecutionCompletedEvent):
            self.action_times.append(event.execution_time_ms)
```

### LLM Cost Tracker
```python
class CostTracker(EventHandler):
    def __init__(self):
        self.total_tokens = 0
    
    def handle(self, event):
        if isinstance(event, LLMRequestCompletedEvent):
            self.total_tokens += event.total_tokens or 0
```

### Progress Logger
```python
class ProgressLogger(EventHandler):
    def handle(self, event):
        if isinstance(event, AgentStepCompletedEvent):
            print(f"✅ Step {event.step_number} done")
```

## 📁 File Structure

```
browser_ai/event_bus/
├── events.py                    # 60+ event definitions
├── core.py                      # EventManager & EventHandler
├── handlers/
│   └── console.py              # Console handler example
├── README.md                   # This overview
├── EVENTS_DOCUMENTATION.md     # Full event reference
└── INTEGRATION_GUIDE.md        # Integration instructions

examples/
└── event_system_example.py     # 7 working examples
```

## 🔗 Event Flow Examples

### Successful Agent Execution
```
AgentStartedEvent
 → AgentStepStartedEvent
   → ActionExecutionStartedEvent
   → ActionExecutionCompletedEvent
 → AgentStepCompletedEvent
 → AgentCompletedEvent
```

### Page Navigation
```
PageNavigationStartedEvent
 → PageLoadedEvent
 → DOMProcessingStartedEvent
 → DOMTreeBuiltEvent
 → ScreenshotCapturedEvent
 → PageNavigationCompletedEvent
```

### Error Recovery
```
ActionExecutionFailedEvent
 → ErrorOccurredEvent
 → RecoveryAttemptedEvent
 → RecoverySuccessEvent
 → ActionExecutionStartedEvent (retry)
```

## 🛠️ Integration Checklist

- [ ] Review `EVENTS_DOCUMENTATION.md`
- [ ] Choose events to implement
- [ ] Add imports to components
- [ ] Emit events at key points
- [ ] Create custom handlers
- [ ] Test with `event_system_example.py`
- [ ] Set up monitoring/logging

## 💡 Use Cases

| Use Case | Events to Use |
|----------|---------------|
| **Performance Monitoring** | `PerformanceMetricEvent`, `StepDurationEvent`, `ActionExecutionCompletedEvent` |
| **Cost Tracking** | `LLMRequestCompletedEvent` |
| **Error Analysis** | `ErrorOccurredEvent`, `AgentStepFailedEvent`, `RecoveryAttemptedEvent` |
| **Audit Logging** | All events → JSON file |
| **Real-time Dashboard** | `AgentStepCompletedEvent`, `ActionExecutionStartedEvent`, etc. |
| **Testing** | Assert expected events received |
| **Analytics** | Aggregate metrics over time |

## 🔍 Finding Events

### By Component
- **Agent**: See "Agent Events" in docs
- **Browser**: See "Browser Events" in docs
- **Controller**: See "Controller & Action Events" in docs
- **LLM**: See "LLM Events" in docs

### By Purpose
- **Lifecycle**: `*StartedEvent`, `*CompletedEvent`, `*ClosedEvent`
- **Errors**: `*FailedEvent`, `ErrorOccurredEvent`
- **Performance**: `*DurationEvent`, `PerformanceMetricEvent`
- **State**: `*SnapshotEvent`, `MemoryUpdatedEvent`

## 📖 Documentation Links

1. **Full Event Reference**: `EVENTS_DOCUMENTATION.md`
2. **Integration Guide**: `INTEGRATION_GUIDE.md`
3. **Working Examples**: `examples/event_system_example.py`
4. **Overview**: `README.md` (detailed summary)

## ⚡ Quick Commands

```bash
# Run example
python examples/event_system_example.py

# View events documentation
cat browser_ai/event_bus/EVENTS_DOCUMENTATION.md

# View integration guide
cat browser_ai/event_bus/INTEGRATION_GUIDE.md
```

## 🎨 Event Naming Convention

Pattern: `[Component][Action][Event]`

Examples:
- `AgentStartedEvent` - Agent component started
- `PageNavigationCompletedEvent` - Page navigation completed
- `ActionExecutionFailedEvent` - Action execution failed

## 🔐 All Event Fields

Every event has:
- `topic` - Event topic/category
- `name` - Event name
- `timestamp` - When event occurred
- `...` - Event-specific fields

## 📝 Custom Events

```python
from browser_ai.event_bus.events import BaseEvent

class CustomEvent(BaseEvent):
    topic: str = "custom"
    name: str = "my_event"
    my_field: str
    my_number: int
```

## 🎯 Best Practices

1. ✅ Use async publish in async contexts
2. ✅ Include context IDs (agent_id, context_id)
3. ✅ Handle events in try/except blocks
4. ✅ Log event publishing errors
5. ✅ Use type checking in handlers
6. ✅ Test event sequences
7. ✅ Document custom events

## 🚦 Status

- ✅ Events defined (60+)
- ✅ Documentation complete
- ✅ Examples created
- ⏳ Integration pending (follow INTEGRATION_GUIDE.md)
- ⏳ Handlers to be customized per use case

---

**Last Updated**: October 2025  
**Version**: 1.0.0  
**Status**: Ready for integration
