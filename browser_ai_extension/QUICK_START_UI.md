# Browser.AI Chrome Extension - Quick Start Guide

## 🚀 What's New

The Browser.AI Chrome Extension now features a **modern, GitHub Copilot-inspired UI** with intelligent notifications and real-time task tracking!

## ✨ Key Features

### 1. **Auto-Open Side Panel**
- Click the Browser.AI extension icon
- Side panel opens automatically (no popup needed!)
- Clean, modern interface loads instantly

### 2. **Smart Notifications**
Popup windows automatically appear for:
- ⚠️ **User Interaction Needed**: When AI needs human help
- ✅ **Task Completed**: When automation finishes
- ❌ **Errors**: When something goes wrong

### 3. **Modern UI Components**
- **Chat Input**: Type tasks at the bottom, just like GitHub Copilot
- **Execution Logs**: Real-time, animated log entries with color coding
- **Control Buttons**: Stop ⏹️, Pause ⏸️, Resume ▶️ your tasks
- **Status Display**: See connection and task status at a glance

## 📦 Installation

### 1. Build the Extension

```bash
cd browser_ai_extension/browse_ai
pnpm install
pnpm build
```

### 2. Load in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select: `browser_ai_extension/browse_ai/build`

### 3. Pin the Extension

1. Click the puzzle piece icon in Chrome toolbar
2. Find "browse_ai" 
3. Click the pin icon to keep it visible

## 🎯 Usage

### Starting a Task

1. **Click the extension icon** → Side panel opens
2. **Type your task** in the chat input (e.g., "Search for Python tutorials")
3. **Press Enter** or click Send
4. Watch real-time execution logs appear!

### Handling User Interactions

When a notification popup appears:

1. **Read the message** to understand what's needed
2. **Complete the action** in the browser (e.g., solve CAPTCHA)
3. **AI auto-detects** completion and continues
4. Or click **"Open Side Panel"** for more details

### Controlling Tasks

Use the control buttons:

- **⏸️ Pause**: Temporarily pause execution
- **▶️ Resume**: Continue paused task
- **⏹️ Stop**: Terminate task completely

## 🔧 Configuration

### Server URL
Default: `http://localhost:5000`

Change it in the side panel if your server runs on a different port.

### Starting the Server

```bash
# From Browser.AI root directory
uv run browser_ai_gui/main.py web --port 5000
```

The extension will connect to `/extension` namespace automatically.

## 📱 UI Components

### Chat Input (Bottom)
- Modern text input with auto-expand
- Send button with icon
- Disabled when disconnected or running

### Execution Logs (Middle)
- Animated slide-in entries
- Color-coded by severity:
  - 🔵 INFO (blue)
  - 🟡 WARNING (yellow)
  - 🔴 ERROR (red)
  - 🟣 DEBUG (purple)
- Auto-scroll to latest

### Control Buttons (Top)
- Visual feedback on hover
- Smart enable/disable based on status
- Clear icons for each action

### Status Display (Top)
- Connection indicator (🟢 Connected / 🔴 Disconnected)
- Current task name
- Running/Paused badge

## 🔔 Notification System

### When Do Popups Appear?

**User Interaction Required**
- CAPTCHA needs solving
- Login required
- Manual action needed
- Shows current page URL

**Task Completed**
- Automation finished successfully
- Optional: Shows extracted results
- Formatted JSON display

**Error Occurred**
- Critical error happened
- Error details included
- Timestamp for tracking

### Notification Actions

All notifications have:
- **Timestamp**: When it occurred
- **Close Button**: Dismiss notification
- **Message**: What happened
- **Details**: Additional context (optional)

User interaction notifications also have:
- **Open Side Panel**: Quick access to view logs

## 🎨 Visual Design

### Colors
- **Primary**: Blue (#3b82f6) - Actions, links
- **Success**: Green (#10b981) - Completed tasks
- **Warning**: Amber (#f59e0b) - User attention needed
- **Error**: Red (#ef4444) - Errors, failures

### Animations
- **Logs**: Slide-in from bottom (300ms)
- **Popups**: Scale + fade (300ms)
- **Buttons**: Hover lift effect
- **Status**: Smooth color transitions

### Effects
- **Glassmorphism**: Blurred backgrounds
- **Shadows**: Depth and elevation
- **Borders**: Rounded corners (8-16px)
- **Gradients**: Subtle background transitions

## 🐛 Troubleshooting

### Side Panel Won't Open
- Make sure you **click** the icon (not right-click)
- Reload the extension from `chrome://extensions`
- Check that side panel is enabled in manifest

### WebSocket Won't Connect
- Verify server is running: `http://localhost:5000`
- Check server URL in side panel settings
- Look for errors in browser console (F12)

### Notifications Not Appearing
- Check Chrome notification permissions
- Verify background service worker is active
- Reload the extension

### Build Errors
```bash
# Clean install
rm -rf node_modules
pnpm install
pnpm build
```

## 📚 Next Steps

1. **Start the server**: `uv run browser_ai_gui/main.py web --port 5000`
2. **Load the extension** in Chrome
3. **Click the icon** to open side panel
4. **Try a simple task**: "Open Google"
5. **Watch the magic happen!** ✨

## 📖 Documentation

- **Full UI Features Guide**: `UI_FEATURES.md`
- **CDP WebSocket Guide**: `CDP_WEBSOCKET_README.md`
- **Extension README**: `EXTENSION_README.md`

## 💡 Tips

- Use **Shift+Enter** in chat input for multi-line tasks
- **Pin the extension** for quick access
- Notifications **auto-close** after clicking buttons
- **Resume** works even if you close the notification
- Check **side panel logs** for detailed execution steps

---

**Enjoy the new modern Browser.AI experience!** 🎉
