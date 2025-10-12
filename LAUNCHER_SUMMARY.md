# Browser.AI Complete Project Launcher - Summary

## 📦 What Was Created

### Main Launcher Script
**File:** `run_project.py`

A comprehensive Python script that automates the entire Browser.AI development workflow:

#### Features:
- ✅ **Chrome Debug Mode Launch** - Starts Chrome with remote debugging on port 9222
- ✅ **Extension Building** - Automatically builds the Chrome extension (dev or production)
- ✅ **Server Management** - Starts the Flask/SocketIO server on port 5000
- ✅ **Dependency Handling** - Auto-installs missing dependencies
- ✅ **Cross-Platform** - Works on Windows, macOS, and Linux
- ✅ **Flexible Configuration** - Extensive command-line options
- ✅ **Process Management** - Clean shutdown with Ctrl+C
- ✅ **Colored Output** - Beautiful terminal output with status indicators

### Quick Launch Scripts

#### Windows: `start.bat`
```batch
start.bat
```
Simple batch file for one-click launching on Windows.

#### Unix/Linux/macOS: `start.sh`
```bash
chmod +x start.sh
./start.sh
```
Bash script for one-click launching on Unix-based systems.

### Documentation

#### Comprehensive Guide: `RUN_PROJECT_GUIDE.md`
- Complete usage instructions
- Detailed examples for every scenario
- Troubleshooting section
- Integration with VS Code
- Tips and best practices

#### Quick Reference: `QUICK_START.md`
- TL;DR for getting started
- Common commands table
- Quick reference for all scripts

#### Interactive Examples: `quick_start_examples.py`
```python
python quick_start_examples.py
```
Interactive menu showing common usage patterns.

## 🚀 Quick Start

### Simplest Usage
```bash
python run_project.py
```

This single command will:
1. Build the Chrome extension
2. Launch Chrome in debug mode
3. Start the Browser.AI server
4. Open extension management for easy loading

### Development Mode
```bash
python run_project.py --dev
```

Enables hot reload for the extension - changes rebuild automatically.

### All Options
```bash
python run_project.py --help
```

## 📋 Command-Line Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--dev` | Build extension in dev mode (hot reload) | Production |
| `--port PORT` | Server port | 5000 |
| `--debug-port PORT` | Chrome debug port | 9222 |
| `--skip-build` | Skip building extension | Build |
| `--skip-chrome` | Don't launch Chrome | Launch |
| `--chrome-path PATH` | Custom Chrome executable path | Auto-detect |
| `--server-debug` | Run server in debug mode | Production |

## 🎯 Common Use Cases

### 1. Full Stack Development
```bash
python run_project.py --dev
```
- Extension rebuilds on changes
- Server running
- Chrome launched

### 2. Backend Only
```bash
python run_project.py --skip-chrome --skip-build --server-debug
```
- Only server running
- Debug mode enabled
- No Chrome or build

### 3. Extension Only
```bash
cd browser_ai_extension/browse_ai
pnpm dev
```
- Extension dev server
- Hot reload
- Load manually in Chrome

### 4. Production Testing
```bash
python run_project.py
```
- Production build
- Full stack running
- Ready for testing

### 5. Custom Configuration
```bash
python run_project.py --port 8080 --debug-port 9223 --chrome-path "C:\Custom\Chrome\chrome.exe"
```
- Custom ports
- Custom Chrome location
- Full control

## 🔧 How It Works

### Step-by-Step Process

1. **Extension Build**
   - Detects pnpm or npm
   - Installs dependencies if needed
   - Runs build command
   - Creates `browser_ai_extension/browse_ai/build/`

2. **Chrome Launch**
   - Finds Chrome executable (or uses custom path)
   - Creates profile at `~/.browser_ai_chrome_profile`
   - Launches with flags:
     - `--remote-debugging-port=9222`
     - `--user-data-dir=<profile>`
   - Returns process handle for cleanup

3. **Server Start**
   - Checks for Flask/SocketIO
   - Installs if missing
   - Runs: `python -m browser_ai_gui.main web --port 5000`
   - Monitors output in terminal

4. **Extension Loading Helper**
   - Shows step-by-step instructions
   - Opens `chrome://extensions/`
   - Displays extension path

5. **Graceful Shutdown**
   - Catches Ctrl+C
   - Terminates all processes
   - Cleans up resources

## 📁 Project Structure

```
Browser.AI/
├── run_project.py              # Main launcher script ⭐
├── start.bat                   # Windows quick start
├── start.sh                    # Unix quick start
├── quick_start_examples.py     # Interactive examples
├── RUN_PROJECT_GUIDE.md        # Full documentation
├── QUICK_START.md              # Quick reference
│
├── browser_ai/                 # Core library
├── browser_ai_gui/            # Flask server
│   └── main.py                # Server entry point
│
├── browser_ai_extension/      # Chrome extension
│   └── browse_ai/
│       ├── src/               # TypeScript source
│       ├── build/             # Built extension
│       └── package.json
│
└── .env                       # API keys (create from .env.example)
```

## 🎨 Terminal Output Features

The script provides beautiful, colored terminal output:

- 🟢 **Green** - Success messages
- 🔵 **Blue** - Information messages
- 🟡 **Yellow** - Warnings
- 🔴 **Red** - Errors
- 🟣 **Purple** - Headers and sections

Example output:
```
============================================================
              Launching Chrome in Debug Mode
============================================================

ℹ Chrome path: C:\Program Files\Google\Chrome\Application\chrome.exe
ℹ Debug port: 9222
ℹ User data dir: C:\Users\...\browser_ai_chrome_profile
✓ Chrome launched successfully (PID: 12345)
ℹ Remote debugging available at: http://localhost:9222
```

## 🛠️ Advanced Features

### Process Management
- Tracks all spawned processes
- Clean termination on Ctrl+C
- Handles orphaned processes
- Timeout protection

### Dependency Auto-Install
- Detects missing Node.js/npm/pnpm
- Auto-installs Flask dependencies
- Verifies Python packages
- Helpful error messages

### Cross-Platform Support
- Auto-detects Chrome on all platforms
- Platform-specific process handling
- Correct shell commands for each OS
- UTF-8 support for output

### Error Handling
- Graceful failure messages
- Detailed troubleshooting hints
- Non-zero exit codes
- Logs preserved in terminal

## 🔍 Troubleshooting

### Chrome Not Found
**Solution:** Use `--chrome-path` flag
```bash
python run_project.py --chrome-path "C:\Your\Path\To\chrome.exe"
```

### Port Already in Use
**Solution:** Use custom ports
```bash
python run_project.py --port 8080 --debug-port 9223
```

### Extension Build Fails
**Solution:** Install Node.js from https://nodejs.org/

### Server Won't Start
**Solution:** Check if dependencies are installed
```bash
pip install flask flask-socketio eventlet
```

## 📚 Related Documentation

- **Main README** - `README.md`
- **GUI Documentation** - `GUI_README.md`
- **Architecture Docs** - `docs/architecture-overview.md`
- **API Documentation** - `docs/` folder

## 🎓 Learning Path

1. **First Time?** Run `python quick_start_examples.py`
2. **Quick Start?** Read `QUICK_START.md`
3. **Full Guide?** Read `RUN_PROJECT_GUIDE.md`
4. **Customization?** Edit `run_project.py`

## ✨ Benefits

### Before (Multiple Commands)
```bash
# Terminal 1
cd browser_ai_extension/browse_ai
pnpm install
pnpm build

# Terminal 2
python -m browser_ai_gui.main web --port 5000

# Terminal 3
chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome_dev

# Manually load extension in chrome://extensions/
```

### After (Single Command)
```bash
python run_project.py
```

**Everything handled automatically!** 🎉

## 🤝 Contributing

When contributing to Browser.AI:

1. Use `python run_project.py --dev` for development
2. Test with `python run_project.py` before committing
3. Update documentation if adding features
4. Ensure cross-platform compatibility

## 📝 License

Same as Browser.AI project license.

---

## Quick Command Cheatsheet

```bash
# Standard launch
python run_project.py

# Development mode
python run_project.py --dev

# Server only
python run_project.py --skip-chrome --skip-build

# Custom everything
python run_project.py --dev --port 8080 --debug-port 9223 --server-debug

# Windows one-click
start.bat

# Unix one-click
./start.sh

# See all options
python run_project.py --help

# Interactive guide
python quick_start_examples.py
```

---

**Made with ❤️ for Browser.AI developers**

*Last updated: 2025-10-12*
