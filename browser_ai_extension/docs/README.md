# Browser.AI Chrome Extension

> Modern side panel extension for browser automation with live logs and chat interface

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

The Browser.AI Chrome Extension provides a seamless way to control browser automation directly from your browser's side panel. It features a modern chat interface with real-time log streaming and connects to the Browser.AI Python server via WebSocket.

**Key Benefits:**
- 🎨 Beautiful, modern UI with animations
- 📊 Real-time log streaming with color-coded levels
- 🔌 WebSocket connection for instant updates
- 🎯 CDP integration for precise browser control
- 🔄 Full task control (start, pause, resume, stop)

## ✨ Features

### Chat Interface
- Natural language task input
- Keyboard shortcuts (Ctrl+Enter to start)
- Auto-complete suggestions (future)
- Task history (future)

### Live Log Streaming
- Real-time updates as agent executes
- Color-coded log levels (INFO, WARNING, ERROR, RESULT)
- Event-specific icons (🚀 start, 📍 step, ⚡ action, ✅ complete)
- Auto-scrolling with smooth animations
- Clear logs functionality

### Task Control
- **Start**: Begin automation task
- **Pause**: Temporarily halt execution
- **Resume**: Continue from pause point
- **Stop**: Terminate current task

### Connection Management
- Visual connection indicator
- Automatic reconnection with backoff
- Configurable server URL
- Connection status in header

### Browser Integration
- CDP (Chrome DevTools Protocol) support
- Current tab control
- Debugger attachment handling
- Tab lifecycle management

## 🚀 Quick Start

### Prerequisites

- Node.js >= 14.18.0
- Chrome 88+ or Edge 88+
- Python 3.11+
- Browser.AI Python package

### Installation

**1. Clone and Build**
```bash
cd browser_ai_extension/browse_ai
npm install
npm run build
```

**2. Load Extension**
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `browser_ai_extension/browse_ai/build/`

**3. Start Server**
```bash
# From repository root
python -m browser_ai_gui.main web --port 5000
```

**4. Configure API**
Create `.env` in repository root:
```env
OPENAI_API_KEY=your_key_here
```

**5. Open Side Panel**
- Click Browser.AI icon in toolbar
- Or right-click → "Open side panel"

### First Task

1. Check connection status (should be green)
2. Type: "Search for Python tutorials on Google"
3. Click "Start Task" or press Ctrl+Enter
4. Watch live logs as automation runs
5. Task completes with ✅ icon

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Step-by-step setup guide
- **[EXTENSION_README.md](EXTENSION_README.md)** - Complete documentation
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[UI_GUIDE.md](UI_GUIDE.md)** - UI components and design

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Chrome Extension Layer                       │
│                                                           │
│  ┌─────────────────┐      ┌────────────────────────┐    │
│  │  Side Panel UI  │      │  Background Worker     │    │
│  │    (React)      │◄────►│  (Service Worker)      │    │
│  └────────┬────────┘      └──────────┬─────────────┘    │
│           │                           │                   │
└───────────┼───────────────────────────┼───────────────────┘
            │                           │
            │ WebSocket                 │ CDP API
            │ (socket.io)               │ (Debugger)
            ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│              Browser.AI Server Layer                      │
│                                                           │
│  ┌──────────────────┐     ┌─────────────────────────┐   │
│  │ WebSocket Server │     │  Extension Handler      │   │
│  │ (Flask-SocketIO) │◄───►│  (Task Manager)         │   │
│  └──────────────────┘     └───────────┬─────────────┘   │
│                                        │                  │
│                                        ▼                  │
│                        ┌───────────────────────────┐     │
│                        │  Browser.AI Agent         │     │
│                        │  (CDP-connected)          │     │
│                        └───────────┬───────────────┘     │
│                                    │                      │
└────────────────────────────────────┼──────────────────────┘
                                     │
                                     ▼
                        ┌───────────────────────────┐
                        │  Browser Context          │
                        │  (Current Tab via CDP)    │
                        └───────────────────────────┘
```

### Components

1. **Side Panel UI** (`src/sidepanel/`)
   - React-based chat interface
   - WebSocket client (socket.io)
   - Real-time log display
   - Task controls

2. **Background Worker** (`src/background/`)
   - Service worker for message handling
   - CDP connection management
   - Debugger lifecycle handling

3. **WebSocket Server** (`browser_ai_gui/websocket_server.py`)
   - Flask-SocketIO server
   - Extension client management
   - Event broadcasting

4. **Extension Handler**
   - Task execution with CDP
   - Browser.AI agent integration
   - Status management

## 🛠️ Development

### Development Mode

```bash
npm run dev
```

Starts development server with hot reload at `http://localhost:5173`

### Building

```bash
npm run build
```

Output: `build/` directory

### Linting

```bash
npm run fmt
```

Formats code with Prettier

### Creating Distribution

```bash
npm run zip
```

Creates `browse_ai.zip` for Chrome Web Store

### File Structure

```
browse_ai/
├── src/
│   ├── sidepanel/
│   │   ├── SidePanel.tsx       # Main UI component
│   │   ├── SidePanel.css       # Styling
│   │   ├── index.tsx           # Entry point
│   │   └── index.css           # Global styles
│   ├── background/
│   │   └── index.ts            # Service worker
│   ├── contentScript/          # Content scripts
│   ├── popup/                  # Extension popup
│   ├── options/                # Options page
│   ├── devtools/               # DevTools integration
│   └── manifest.ts             # Extension manifest
├── public/
│   └── img/                    # Icons and images
├── build/                      # Compiled output
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
└── vite.config.ts              # Vite config
```

### Technology Stack

**Frontend:**
- React 18.2
- TypeScript 5.2
- Socket.IO Client 4.7
- Vite 5.4
- CRXJS Vite Plugin 2.0

**Backend:**
- Flask 3.1
- Flask-SocketIO 5.5
- Python-SocketIO 5.14
- Eventlet 0.40

### Adding New Features

1. **New UI Component**
   ```typescript
   // src/sidepanel/components/NewFeature.tsx
   export const NewFeature = () => {
     return <div>New Feature</div>
   }
   ```

2. **New WebSocket Event**
   ```python
   # browser_ai_gui/websocket_server.py
   @self.socketio.on('new_event', namespace='/extension')
   def handle_new_event(data):
       # Handle event
       emit('response', {'success': True})
   ```

3. **New Background Task**
   ```typescript
   // src/background/index.ts
   chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
     if (request.type === 'NEW_TASK') {
       // Handle task
     }
   })
   ```

## 🐛 Troubleshooting

### Common Issues

**1. Extension Not Loading**
- Verify build folder exists: `ls -la build/`
- Check manifest.json is present
- Look for errors in chrome://extensions/
- Try rebuilding: `npm run build`

**2. WebSocket Not Connecting**
- Verify server is running: `http://localhost:5000`
- Check server URL in extension matches
- Look for CORS errors in console
- Test server: `curl http://localhost:5000`

**3. Tasks Not Starting**
- Verify API key is configured
- Check connection status is green
- Look for errors in logs section
- Check Python server console for errors

**4. Build Errors**
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

**5. TypeScript Errors**
- Most @ts-ignore comments are intentional
- Update @crxjs/vite-plugin if issues persist
- Check TypeScript version compatibility

### Debug Mode

**Extension Console:**
1. Right-click side panel → "Inspect"
2. Console tab shows JS errors
3. Network tab shows WebSocket traffic

**Python Server:**
```bash
# Enable debug logging
export FLASK_ENV=development
python -m browser_ai_gui.main web --port 5000
```

**Testing WebSocket:**
```bash
python test_extension_server.py
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Make changes and test
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing`
6. Open Pull Request

### Development Guidelines

- Follow existing code style
- Add TypeScript types
- Update documentation
- Test thoroughly
- Keep commits atomic

## 📝 License

Same as Browser.AI project license.

## 🙏 Acknowledgments

- Browser.AI core team
- CRXJS for excellent Vite plugin
- Socket.IO for reliable WebSocket
- React community for great tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Sathursan-S/Browser.AI/issues)
- **Discussions**: GitHub Discussions
- **Documentation**: This repository

## 🗺️ Roadmap

- [ ] Dark mode support
- [ ] Task history
- [ ] Export logs
- [ ] Multiple server profiles
- [ ] Keyboard shortcut customization
- [ ] Task templates
- [ ] Advanced filtering
- [ ] Performance metrics
- [ ] Multi-tab support
- [ ] Browser action shortcuts

---

**Made with ❤️ for the Browser.AI community**
