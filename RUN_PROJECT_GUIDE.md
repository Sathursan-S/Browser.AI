# Browser.AI Complete Project Launcher Guide

## Overview

`run_project.py` is a comprehensive Python script that automates the complete setup and launch of the Browser.AI project. It handles:

1. ✅ **Chrome Browser Launch** - Starts Chrome in debug mode with remote debugging enabled
2. ✅ **Extension Building** - Builds the Chrome extension (dev or production mode)
3. ✅ **Server Startup** - Launches the Browser.AI Flask server
4. ✅ **Extension Loading** - Provides instructions and opens Chrome extension management

## Quick Start

### Simplest Usage (Recommended)

```bash
python run_project.py
```

This will:
- Find your Chrome installation automatically
- Build the extension in production mode
- Launch Chrome with remote debugging on port 9222
- Start the Browser.AI server on port 5000
- Open the extension management page for you

## Command-Line Options

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dev` | Build extension in development mode | Production mode |
| `--port PORT` | Port for Browser.AI server | 5000 |
| `--debug-port PORT` | Port for Chrome remote debugging | 9222 |
| `--server-debug` | Run Flask server in debug mode | False |

### Skip Options

| Option | Description |
|--------|-------------|
| `--skip-build` | Skip building the extension (use existing build) |
| `--skip-chrome` | Don't launch Chrome browser |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--chrome-path PATH` | Custom path to Chrome executable |

## Usage Examples

### Development Mode

Build extension in dev mode with hot reload:

```bash
python run_project.py --dev
```

### Custom Server Port

Run server on port 8000:

```bash
python run_project.py --port 8000
```

### Server Only Mode

Start only the server (no Chrome, no build):

```bash
python run_project.py --skip-chrome --skip-build
```

### Custom Chrome Path

Specify custom Chrome installation:

```bash
# Windows
python run_project.py --chrome-path "C:\Program Files\Google\Chrome\Application\chrome.exe"

# macOS
python run_project.py --chrome-path "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Linux
python run_project.py --chrome-path "/usr/bin/google-chrome"
```

### Full Debug Mode

Enable all debug features:

```bash
python run_project.py --dev --server-debug
```

### Production Build with Custom Ports

```bash
python run_project.py --port 8080 --debug-port 9223
```

## What Happens When You Run It?

### Step 1: Extension Build

The script will:
- Check if Node.js and pnpm/npm are installed
- Install extension dependencies if needed
- Build the extension using `pnpm build` or `npm run build`
- Output: `browser_ai_extension/browse_ai/build/`

### Step 2: Chrome Launch

The script will:
- Locate your Chrome installation (or use `--chrome-path`)
- Create a custom profile at `~/.browser_ai_chrome_profile`
- Launch Chrome with these flags:
  - `--remote-debugging-port=9222` (or custom port)
  - `--user-data-dir=~/.browser_ai_chrome_profile`
  - `--no-first-run`
  - `--no-default-browser-check`

### Step 3: Server Startup

The script will:
- Check if Flask dependencies are installed
- Install them if missing (`flask`, `flask-socketio`, `eventlet`)
- Start the Flask server on port 5000 (or custom port)
- Server URL: `http://localhost:5000`

### Step 4: Extension Loading Instructions

The script will:
- Display step-by-step instructions to load the extension
- Automatically open `chrome://extensions/` in your browser
- Show the path to the built extension

## Loading the Extension in Chrome

After running the script, follow these steps:

1. **Open Extension Management**
   - The script will automatically open `chrome://extensions/`
   - Or manually navigate to it in Chrome

2. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top-right corner

3. **Load Unpacked Extension**
   - Click "Load unpacked" button
   - Navigate to: `browser_ai_extension/browse_ai/build/`
   - Select the folder and click "Open"

4. **Verify Extension**
   - The "Browse.AI" extension should appear in your extensions list
   - Click the extension icon in the Chrome toolbar to use it

## Stopping the Services

Press `Ctrl+C` in the terminal where you ran the script. This will:
- Terminate the Flask server
- Close the Chrome browser
- Clean up all background processes

## Troubleshooting

### Chrome Not Found

**Problem**: Script can't find Chrome executable

**Solution**:
```bash
python run_project.py --chrome-path "YOUR_CHROME_PATH"
```

### Node.js Not Installed

**Problem**: Extension build fails with "Node.js not found"

**Solution**: Install Node.js from https://nodejs.org/

### Port Already in Use

**Problem**: Server fails to start - port 5000 already in use

**Solution**: Use a different port
```bash
python run_project.py --port 8000
```

### Extension Build Fails

**Problem**: Build command fails

**Solution**: Install dependencies manually
```bash
cd browser_ai_extension/browse_ai
pnpm install  # or npm install
pnpm build    # or npm run build
```

### Flask Dependencies Missing

**Problem**: Server fails to start - Flask not found

**Solution**: The script auto-installs them, but you can manually install:
```bash
pip install flask flask-socketio eventlet
```

## Project Structure

```
Browser.AI/
├── run_project.py              # ← This launcher script
├── browser_ai/                 # Core Python library
├── browser_ai_gui/            # Flask web application
│   └── main.py                # Server entry point
├── browser_ai_extension/      # Chrome extension
│   └── browse_ai/
│       ├── src/               # TypeScript/React source
│       ├── build/             # Built extension (generated)
│       └── package.json       # Extension dependencies
└── .env                       # Environment variables (API keys)
```

## Environment Setup

### Required Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI API Key (required for LLM)
OPENAI_API_KEY=sk-...

# Optional: Other LLM providers
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

### Python Dependencies

The core Browser.AI dependencies are in `pyproject.toml`:

```bash
pip install -e .              # Install core dependencies
pip install -e ".[gui]"       # Install with GUI dependencies
pip install -e ".[dev]"       # Install with dev dependencies
```

## Advanced Configuration

### Custom Chrome Profile

By default, the script uses `~/.browser_ai_chrome_profile`. To use a different profile:

1. Modify the `launch_chrome_debug_mode()` function in `run_project.py`
2. Change the `user_data_dir` parameter

### Custom Extension Path

To load a different extension build:

1. Modify the `extension_path` variable in `main()`
2. Update the path to point to your custom build

### Server Configuration

The server can be configured via `browser_ai_gui/config.py`:

```python
# Default configuration
DEFAULT_CONFIG = {
    'llm_provider': 'openai',
    'model_name': 'gpt-4',
    'temperature': 0.0,
    # ... more options
}
```

## Integration with VS Code

### Recommended Launch Configuration

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Browser.AI: Full Stack",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/run_project.py",
      "args": ["--dev"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Browser.AI: Server Only",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/run_project.py",
      "args": ["--skip-chrome", "--server-debug"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Recommended Tasks

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Browser.AI",
      "type": "shell",
      "command": "python",
      "args": ["run_project.py"],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Build Extension",
      "type": "shell",
      "command": "pnpm",
      "args": ["build"],
      "options": {
        "cwd": "${workspaceFolder}/browser_ai_extension/browse_ai"
      },
      "problemMatcher": []
    }
  ]
}
```

## Tips & Best Practices

1. **Development Workflow**
   ```bash
   # Start development
   python run_project.py --dev
   
   # Extension auto-rebuilds on changes
   # Server stays running
   # Reload extension in Chrome to see changes
   ```

2. **Production Testing**
   ```bash
   # Build production version
   python run_project.py
   
   # Test with production build
   # No hot reload
   ```

3. **Server-Only Development**
   ```bash
   # When working only on server code
   python run_project.py --skip-chrome --skip-build --server-debug
   ```

4. **Extension-Only Development**
   ```bash
   # When working only on extension
   cd browser_ai_extension/browse_ai
   pnpm dev
   
   # Load extension manually in Chrome
   ```

## Next Steps

After running the script:

1. **Test the Extension**
   - Click the Browser.AI icon in Chrome
   - Open the side panel
   - Try a simple task

2. **Check Server Logs**
   - Monitor the terminal for server output
   - Check for any errors or warnings

3. **Configure API Keys**
   - Ensure `.env` has your API keys
   - Test LLM connectivity

4. **Read the Docs**
   - Check `docs/` folder for detailed documentation
   - Review `GUI_README.md` for GUI-specific info

## Support

For issues or questions:
- Check the main `README.md`
- Review documentation in `docs/`
- Check existing GitHub issues
- Create a new issue with detailed logs

---

**Happy Automating! 🤖✨**
