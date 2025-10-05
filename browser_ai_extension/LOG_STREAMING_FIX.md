# Log Streaming Fix

## Problem

Logs were not streaming properly from the Browser.AI server to the Chrome extension.

## Root Cause

There were **two different `LogEvent` dataclass definitions** with incompatible type structures:

1. **`event_adapter.py`**: Used Python native types
   - `timestamp: datetime` (Python datetime object)
   - `level: LogLevel` (enum instance)
   - `event_type: EventType` (enum instance)

2. **`protocol.py`**: Used JSON-serializable string types
   - `timestamp: str` (ISO 8601 string)
   - `level: str` (string value like "INFO")
   - `event_type: str` (string value like "log")

When `LogCapture.emit()` created a `LogEvent` with datetime/enum types and tried to serialize it for WebSocket transmission, the types didn't match what the extension expected.

## Solution

**Unified the protocol** by making `event_adapter.py` use the protocol-defined `LogEvent`:

### Changes Made

1. **`event_adapter.py`**:
   - Removed duplicate `LogLevel`, `EventType`, and `LogEvent` definitions
   - Imported them from `protocol.py` instead
   - Updated `LogCapture.emit()` to create `LogEvent` with string types:
     ```python
     event = LogEvent(
         timestamp=datetime.fromtimestamp(record.created).isoformat(),
         level=level.value,  # Convert enum to string
         event_type=event_type.value,  # Convert enum to string
         ...
     )
     ```
   - Updated `emit_custom_event()` similarly

2. **`websocket_server.py`**:
   - Simplified `broadcast_event()` to use `event.to_dict()` directly
   - Removed unnecessary `_serialize_log_event()` method
   - Cleaned up unused imports

## Benefits

✅ **Type Safety**: Single source of truth for protocol types  
✅ **Consistency**: Server and extension use matching data structures  
✅ **Maintainability**: Changes to protocol only need to be made in one place  
✅ **Reliability**: Logs now stream properly with correct type serialization

## Data Flow

```
Browser.AI Logger
    ↓
LogCapture.emit() → LogEvent (timestamp: str, level: str, event_type: str)
    ↓
event_queue.put()
    ↓
EventAdapter._process_events() → callback(event)
    ↓
ExtensionWebSocketHandler.broadcast_event(event)
    ↓
socketio.emit("log_event", event.to_dict())
    ↓
Extension SidePanel.tsx receives correct format
    ↓
addLog(event) → Display in UI
```

## Testing

To verify the fix:

1. Start the server: `python -m browser_ai_gui.main web --port 5000`
2. Load the extension in Chrome
3. Start a task from the extension
4. Verify logs appear in real-time in the extension side panel

Expected behavior:
- Logs should stream immediately as the agent executes
- Different event types should be color-coded correctly
- Timestamps should display properly
- No console errors about type mismatches
