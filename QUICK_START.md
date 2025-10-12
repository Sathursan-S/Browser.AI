# 🚀 Quick Start - Browser.AI Complete Launcher

## TL;DR - Fastest Way to Start

### Windows
```bash
start.bat
```

### macOS/Linux
```bash
chmod +x start.sh
./start.sh
```

### Python (All Platforms)
```bash
python run_project.py
```

---

## What Gets Launched?

✅ Chrome browser in debug mode (port 9222)  
✅ Browser.AI Chrome extension (auto-built)  
✅ Browser.AI server (http://localhost:5000)  
✅ Extension management page (for loading extension)

## All Available Scripts

| Script | Purpose | Platform |
|--------|---------|----------|
| `start.bat` | One-click launcher | Windows |
| `start.sh` | One-click launcher | macOS/Linux |
| `run_project.py` | Full-featured launcher | All |
| `quick_start_examples.py` | Interactive examples | All |

## Common Commands

```bash
# Standard launch (recommended)
python run_project.py

# Development mode (hot reload)
python run_project.py --dev

# Custom port
python run_project.py --port 8080

# Server only (no browser)
python run_project.py --skip-chrome --skip-build

# See all options
python run_project.py --help

# Interactive examples
python quick_start_examples.py
```

## After Launch

1. Chrome will open automatically
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode" (top-right toggle)
4. Click "Load unpacked"
5. Select folder: `browser_ai_extension/browse_ai/build/`
6. Extension is ready! 🎉

## Need Help?

📖 Full documentation: `RUN_PROJECT_GUIDE.md`  
💡 Interactive examples: `python quick_start_examples.py`  
🐛 Issues? Check the terminal output for error messages

## Requirements

- Python 3.11+
- Node.js 14+ (for extension build)
- Google Chrome
- API keys in `.env` file (see `.env.example`)

---

**Ready? Just run `start.bat` (Windows) or `./start.sh` (macOS/Linux)!** 🚀
