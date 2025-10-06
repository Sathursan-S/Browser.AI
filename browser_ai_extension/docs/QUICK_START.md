# Browser.AI Chrome Extension - Quick Start Guide

## Installation & Setup

### Step 1: Build the Extension

```bash
cd browser_ai_extension/browse_ai
npm install
npm run build
```

The extension will be built to the `build/` directory.

### Step 2: Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Navigate to and select: `browser_ai_extension/browse_ai/build/`

### Step 3: Start the Python Server

```bash
# From the root Browser.AI directory
python -m browser_ai_gui.main web --port 5000
```

Or use the launcher:

```bash
python launch.py
# Then select "Web GUI"
```

### Step 4: Configure API Key

Create a `.env` file in the root directory with your API key:

```env
# For OpenAI
OPENAI_API_KEY=your_key_here

# Or for other providers
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

## Usage

### Opening the Side Panel

1. Click the Browser.AI extension icon in your toolbar
2. Or right-click and select "Open side panel"

### Using the Chat Interface

1. **Check Connection**: Verify the green "Connected" indicator at the top
2. **Enter Task**: Type your automation task in the text area
3. **Start Task**: Click "Start Task" or press `Ctrl+Enter`
4. **Monitor Progress**: Watch the live logs section for updates
5. **Control Execution**: Use Pause/Resume/Stop buttons as needed

### Example Tasks

```
Search for Python tutorials on Google and summarize the top 5 results
```

```
Navigate to GitHub, find the most starred Python projects this week
```

```
Fill out this contact form with name: John Doe, email: john@example.com
```

## Features

### Live Log Streaming
- Real-time updates as the agent executes steps
- Color-coded log levels (INFO, WARNING, ERROR, RESULT)
- Animated step indicators
- Auto-scrolling to latest log

### Task Control
- **Start**: Begin a new automation task
- **Pause**: Temporarily pause execution
- **Resume**: Continue from where you left off
- **Stop**: Terminate the current task

### Event Icons
- 🚀 Task started
- 📍 Processing step
- ⚡ Action performed
- ✨ Result extracted
- ✅ Task completed
- ❌ Error occurred
- ⏸️ Task paused
- ▶️ Task resumed
- ⏹️ Task stopped

## Architecture

```
Chrome Extension (Side Panel)
    ↕ WebSocket (socket.io)
Python Server (Flask + SocketIO)
    ↕ CDP/Playwright
Browser Context (Current Tab)
```

## Troubleshooting

### Connection Issues

**Problem**: Shows "Disconnected"

**Solution**:
- Verify Python server is running on port 5000
- Check console for CORS errors
- Restart the server and refresh the extension

### API Key Errors

**Problem**: "No API key configured"

**Solution**:
- Create `.env` file with your API key
- Restart the Python server
- Verify the key is correct

### Task Not Starting

**Problem**: Task doesn't execute

**Solution**:
- Ensure you're connected (green indicator)
- Check that API key is configured
- Look for errors in the logs section
- Check browser console for JavaScript errors

## Advanced Features

### CDP Integration

The extension can control your current browser tab using Chrome DevTools Protocol:

1. The extension automatically attempts to use CDP for the active tab
2. This provides more reliable control over the browser
3. Falls back to standard Playwright if CDP is unavailable

### Server Configuration

You can change the server URL in the side panel if running on a different port or host:

1. Enter the new URL in the configuration section
2. The extension will attempt to reconnect automatically

## Development

### Hot Reload

```bash
npm run dev
```

This starts a development server with automatic reloading.

### Building for Production

```bash
npm run build
```

### Debugging

1. Open Chrome DevTools for the side panel:
   - Right-click in the side panel → "Inspect"
2. Check the Console tab for errors
3. Use the Network tab to monitor WebSocket connection

## Security Notes

- The extension requires debugger permission for CDP functionality
- Host permissions are needed to inject content scripts
- All communication with the server uses WebSocket (ensure HTTPS in production)

## Next Steps

- Configure LLM settings in the Python server
- Try different automation tasks
- Monitor resource usage
- Report issues on GitHub

For more details, see the main README and documentation.
