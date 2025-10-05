# Chrome Extension State Management & Persistence

## Overview

This document describes the comprehensive state management and persistence system implemented for the Browser.AI Chrome extension. The system ensures that the extension maintains its state across reloads, refreshes, tab changes, and browser restarts.

## Problem Statement

### Issues Fixed

1. **ControlButtons not rendering properly**
   - Sometimes buttons would appear, sometimes not
   - State was inconsistent between reloads
   - UI didn't reflect actual server state

2. **State lost on extension lifecycle events**
   - Extension reload → state lost
   - Tab switch → state lost  
   - Browser restart → state lost
   - Page refresh → state lost

3. **No initial server synchronization**
   - Extension didn't request status on connection
   - UI could be out of sync with server
   - No way to recover from disconnection

## Solution Architecture

### Three-Layer State Management

```
┌─────────────────────────────────────────────────┐
│          1. In-Memory State (React)              │
│  - Fast access for UI rendering                  │
│  - useState hooks in SidePanel component         │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│     2. Persistent Storage (Chrome Storage)       │
│  - chrome.storage.local for extension state     │
│  - chrome.storage.sync for user settings        │
│  - Survives reloads and browser restarts        │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│       3. Server State (WebSocket/Python)         │
│  - Source of truth for task execution           │
│  - Real-time status updates via WebSocket       │
│  - Status requested on connection                │
└─────────────────────────────────────────────────┘
```

## Implementation

### 1. Global State Manager (`src/utils/state.ts`)

Centralized utility module for managing persistent extension state:

#### API Functions

```typescript
// Task Status Management
loadTaskStatus(): Promise<TaskStatus | null>
saveTaskStatus(status: TaskStatus): Promise<void>

// CDP Endpoint Management
loadCdpEndpoint(): Promise<string | null>
saveCdpEndpoint(endpoint: string): Promise<void>

// Task History
loadLastTask(): Promise<string | null>
saveLastTask(task: string): Promise<void>

// Cleanup
clearExtensionState(): Promise<void>

// Cross-Page Synchronization
onTaskStatusChanged(callback: (status: TaskStatus) => void): void
```

#### Storage Keys

```typescript
const STATE_KEYS = {
  TASK_STATUS: 'taskStatus',     // Current execution status
  CDP_ENDPOINT: 'cdpEndpoint',   // CDP WebSocket endpoint  
  LAST_TASK: 'lastTask',         // Last task description
}
```

#### Features

- **Async/Await API**: Promise-based for clean async handling
- **Automatic Logging**: All operations logged for debugging
- **Type Safety**: Full TypeScript types for all operations
- **Cross-Page Sync**: chrome.storage.onChanged listener for real-time updates

### 2. Enhanced SidePanel Component

#### State Lifecycle

```typescript
useEffect(() => {
  // 1. Load user settings (server URL, dev mode, etc.)
  loadSettings().then(setSettings)
  onSettingsChanged(setSettings)
  
  // 2. Load persisted task status
  loadTaskStatus().then((status) => {
    if (status) {
      setTaskStatus(status)
    }
  })
  
  // 3. Load persisted CDP endpoint
  loadCdpEndpoint().then((endpoint) => {
    if (endpoint) {
      setCdpEndpoint(endpoint)
    }
  })
  
  // 4. Listen for cross-page state changes
  onTaskStatusChanged(setTaskStatus)
}, [])
```

#### Auto-Persistence

```typescript
// Persist task status whenever it changes
useEffect(() => {
  saveTaskStatus(taskStatus)
}, [taskStatus])

// Persist CDP endpoint whenever it changes
useEffect(() => {
  if (cdpEndpoint) {
    saveCdpEndpoint(cdpEndpoint)
  }
}, [cdpEndpoint])
```

#### Server Synchronization

```typescript
newSocket.on('connect', () => {
  setConnected(true)
  newSocket.emit('extension_connect')
  
  // NEW: Request current status from server on connect
  newSocket.emit('get_status')
})

newSocket.on('status', (status: ProtocolTaskStatus) => {
  // Server status automatically persisted via useEffect
  setTaskStatus(status)
})
```

### 3. Improved ControlButtons Component

#### Consistent Rendering Logic

```typescript
export const ControlButtons = ({
  isRunning,
  isPaused,
  connected,
  onPause,
  onResume,
  onStop,
}: ControlButtonsProps) => {
  // Only show when task is running
  if (!isRunning) {
    return null
  }

  return (
    <div className="control-buttons-container">
      {/* Pause/Resume button */}
      {isPaused ? (
        <button onClick={onResume}>Resume</button>
      ) : (
        <button onClick={onPause}>Pause</button>
      )}
      
      {/* Stop button */}
      <button onClick={onStop}>Stop</button>
    </div>
  )
}
```

**Key Changes:**
- Simple boolean check for `isRunning`
- Consistent rendering of pause/resume button
- No complex conditional logic that could fail

## State Flow Diagrams

### Extension Startup Flow

```
1. Extension Opens/Reloads
   ↓
2. Load Persisted State from chrome.storage.local
   - Task Status (is_running, is_paused, current_task)
   - CDP Endpoint
   - Last Task
   ↓
3. Render UI with Persisted State
   - ControlButtons show if is_running=true
   - TaskStatus shows current_task
   ↓
4. Connect to WebSocket Server
   - Emit 'extension_connect'
   - Emit 'get_status' (request current state)
   ↓
5. Receive Server Status
   - Update taskStatus state
   - Auto-persist to chrome.storage.local
   ↓
6. UI Re-renders with Server State
   - ControlButtons update if needed
   - TaskStatus updates if needed
```

### State Update Flow

```
User Action (Pause/Resume/Stop)
   ↓
WebSocket Event Sent to Server
   ↓
Server Processes Action
   ↓
Server Broadcasts Status Update
   ↓
All Connected Clients Receive Status
   ↓
setTaskStatus(newStatus) Called
   ↓
React State Updated
   ↓
useEffect Triggered (taskStatus dependency)
   ↓
saveTaskStatus(taskStatus) Called
   ↓
State Persisted to chrome.storage.local
   ↓
UI Re-renders with New State
   ↓
ControlButtons Show Correct State
```

### Cross-Page Synchronization Flow

```
Page A: User pauses task
   ↓
Page A: setTaskStatus({..., is_paused: true})
   ↓
Page A: saveTaskStatus() saves to chrome.storage.local
   ↓
chrome.storage.onChanged event fires
   ↓
Page B: onTaskStatusChanged listener triggered
   ↓
Page B: setTaskStatus({..., is_paused: true})
   ↓
Page B: UI updates to show paused state
```

## Benefits

### 1. Reliability
- ✅ State always persists across reloads
- ✅ ControlButtons render consistently
- ✅ No more state desynchronization

### 2. User Experience  
- ✅ Extension "remembers" current task
- ✅ Survives browser restarts
- ✅ Works across multiple windows/tabs

### 3. Developer Experience
- ✅ Clean, centralized state management
- ✅ Easy to debug with automatic logging
- ✅ Type-safe API
- ✅ Clear separation of concerns

### 4. Robustness
- ✅ Handles disconnection gracefully
- ✅ Syncs with server on reconnection
- ✅ Cross-page state synchronization
- ✅ No race conditions

## Storage Usage

### chrome.storage.local
Stores extension-specific state (not synced):

```typescript
{
  taskStatus: {
    is_running: boolean
    current_task: string | null
    has_agent: boolean
    is_paused: boolean
    cdp_endpoint: string | null
  },
  cdpEndpoint: string,
  lastTask: string
}
```

**Why local?**
- Task state is session-specific
- CDP endpoint is machine-specific
- Faster access than sync storage

### chrome.storage.sync  
Stores user settings (synced across devices):

```typescript
{
  settings: {
    serverUrl: string
    devMode: boolean
    autoReconnect: boolean
    maxLogs: number
    showNotifications: boolean
  }
}
```

**Why sync?**
- User preferences should follow them
- Settings work across all devices
- Consistent experience everywhere

## Testing Checklist

### State Persistence
- [x] State persists on extension reload
- [x] State persists on page refresh
- [x] State persists on browser restart
- [x] State persists on tab switch
- [x] State persists on window close/reopen

### ControlButtons Rendering
- [x] Buttons show when task is running
- [x] Buttons hide when task is stopped
- [x] Pause button shows when task is running
- [x] Resume button shows when task is paused
- [x] Stop button always shows when running
- [x] Buttons update immediately on state change

### Server Synchronization
- [x] Status requested on connection
- [x] Status updated when server sends update
- [x] State persisted when server updates
- [x] UI reflects server state after sync
- [x] Works correctly after disconnection/reconnection

### Cross-Page Synchronization
- [x] State changes in one tab update other tabs
- [x] Multiple sidepanel instances stay in sync
- [x] Options page changes reflected in sidepanel

## Debugging

### Enable Logging

All state operations are logged to console:

```javascript
// State Manager Logs
[State] Loaded task status: {...}
[State] Saved task status: {...}
[State] Loaded CDP endpoint: ws://...
[State] Saved CDP endpoint: ws://...
[State] Task status changed: {...}

// SidePanel Logs  
Loaded persisted task status: {...}
Persisted task status: {...}
Connected to Browser.AI server
Received status update: {...}
```

### Inspect Storage

```javascript
// In DevTools Console (extension context)

// View all stored state
chrome.storage.local.get(null, console.log)

// View specific state
chrome.storage.local.get(['taskStatus'], console.log)

// Clear all state
chrome.storage.local.clear()
```

### Common Issues

**ControlButtons not showing:**
1. Check if `is_running` is true in storage
2. Verify WebSocket connection
3. Request status manually: `socket.emit('get_status')`

**State not persisting:**
1. Check console for storage errors
2. Verify chrome.storage permissions in manifest
3. Check storage quota (unlikely to be exceeded)

**Cross-page sync not working:**
1. Verify onChanged listener is registered
2. Check if both pages are using chrome.storage.local
3. Ensure state keys match exactly

## Future Enhancements

Potential improvements for future development:

1. **State Migration**
   - Version state schema
   - Migrate old state to new format
   - Handle breaking changes gracefully

2. **State Compression**
   - Compress logs before storage
   - LZ-string for large state objects
   - Reduce storage usage

3. **State Validation**
   - Validate state on load
   - Handle corrupted state gracefully
   - Provide defaults for invalid state

4. **Advanced Debugging**
   - State history/time-travel debugging
   - Export/import state for bug reports
   - Visual state inspector

5. **Performance Optimization**
   - Debounce state saves
   - Batch multiple updates
   - Only save changed fields

## Conclusion

The state management system provides a robust, reliable foundation for the Browser.AI Chrome extension. It ensures that users have a consistent experience regardless of how they interact with the extension, while also providing developers with a clean, debuggable architecture for managing complex asynchronous state.

All state persistence issues have been resolved, and the extension now maintains proper state across all lifecycle events.
