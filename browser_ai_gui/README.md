# Browser.AI GUI Components

This package provides intuitive chat-based interfaces for Browser.AI automation, including both web and desktop applications that mimic popular AI assistants like GitHub Copilot.

## Features

- **Web Interface**: Chat-style web application with real-time log streaming
- **Desktop GUI**: Tkinter-based application similar to VS Code's Copilot chat
- **Configuration Management**: Easy setup for LLM providers and browser settings
- **Real-time Updates**: Live task progress and log streaming
- **Task Control**: Start, stop, and pause automation tasks
- **Event System**: Non-intrusive log capture without modifying Browser.AI core

## Quick Start

### Prerequisites

```bash
# Install Browser.AI (main package)
pip install -r ../pyproject.toml

# Install GUI dependencies
pip install flask flask-socketio
```

### Running the Applications

#### Web Interface

```bash
# Start web interface on default port (5000)
python examples.py web

# Start on custom port
python examples.py web --port 8080

# Run in debug mode
python examples.py web --debug
```

Access the web interface at: `http://localhost:5000`

#### Desktop GUI

```bash
# Start desktop GUI
python examples.py desktop
```

#### Using the Main Module

```bash
# Alternative way to run
cd browser_ai_gui
python main.py web --port 8080
python main.py desktop
```

## Configuration

### First Time Setup

1. **Run any interface first** - it will create a configuration directory
2. **Set up your API keys** in the settings panel
3. **Configure browser and agent settings** as needed

### Configuration Location

- Default: `~/.browser_ai_gui/config.json`
- Custom: Use `--config-dir` parameter

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  
GOOGLE_API_KEY=your_google_api_key

# Logging level
BROWSER_AI_LOGGING_LEVEL=info
```

### Supported LLM Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro
- **Ollama**: Local models (Llama2, CodeLlama, Mistral, etc.)

## Usage Examples

### Sample Tasks

Try these example tasks in the chat interface:

```
Search for Python tutorials on Google and summarize the top 5 results

Go to GitHub, find trending Python repositories, and extract their names and descriptions

Navigate to news.ycombinator.com and get the titles of the top 10 stories

Fill out the contact form on example.com with sample data
```

### Web Interface Features

- **Real-time Chat**: Interactive conversation with the AI agent
- **Configuration Panel**: Easy setup of LLM and browser settings
- **Live Status Updates**: See task progress in real-time
- **Task Controls**: Pause, resume, and stop running tasks
- **Responsive Design**: Works on desktop and mobile

### Desktop GUI Features

- **VS Code Style**: Familiar interface similar to GitHub Copilot
- **Split Layout**: Configuration sidebar with main chat area
- **Log Viewer**: Real-time log streaming in the sidebar
- **Native Feel**: Desktop-native controls and styling

## Architecture

### Core Components

1. **EventAdapter**: Captures Browser.AI logs without modifying the library (legacy)
2. **Structured Event System**: New SOLID-compliant event emission system
3. **ConfigManager**: Handles LLM, browser, and GUI configuration
4. **WebApp**: Flask-based web application with WebSocket support
5. **BrowserAIGUI**: Tkinter desktop application
6. **TaskManager**: Manages Browser.AI agent lifecycle

### Event System

#### New Structured Event System (Recommended)

The new structured event system provides a decoupled, SOLID-compliant architecture for emitting and consuming events:

```python
from browser_ai_gui.events import (
    EventEmitter, 
    EventTransport, 
    AgentStartEvent,
    EventCategory
)
from browser_ai_gui.events.bridge import EventBridge

# Create event system
emitter = EventEmitter()
transport = EventTransport(socketio=socketio, namespace="/extension")
bridge = EventBridge(emitter, transport)

# Subscribe to events
def handle_event(event):
    print(f"Event: {event.event_type}")

emitter.subscribe(handle_event)

# Emit structured events
event = bridge.create_agent_start_event(
    task_description="Book a ticket",
    agent_id="agent-123",
    configuration={"max_steps": 50}
)
bridge.emit_structured_event(event)
```

**Features:**
- Type-safe event schemas
- Event filtering by type and category
- Multiple transport support (WebSocket, callbacks)
- Session and task ID tracking
- Progress and LLM output events

**See:** [Structured Events Documentation](../docs/STRUCTURED_EVENTS.md)

#### Legacy Event Adapter

The original event adapter is still supported for backward compatibility:

```python
from browser_ai_gui import EventAdapter, LogEvent

# Create event adapter
adapter = EventAdapter()

# Subscribe to events
def handle_event(event: LogEvent):
    print(f"[{event.level}] {event.message}")

adapter.subscribe(handle_event)
adapter.start()

# Now Browser.AI logs will be captured
```

### Custom Integration

```python
from browser_ai_gui import ConfigManager, TaskManager, EventAdapter
from browser_ai_gui.events import EventEmitter, EventTransport
from browser_ai_gui.events.bridge import EventBridge

# Setup components
config = ConfigManager()
adapter = EventAdapter()

# Setup structured events
emitter = EventEmitter()
transport = EventTransport()
bridge = EventBridge(emitter, transport)

# Subscribe to structured events
emitter.subscribe(lambda event: print(f"Event: {event.event_type}"))

task_manager = TaskManager(config, adapter)

# Start a task programmatically
task_manager.start_task("Your task description here")
```

## Development

### Project Structure

```
browser_ai_gui/
├── __init__.py           # Package initialization
├── event_adapter.py     # Legacy log capture and event streaming
├── events/              # New structured event system
│   ├── __init__.py      # Public event system API
│   ├── schemas.py       # Event data structures
│   ├── emitter.py       # Event emission (pub-sub)
│   ├── transport.py     # Event transport layer
│   └── bridge.py        # Integration bridge
├── config.py            # Configuration management
├── protocol.py          # WebSocket protocol definitions
├── websocket_server.py  # Extension WebSocket server
├── web_app.py           # Flask web application
├── tkinter_gui.py       # Desktop GUI application
├── main.py              # Main entry points
└── templates/
    └── index.html       # Web interface template
```

### Adding New Features

1. **Event Types**: Add new event types in `event_adapter.py`
2. **Configuration**: Extend config models in `config.py`
3. **UI Components**: Update templates and GUI components
4. **API Endpoints**: Add new Flask routes in `web_app.py`

### Testing

```bash
# Test web interface
python -c "from browser_ai_gui import WebApp; print('Web app imports successfully')"

# Test desktop interface
python -c "from browser_ai_gui import BrowserAIGUI; print('Desktop GUI imports successfully')"

# Test configuration
python -c "from browser_ai_gui import ConfigManager; c = ConfigManager(); print('Config loaded')"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Install missing dependencies with `pip install flask flask-socketio`
2. **Port Already in Use**: Use `--port` parameter to specify a different port
3. **API Key Issues**: Check your API keys in the configuration panel
4. **Tkinter Not Available**: Reinstall Python with Tkinter support

### Debug Mode

Run the web interface in debug mode for detailed error information:

```bash
python examples.py web --debug
```

### Log Levels

Set logging level in environment or configuration:

```bash
export BROWSER_AI_LOGGING_LEVEL=debug
```

## Contributing

Contributions welcome! Areas for improvement:

- **Additional LLM Providers**: Support for more language models
- **UI Enhancements**: Better styling and user experience
- **Mobile Support**: Responsive web interface improvements  
- **Export Features**: Save conversation history and results
- **Plugin System**: Extensible action and event system

## License

Same as Browser.AI main package.