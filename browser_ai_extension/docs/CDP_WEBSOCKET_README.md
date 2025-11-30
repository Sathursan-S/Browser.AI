# CDP WebSocket Server for Browser.AI Extension

## Overview

The CDP WebSocket Server provides a dedicated communication channel between the Chrome extension and Browser.AI, allowing direct control of browser contexts via Chrome DevTools Protocol (CDP).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
│                                                              │
│  ┌────────────────┐          ┌─────────────────────┐       │
│  │  Side Panel UI │◄────────►│ Background Worker  │       │
│  │   (React)      │          │   (CDP Manager)    │       │
│  └────────┬───────┘          └──────────┬──────────┘       │
│           │                              │                  │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            │ WebSocket (/cdp)             │ chrome.debugger API
            │ (socket.io)                  │
            ▼                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  Browser.AI Python Server                     │
│                                                               │
│  ┌──────────────────────┐     ┌────────────────────────┐    │
│  │ CDP WebSocket Server │────►│ CDP Browser Context    │    │
│  │   (/cdp namespace)   │     │      Manager           │    │
│  └──────────────────────┘     └────────┬───────────────┘    │
│                                         │                     │
│                                         ▼                     │
│                         ┌──────────────────────────────┐     │
│                         │  Tab-Specific Browser        │     │
│                         │  Instances (CDP Connected)   │     │
│                         └──────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

## Key Features

1. **Tab-Specific Browser Contexts**: Each browser tab can have its own Browser.AI agent
2. **Direct CDP Command Proxy**: Send CDP commands through WebSocket to browser context
3. **Isolated Task Management**: Run independent tasks on different tabs
4. **Real-time Event Broadcasting**: Receive agent logs and status updates
5. **Automatic Cleanup**: Properly manages browser instances and connections

## WebSocket Namespace

The CDP server runs on the `/cdp` namespace (separate from the legacy `/extension` namespace).

**Connection URL**: `ws://localhost:5000/cdp`

## WebSocket Events

### Client → Server Events

#### `attach_tab`
Attach to a browser tab via CDP.

**Payload**:
```json
{
  "tab_id": 123,
  "cdp_url": "ws://localhost:9222/devtools/page/..."
}
```

**Response Event**: `attach_result`
```json
{
  "success": true,
  "message": "Successfully attached to tab 123",
  "tab_id": 123
}
```

---

#### `detach_tab`
Detach from a browser tab and cleanup resources.

**Payload**:
```json
{
  "tab_id": 123
}
```

**Response Event**: `detach_result`
```json
{
  "success": true,
  "message": "Successfully detached from tab 123",
  "tab_id": 123
}
```

---

#### `send_cdp_command`
Send a CDP command to the browser context.

**Payload**:
```json
{
  "command_id": "unique-command-id",
  "tab_id": 123,
  "method": "Page.navigate",
  "params": {
    "url": "https://example.com"
  }
}
```

**Response Event**: `cdp_response`
```json
{
  "command_id": "unique-command-id",
  "success": true,
  "result": {
    "frameId": "...",
    "loaderId": "..."
  },
  "error": null
}
```

---

#### `start_task`
Start a Browser.AI task on a specific tab.

**Payload**:
```json
{
  "tab_id": 123,
  "task": "Find the price of the first product"
}
```

**Response Events**: 
- `task_started`: Confirmation that task has started
- `task_completed`: Result when task finishes

```json
{
  "success": true,
  "message": "Task started successfully",
  "tab_id": 123,
  "task": "Find the price of the first product"
}
```

---

#### `get_tab_status`
Get the current status of a specific tab.

**Payload**:
```json
{
  "tab_id": 123
}
```

**Response Event**: `tab_status`
```json
{
  "tab_id": 123,
  "is_attached": true,
  "has_agent": false,
  "current_task": null,
  "is_running": false
}
```

---

### Server → Client Events

#### `connected`
Sent when client successfully connects.

```json
{
  "client_id": "socket-session-id"
}
```

---

#### `log_event`
Broadcast of agent execution logs.

```json
{
  "timestamp": "2025-10-05T10:30:00.000Z",
  "level": "INFO",
  "message": "Navigating to page",
  "event_type": "AGENT_STEP",
  "metadata": {
    "step": 1,
    "action": "navigate"
  }
}
```

---

#### `error`
Error messages from the server.

```json
{
  "message": "Tab ID is required"
}
```

## Usage Examples

### Extension Background Script

```typescript
// Connect to CDP WebSocket server
const socket = io('http://localhost:5000/cdp', {
  transports: ['websocket'],
  reconnection: true
})

// Listen for connection
socket.on('connected', (data) => {
  console.log('Connected to CDP server:', data.client_id)
})

// Attach to current tab
async function attachToCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  
  // Attach debugger first
  await chrome.debugger.attach({ tabId: tab.id }, '1.3')
  
  // Get CDP URL (in extension mode, use special identifier)
  socket.emit('attach_tab', {
    tab_id: tab.id,
    cdp_url: `extension-tab-${tab.id}`
  })
}

// Listen for attach result
socket.on('attach_result', (result) => {
  if (result.success) {
    console.log('Attached to tab:', result.tab_id)
  } else {
    console.error('Failed to attach:', result.error)
  }
})

// Send CDP command through WebSocket
function sendCdpCommand(tabId, method, params) {
  const commandId = `cmd-${Date.now()}`
  
  socket.emit('send_cdp_command', {
    command_id: commandId,
    tab_id: tabId,
    method: method,
    params: params
  })
  
  return new Promise((resolve, reject) => {
    socket.once('cdp_response', (response) => {
      if (response.command_id === commandId) {
        if (response.success) {
          resolve(response.result)
        } else {
          reject(new Error(response.error))
        }
      }
    })
  })
}

// Start a task
function startTask(tabId, task) {
  socket.emit('start_task', {
    tab_id: tabId,
    task: task
  })
}

// Listen for task events
socket.on('task_started', (result) => {
  console.log('Task started:', result)
})

socket.on('task_completed', (result) => {
  console.log('Task completed:', result)
})

// Listen for log events
socket.on('log_event', (event) => {
  console.log(`[${event.level}] ${event.message}`)
})

// Clean up on tab close
chrome.tabs.onRemoved.addListener((tabId) => {
  socket.emit('detach_tab', { tab_id: tabId })
})
```

### Python Client Example

```python
from socketio import Client

sio = Client()

@sio.on('connected', namespace='/cdp')
def on_connected(data):
    print(f"Connected: {data['client_id']}")

@sio.on('attach_result', namespace='/cdp')
def on_attach_result(data):
    if data['success']:
        print(f"Attached to tab {data['tab_id']}")
    else:
        print(f"Attachment failed: {data['error']}")

@sio.on('cdp_response', namespace='/cdp')
def on_cdp_response(data):
    print(f"CDP Response: {data}")

@sio.on('log_event', namespace='/cdp')
def on_log_event(data):
    print(f"[{data['level']}] {data['message']}")

# Connect
sio.connect('http://localhost:5000', namespaces=['/cdp'])

# Attach to tab
sio.emit('attach_tab', {
    'tab_id': 123,
    'cdp_url': 'ws://localhost:9222/devtools/page/abc123'
}, namespace='/cdp')

# Send CDP command
sio.emit('send_cdp_command', {
    'command_id': 'cmd-001',
    'tab_id': 123,
    'method': 'Page.navigate',
    'params': {'url': 'https://example.com'}
}, namespace='/cdp')

# Start task
sio.emit('start_task', {
    'tab_id': 123,
    'task': 'Find the main heading on the page'
}, namespace='/cdp')

sio.wait()
```

## CDP Command Examples

### Navigate to URL

```json
{
  "method": "Page.navigate",
  "params": {
    "url": "https://example.com"
  }
}
```

### Click Element

```json
{
  "method": "Runtime.evaluate",
  "params": {
    "expression": "document.querySelector('.button').click()"
  }
}
```

### Get Page Title

```json
{
  "method": "Runtime.evaluate",
  "params": {
    "expression": "document.title"
  }
}
```

### Take Screenshot

```json
{
  "method": "Page.captureScreenshot",
  "params": {
    "format": "png"
  }
}
```

## Implementation Details

### CDPBrowserContextManager

Manages browser instances and contexts per tab:

- **Tab Tracking**: Maps tab IDs to browser instances
- **Agent Management**: Each tab can have its own agent
- **Task Isolation**: Tasks run independently per tab
- **Resource Cleanup**: Automatic cleanup on detach

### CDPWebSocketNamespace

Flask-SocketIO namespace handler:

- **Event Handling**: Processes WebSocket events
- **Threading**: Runs async operations in background threads
- **Broadcasting**: Sends log events to all connected clients
- **Error Handling**: Proper error responses for all operations

## Integration with Existing Extension

The CDP WebSocket server is complementary to the existing `/extension` namespace:

- **Legacy `/extension`**: For simple task execution without CDP
- **New `/cdp`**: For advanced CDP-based browser control

Both can run simultaneously on the same server.

## Starting the Server

The CDP WebSocket server is automatically initialized when starting the web app:

```bash
uv run browser_ai_gui/main.py web --port 5000
```

Or:

```bash
python -m browser_ai_gui.main web --port 5000
```

The CDP namespace will be available at: `ws://localhost:5000/cdp`

## Error Handling

All operations return a consistent response format:

```json
{
  "success": true|false,
  "message": "Success message",
  "error": "Error message if failed",
  "tab_id": 123,
  "result": {}  // For CDP commands
}
```

## Limitations

1. **Browser Instance Lifecycle**: Browser instances are managed per tab attachment
2. **CDP URL Requirement**: For non-extension mode, requires valid CDP WebSocket URL
3. **Single Agent Per Tab**: Only one agent can run per tab at a time
4. **Threading Model**: Uses threading for async operations (Flask-SocketIO limitation)

## Security Considerations

1. **CORS**: Configured to allow all origins (development mode)
2. **Authentication**: No authentication implemented (add for production)
3. **CDP Access**: Direct CDP access requires careful validation
4. **Resource Limits**: No limits on concurrent tabs/agents (implement for production)

## Future Improvements

- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Connection pooling
- [ ] Better error recovery
- [ ] Metrics and monitoring
- [ ] Support for multiple agents per tab
- [ ] Persistent session management
