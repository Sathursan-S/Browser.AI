# Browser.AI Chrome Extension - UI Features

## Overview

The Browser.AI Chrome Extension now features a modern, GitHub Copilot-inspired UI with real-time execution tracking, chat interface, and intelligent notification system.

## Key Features

### 🎨 Modern Side Panel UI

- **GitHub Copilot-Style Interface**: Clean, modern design with smooth animations
- **Component-Based Architecture**: Modular, maintainable React components
- **Real-Time Execution Logs**: Animated log entries with color-coded severity levels
- **Chat Interface**: Bottom-aligned chat input for task commands
- **Task Controls**: Stop, Pause, and Resume buttons for task management

### 🔔 Smart Notifications

The extension automatically shows popup notifications for:

- **User Interaction Required**: When the AI needs human input to proceed
- **Task Completion**: When a task successfully completes
- **Errors**: When critical errors occur during execution

Notifications include:
- Clear, actionable messages
- Timestamp for tracking
- Quick access to side panel
- Optional result display in JSON format

### 🚀 Auto-Open Side Panel

Click the extension icon to automatically open the side panel - no need for separate popup windows!

## Components

### 1. ChatInput Component
Located at: `src/sidepanel/components/ChatInput.tsx`

**Features:**
- Modern text input with send button
- Auto-expand textarea
- Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Disabled state when disconnected

**Usage:**
```tsx
<ChatInput 
  onSendTask={(task) => handleStartTask(task)}
  disabled={!connected || taskStatus.is_running}
/>
```

### 2. ExecutionLog Component
Located at: `src/sidepanel/components/ExecutionLog.tsx`

**Features:**
- Animated log entries with slide-in effect
- Color-coded severity levels (INFO, WARNING, ERROR, DEBUG)
- Emoji icon mapping for visual clarity
- Auto-scroll to latest logs
- Timestamp display

**Log Levels:**
- 🔵 **INFO**: General information
- 🟡 **WARNING**: Warnings and cautions
- 🔴 **ERROR**: Errors and failures
- 🟣 **DEBUG**: Debug information

**Usage:**
```tsx
<ExecutionLog logs={logs} />
```

### 3. ControlButtons Component
Located at: `src/sidepanel/components/ControlButtons.tsx`

**Features:**
- Stop, Pause, Resume task controls
- Visual feedback with hover effects
- Disabled states based on task status
- Icon-based buttons for clarity

**Usage:**
```tsx
<ControlButtons
  onStop={handleStopTask}
  onPause={handlePauseTask}
  onResume={handleResumeTask}
  isRunning={taskStatus.is_running}
  isPaused={taskStatus.is_paused}
/>
```

### 4. TaskStatus Component
Located at: `src/sidepanel/components/TaskStatus.tsx`

**Features:**
- Real-time connection status
- Current task display
- Running/Paused/Stopped indicators
- Animated status badges

**Usage:**
```tsx
<TaskStatus
  connected={connected}
  taskStatus={taskStatus}
/>
```

### 5. Notification Popup
Located at: `src/notification/Notification.tsx`

**Features:**
- Full-screen popup with glassmorphism backdrop
- Type-specific styling (warning, success, error)
- Auto-close functionality
- Quick access to side panel
- Optional result display

**Notification Types:**
- `user_interaction`: Yellow border, warning icon ⚠️
- `task_complete`: Green border, success icon ✅
- `error`: Red border, error icon ❌

## User Interaction Flow

### 1. Starting a Task

1. Click extension icon → Side panel opens automatically
2. Enter task in chat input at bottom
3. Press Enter or click Send button
4. Execution logs appear in real-time with animations

### 2. Handling User Interactions

When the AI needs user input:

1. **Popup notification** appears automatically
2. Notification shows the reason and current page URL
3. Options:
   - **Open Side Panel**: Go to side panel to view details
   - **Dismiss**: Close notification (task remains paused)
4. Complete the required action in the browser
5. AI auto-detects completion and resumes

### 3. Task Controls

- **⏸️ Pause**: Temporarily pause task execution
- **▶️ Resume**: Continue paused task
- **⏹️ Stop**: Terminate task completely

### 4. Task Completion

When task completes:

1. **Success notification** popup appears
2. Shows completion message and optional results
3. Results displayed in formatted JSON (if available)
4. Auto-close or manual close option

## Styling

### Modern Design Elements

- **Glassmorphism**: Backdrop blur effects on popups
- **Smooth Animations**: 
  - Slide-in for logs (0.3s ease-out)
  - Scale animation for popups (0.3s ease)
  - Fade transitions for status changes
- **Color Palette**:
  - Primary: `#3b82f6` (Blue)
  - Success: `#10b981` (Green)
  - Warning: `#f59e0b` (Amber)
  - Error: `#ef4444` (Red)
  - Background: `#ffffff` (White) / `#1f2937` (Dark)

### Responsive Design

- Adapts to different side panel widths
- Mobile-friendly notification popups
- Flexible layout with CSS Grid and Flexbox

## WebSocket Events

### Incoming Events (from server)

```typescript
socket.on('connect', () => { ... })
socket.on('disconnect', () => { ... })
socket.on('status', (status: TaskStatus) => { ... })
socket.on('log_event', (event: LogEvent) => { ... })
socket.on('task_started', (data) => { ... })
socket.on('error', (data) => { ... })
```

### Outgoing Events (to server)

```typescript
socket.emit('extension_connect')
socket.emit('start_task', { task, cdp_endpoint })
socket.emit('stop_task')
socket.emit('pause_task')
socket.emit('resume_task')
```

## Configuration

### Server URL

Default: `http://localhost:5000`

Can be changed in the side panel settings area (top of panel).

### CDP Endpoint

Automatically detected from current tab or uses extension proxy mode.

## Development

### File Structure

```
src/
├── sidepanel/
│   ├── SidePanel.tsx          # Main side panel component
│   ├── SidePanel.css          # Main styles
│   ├── components/
│   │   ├── ChatInput.tsx      # Chat input component
│   │   ├── ChatInput.css      # Chat input styles
│   │   ├── ExecutionLog.tsx   # Log display component
│   │   ├── ExecutionLog.css   # Log styles
│   │   ├── ControlButtons.tsx # Control buttons
│   │   ├── ControlButtons.css # Control button styles
│   │   ├── TaskStatus.tsx     # Status display
│   │   └── TaskStatus.css     # Status styles
├── notification/
│   ├── Notification.tsx       # Popup notification
│   ├── Notification.css       # Notification styles
│   └── index.tsx             # Notification entry point
└── background/
    └── index.ts              # Background service worker
```

### Building

```bash
cd browser_ai_extension/browse_ai
pnpm install
pnpm build
```

### Loading in Chrome

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `browser_ai_extension/browse_ai/build` folder

## Troubleshooting

### Side Panel Not Opening

- Ensure you're clicking the extension icon (not right-clicking)
- Check that side panel is enabled in manifest.json
- Reload the extension

### Notifications Not Showing

- Check Chrome's notification permissions
- Verify background service worker is running
- Check browser console for errors

### WebSocket Connection Issues

- Ensure server is running on configured port (default: 5000)
- Check firewall settings
- Verify server URL in side panel settings

## Future Enhancements

- [ ] Customizable notification preferences
- [ ] Persistent chat history
- [ ] Export logs functionality
- [ ] Dark mode theme
- [ ] Multi-language support
- [ ] Voice input for tasks
- [ ] Screenshot annotations for user help

## License

MIT License - See LICENSE file for details
