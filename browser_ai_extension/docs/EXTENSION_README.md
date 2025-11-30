# Browser.AI Chrome Extension

A Chrome extension that provides a side panel UI for controlling Browser.AI automation tasks directly from your browser.

## Features

- **Side Panel Chat Interface**: Describe tasks in natural language
- **Live Log Streaming**: See real-time progress with animated step indicators
- **CDP Integration**: Control the current browser context using Chrome DevTools Protocol
- **WebSocket Communication**: Connect to Browser.AI Python server for agent execution
- **Visual Feedback**: Color-coded logs with icons for different event types
- **Task Control**: Start, pause, resume, and stop automation tasks

## Prerequisites

1. **Chrome Browser** with developer mode enabled
2. **Browser.AI Python Server** running (see setup instructions below)
3. **Chrome Remote Debugging** enabled (optional, for advanced usage)

## Installation

### 1. Install Dependencies

```bash
cd browser_ai_extension/browse_ai
npm install
```

### 2. Build the Extension

```bash
npm run build
```

This will create a `dist` folder with the compiled extension.

### 3. Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in the top-right corner)
3. Click "Load unpacked"
4. Select the `browser_ai_extension/browse_ai/dist` folder
5. The Browser.AI extension should now appear in your extensions list

## Setting Up the Python Server

### 1. Start the Browser.AI Web Server

```bash
# From the main Browser.AI directory
python -m browser_ai_gui.main web --port 5000
```

Or use the GUI launcher:

```bash
python launch.py
```

### 2. Configure API Keys

Make sure you have your LLM API keys configured. Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
# Or use other supported providers:
# ANTHROPIC_API_KEY=your_anthropic_key
# GOOGLE_API_KEY=your_google_key
```

### 3. Verify Server Connection

1. Open the extension side panel (click the extension icon or use the side panel)
2. Check that the connection status shows "Connected" (green indicator)
3. If not connected, verify the server URL (default: `http://localhost:5000`)

## Usage

### Basic Task Execution

1. **Open the Side Panel**: Click the Browser.AI extension icon in your toolbar
2. **Enter a Task**: Type what you want to automate in the chat input, for example:
   - "Search for Python tutorials on Google and summarize the top 5 results"
   - "Fill out this form with my information"
   - "Navigate to GitHub and find the most starred Python projects"
3. **Start the Task**: Click "Start Task" or press `Ctrl+Enter`
4. **Monitor Progress**: Watch the live logs section for real-time updates
5. **Control Execution**: Use Pause/Resume/Stop buttons as needed

### Understanding the UI

#### Connection Status
- **Green indicator**: Connected to Python server
- **Red indicator**: Disconnected from server

#### Log Events
- 🚀 **Agent Start**: Task execution has begun
- 📍 **Agent Step**: Agent is processing a step
- ⚡ **Agent Action**: Agent performed an action (click, type, etc.)
- ✨ **Agent Result**: Result extracted from page
- ✅ **Agent Complete**: Task completed successfully
- ❌ **Agent Error**: An error occurred
- ⏸️ **Agent Pause**: Task paused
- ▶️ **Agent Resume**: Task resumed
- ⏹️ **Agent Stop**: Task stopped

#### Log Levels
- **INFO** (blue): Informational messages
- **WARNING** (orange): Warnings that don't stop execution
- **ERROR** (red): Errors that occurred
- **RESULT** (green): Successful results and extractions

### Advanced: Using CDP for Current Browser Control

The extension can control your current browser tab using Chrome DevTools Protocol:

1. **Start Chrome with Remote Debugging** (optional for enhanced control):
   ```bash
   # macOS
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   
   # Linux
   google-chrome --remote-debugging-port=9222
   
   # Windows
   chrome.exe --remote-debugging-port=9222
   ```

2. The extension will automatically detect and use the CDP endpoint when available

## Development

### Development Mode

```bash
npm run dev
```

This starts a development server with hot reloading.

### Building for Production

```bash
npm run build
```

### Creating Distribution Package

```bash
npm run zip
```

This creates a zip file ready for Chrome Web Store submission.

## Configuration

### Server URL

The default server URL is `http://localhost:5000`. You can change this in the side panel's configuration section.

### Reconnection

The extension automatically attempts to reconnect to the server if the connection is lost, with exponential backoff.

## Troubleshooting

### "Disconnected" Status

**Problem**: Extension shows "Disconnected" status

**Solutions**:
1. Verify the Python server is running: `http://localhost:5000`
2. Check that the server URL in the extension matches your server
3. Look for CORS errors in the browser console
4. Restart the Python server and refresh the extension

### CDP Endpoint Not Found

**Problem**: "CDP endpoint not found" error

**Solutions**:
1. Start Chrome with `--remote-debugging-port=9222`
2. Check if another process is using port 9222
3. Try using the extension without CDP (basic automation still works)

### Extension Not Loading

**Problem**: Extension fails to load in Chrome

**Solutions**:
1. Make sure you built the extension: `npm run build`
2. Verify you're loading the `dist` folder, not the source folder
3. Check the Chrome console for error messages
4. Try disabling and re-enabling developer mode

### Task Not Starting

**Problem**: Clicking "Start Task" doesn't start the task

**Solutions**:
1. Check that the connection status is "Connected"
2. Verify your LLM API keys are configured in the Python server
3. Look for errors in the logs section
4. Check the browser console for WebSocket errors

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
│                                                              │
│  ┌────────────────┐          ┌─────────────────────┐       │
│  │  Side Panel UI │◄────────►│ Background Worker  │       │
│  │   (React)      │          │   (CDP Handler)    │       │
│  └────────┬───────┘          └──────────┬──────────┘       │
│           │                              │                  │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            │ WebSocket                    │ CDP/Debugger API
            │ (socket.io)                  │
            ▼                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  Browser.AI Python Server                     │
│                                                               │
│  ┌─────────────────┐      ┌──────────────────────────────┐  │
│  │ WebSocket Server│      │  Agent Controller            │  │
│  │  (Flask-SocketIO)│◄────►│  (Browser.AI Agent)         │  │
│  └─────────────────┘      └──────────────┬───────────────┘  │
│                                           │                   │
│                                           ▼                   │
│                           ┌──────────────────────────────┐  │
│                           │   Browser Context (CDP)      │  │
│                           │   (Playwright + CDP)         │  │
│                           └──────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Components

1. **Side Panel UI** (React): User interface for task input and log display
2. **Background Worker**: Handles CDP connections and message routing
3. **WebSocket Server** (Python): Manages extension connections and task execution
4. **Agent Controller**: Executes Browser.AI tasks using CDP-connected browser
5. **Browser Context**: The actual browser being controlled via CDP

## API Reference

### WebSocket Events (Extension → Server)

- `extension_connect`: Initialize connection and get status
- `start_task`: Start a new automation task
  ```javascript
  { task: string, cdp_endpoint: string }
  ```
- `stop_task`: Stop the current task
- `pause_task`: Pause the current task
- `resume_task`: Resume the paused task
- `get_status`: Request current status

### WebSocket Events (Server → Extension)

- `status`: Current task status
  ```javascript
  { is_running: boolean, current_task: string | null, has_agent: boolean }
  ```
- `log_event`: Log event from agent execution
  ```javascript
  { timestamp: string, level: string, message: string, event_type: string }
  ```
- `task_started`: Confirmation that task has started
- `task_action_result`: Result of a task action (stop/pause/resume)
- `error`: Error message from server

## License

This extension is part of the Browser.AI project and follows the same license.

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.

## Support

For issues and questions:
- GitHub Issues: [Browser.AI Issues](https://github.com/Sathursan-S/Browser.AI/issues)
- Documentation: See main Browser.AI README
