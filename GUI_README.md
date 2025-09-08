# 🤖 Browser.AI GUI Components

Professional chat-based interfaces for Browser.AI automation, featuring both web and desktop applications that provide a GitHub Copilot-style experience for web automation tasks.

## ✨ Features

- **🌐 Web Interface**: Modern chat-style web application with real-time updates
- **🖥️ Desktop GUI**: Native Tkinter application mimicking VS Code's Copilot chat
- **⚙️ Configuration Management**: Easy setup for multiple LLM providers
- **📊 Real-time Monitoring**: Live task progress and log streaming  
- **🔄 Task Control**: Start, pause, resume, and stop automation tasks
- **🔌 Non-intrusive Integration**: Works with existing Browser.AI without modifications

## 🚀 Quick Start

### Prerequisites

Ensure you have Browser.AI installed:
```bash
# If using from PyPI
pip install browser-ai

# If using from source (development)
cd Browser.AI && pip install -e .
```

### Launch Applications

```bash
# 🌐 Web Interface (recommended)
python launch.py web

# 🖥️ Desktop GUI
python launch.py desktop

# 🌐 Web Interface on custom port
python launch.py web --port 8080
```

The launcher will automatically install missing dependencies.

### First Time Setup

1. **Choose your interface** (web or desktop)
2. **Configure LLM settings** in the settings panel
3. **Add your API key** for your chosen provider
4. **Start chatting** with your AI automation assistant!

## 🎯 Sample Tasks

Try these example tasks in the chat interface:

```
Search for Python tutorials on Google and summarize the top 5 results

Navigate to GitHub, find trending Python repositories, and get their names and descriptions

Go to news.ycombinator.com and extract the titles of the top 10 stories

Fill out a contact form on example.com with sample information
```

## 🖼️ Interface Preview

### 🌐 Web Interface
- **GitHub Copilot-style chat** with dark theme
- **Real-time task execution** with live updates
- **Configuration sidebar** for LLM and browser settings
- **Mobile-responsive design** works on phones and tablets
- **WebSocket communication** for instant updates

### 🖥️ Desktop GUI
- **VS Code Copilot-style** split-pane interface
- **Native desktop controls** and styling
- **Real-time log viewer** in the sidebar
- **Configuration dialogs** for settings management
- **Thread-safe updates** for smooth operation

## ⚙️ Configuration

### Supported LLM Providers

| Provider | Models | Setup |
|----------|--------|-------|
| **OpenAI** | GPT-4, GPT-4-turbo, GPT-3.5-turbo | Add `OPENAI_API_KEY` |
| **Anthropic** | Claude-3 (Opus, Sonnet, Haiku) | Add `ANTHROPIC_API_KEY` |
| **Google** | Gemini Pro, Gemini Pro Vision | Add `GOOGLE_API_KEY` |
| **Ollama** | Llama2, CodeLlama, Mistral, etc. | Local installation |

### Environment Setup

Create a `.env` file in your project root:

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Logging level (debug, info, result)
BROWSER_AI_LOGGING_LEVEL=info
```

### Configuration Location

Settings are stored in:
- **Default**: `~/.browser_ai_gui/config.json`
- **Custom**: Use `--config-dir` parameter

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web/Desktop   │    │  Event Adapter  │    │  Browser.AI     │
│   Interface     │◄───┤  (Log Stream)   │◄───┤     Agent       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Config Manager  │    │ Task Manager    │    │ Browser Context │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Event Flow

1. **User Input** → Chat interface captures task description
2. **Task Manager** → Creates Browser.AI Agent with configured LLM
3. **Agent Execution** → Browser.AI performs automation steps
4. **Log Capture** → Event Adapter captures logs non-intrusively
5. **Real-time Updates** → GUI receives live progress updates
6. **Result Display** → Formatted results shown in chat

## 📁 Project Structure

```
browser_ai_gui/
├── __init__.py              # Package initialization
├── event_adapter.py         # Non-intrusive log capture
├── config.py               # Configuration management
├── web_app.py              # Flask web application
├── tkinter_gui.py          # Desktop GUI application
├── main.py                 # Entry points
├── requirements.txt        # Additional dependencies
├── templates/
│   └── index.html          # Web interface template
└── README.md               # Component documentation

# Additional files
├── launch.py               # Smart launcher script
├── examples.py             # Usage examples  
├── demo.py                 # Component testing
├── IMPLEMENTATION.md       # Technical details
└── test_web.py            # Web interface testing
```

## 🛠️ Development

### Installing Dependencies

```bash
# GUI dependencies
pip install flask flask-socketio eventlet

# Or use optional dependencies
pip install .[gui]
```

### Running Tests

```bash
# Test core components
python demo.py

# Test web interface
python test_web.py

# Test imports
python -c "from browser_ai_gui import EventAdapter, ConfigManager, WebApp; print('✅ All imports successful')"
```

### Adding Custom Features

The modular architecture makes it easy to extend:

- **Event Types**: Add new events in `event_adapter.py`
- **Configuration**: Extend config models in `config.py`
- **API Endpoints**: Add Flask routes in `web_app.py`
- **UI Components**: Update templates and GUI components

## 🔧 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Install missing dependencies
pip install flask flask-socketio eventlet
```

**Port Already in Use**
```bash
# Use different port
python launch.py web --port 8080
```

**Tkinter Not Available**
```bash
# Linux
sudo apt-get install python3-tk

# Use web interface instead
python launch.py web
```

**API Key Issues**
- Check your API keys in the configuration panel
- Ensure sufficient credits/quota
- Verify the correct environment variables

### Debug Mode

```bash
# Enable detailed logging
export BROWSER_AI_LOGGING_LEVEL=debug

# Run web interface in debug mode
python launch.py web --debug
```

## 📖 Advanced Usage

### Programmatic Usage

```python
from browser_ai_gui import EventAdapter, ConfigManager, WebApp

# Setup components
config = ConfigManager()
adapter = EventAdapter()

# Configure LLM
config.update_llm_config(
    provider="openai",
    model="gpt-4-turbo",
    api_key="your-api-key"
)

# Start event streaming
adapter.start()
adapter.subscribe(lambda event: print(f"[{event.level}] {event.message}"))

# Create web app
app = WebApp(config, port=5000)
app.run()
```

### Custom Event Handling

```python
from browser_ai_gui import EventAdapter, EventType, LogLevel

adapter = EventAdapter()

def handle_agent_events(event):
    if event.event_type == EventType.AGENT_COMPLETE:
        print("✅ Task completed successfully!")
    elif event.event_type == EventType.AGENT_ERROR:
        print(f"❌ Error occurred: {event.message}")

adapter.subscribe(handle_agent_events)
adapter.start()

# Emit custom events
adapter.emit_custom_event(
    EventType.AGENT_START,
    "Custom task started",
    LogLevel.INFO,
    {"task_id": "custom-001"}
)
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- **Additional LLM Providers**: Support for more language models
- **UI Enhancements**: Improved styling and user experience
- **Mobile Support**: Better responsive design
- **Export Features**: Save conversations and results
- **Plugin System**: Extensible actions and events
- **Advanced Monitoring**: Analytics and performance metrics

## 📄 License

Same as Browser.AI main package.

---

## 🎉 Success Story

This implementation successfully provides:

✅ **Professional GUI interfaces** for Browser.AI automation  
✅ **Real-time task monitoring** with live log streaming  
✅ **Multi-provider LLM support** with easy configuration  
✅ **Non-intrusive integration** requiring zero Browser.AI modifications  
✅ **Production-ready architecture** with proper error handling  
✅ **User-friendly experience** rivaling commercial AI assistants  

**Get started now with:** `python launch.py web`