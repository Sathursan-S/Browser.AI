# Browser AI Chat Interface

A conversational interface for the Browser AI library that provides GitHub Copilot-like chat functionality for browser automation. Available as both a web application and Qt desktop application.

## Features

### 🤖 Conversational Browser Automation
- Chat-based interface for controlling browser automation
- Natural language task descriptions
- Real-time progress updates and logging

### 🌐 Web Application
- Modern web interface built with Gradio
- Real-time log streaming
- Responsive design for desktop and mobile
- Easy configuration management

### 🖥️ Desktop Application  
- Native Qt desktop interface
- System tray integration
- Customizable themes
- Offline configuration storage

### ⚙️ LLM Configuration
- Support for multiple LLM providers:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Ollama (Local models)
  - Google Gemini
  - Fireworks AI
- Easy API key management
- Temperature and parameter controls
- Configuration testing

### 📊 Real-time Monitoring
- Live log streaming from Browser AI
- Animated status indicators
- Task progress tracking
- Error handling and reporting

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install browser-ai gradio PyQt5

# For Playwright browser automation
playwright install
```

### Quick Start

1. **Web Interface:**
   ```bash
   python launch_web.py
   ```
   - Opens at http://localhost:7860
   - Configure LLM settings in the web interface
   - Start chatting to control browser automation

2. **Desktop Interface:**
   ```bash
   python launch_desktop.py
   ```
   - Native Qt application window
   - Configure LLM in the settings panel
   - Chat interface on the left, logs on the right

## Configuration

### LLM Setup

#### OpenAI
```python
# Add via interface or set environment variable
export OPENAI_API_KEY="your-api-key-here"
```

#### Anthropic Claude
```python
# Add via interface or set environment variable  
export ANTHROPIC_API_KEY="your-api-key-here"
```

#### Ollama (Local)
```bash
# Start Ollama server
ollama serve

# Pull a model
ollama pull llama3.2

# Configure in interface:
# - Provider: ollama
# - Model: llama3.2  
# - Base URL: http://localhost:11434
```

### Application Settings

Settings are stored in `~/.browser_ai_chat/config.json`:

```json
{
  "llm_configs": {
    "my_openai": {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "api_key": "sk-...",
      "temperature": 0.1
    }
  },
  "app_config": {
    "theme": "light",
    "auto_save": true,
    "log_level": "info",
    "max_history_items": 100
  }
}
```

## Usage Examples

### Basic Tasks

```
User: Search for "Python web scraping" on Google
Assistant: 🔄 Starting task execution...
[12:34:56] 🔵 Step 1: Navigating to Google...
[12:34:58] 🔵 Step 2: Searching for "Python web scraping"...
[12:35:02] 🟢 ✅ Task Completed

Search results for "Python web scraping" are now displayed on Google.
```

### E-commerce Automation

```
User: Go to Amazon and find the best rated wireless headphones under $100
Assistant: 🔄 Starting task execution...
[12:35:10] 🔵 Step 1: Navigating to Amazon.com...
[12:35:12] 🔵 Step 2: Searching for wireless headphones...
[12:35:15] 🔵 Step 3: Applying price filter under $100...
[12:35:18] 🔵 Step 4: Sorting by customer ratings...
[12:35:22] 🟢 ✅ Task Completed

Found top-rated wireless headphones under $100:
1. Sony WH-CH720N - 4.4/5 stars - $89.99
2. JBL Tune 760NC - 4.3/5 stars - $79.95
3. Anker Soundcore Q30 - 4.2/5 stars - $79.99
```

### Form Filling

```
User: Fill out the contact form on example.com with my details
Assistant: 🔄 Starting task execution...
[12:36:30] 🔵 Step 1: Navigating to example.com...
[12:36:32] 🔵 Step 2: Locating contact form...
[12:36:34] 🔵 Step 3: Filling name field...
[12:36:36] 🔵 Step 4: Filling email field...
[12:36:38] 🔵 Step 5: Filling message field...
[12:36:40] 🔵 Step 6: Submitting form...
[12:36:42] 🟢 ✅ Task Completed

Contact form successfully submitted with your details.
```

## Architecture

### Event System
The chat interface uses an event-driven architecture to capture real-time updates:

```python
from chat_interface import LogEventListener

# Create event listener
listener = LogEventListener()
listener.start_listening()

# Subscribe to events
listener.subscribe_to_logs(on_log_event)
listener.subscribe_to_tasks(on_task_update)
```

### Configuration Management
Centralized configuration system for LLMs and app settings:

```python
from chat_interface import ConfigManager

config = ConfigManager()
config.add_llm_config("my_llm", llm_config)
llm_instance = config.create_llm_instance(llm_config)
```

### Integration with Browser AI
Seamless integration without modifying core Browser AI library:

```python
# Agent creation with callbacks
agent = Agent(
    task=user_task,
    llm=selected_llm,
    register_new_step_callback=event_listener.handle_agent_step,
    register_done_callback=event_listener.handle_agent_done
)

# Run with real-time updates
history = await agent.run()
```

## Advanced Features

### Custom Actions
Extend functionality with custom browser actions:

```python
from browser_ai import Controller

controller = Controller()

@controller.action("Take screenshot of current page")
async def screenshot(browser):
    # Custom screenshot logic
    return ActionResult(extracted_content="Screenshot saved")
```

### Task Templates
Save common automation patterns:

```python
templates = {
    "google_search": "Search for '{query}' on Google",
    "price_check": "Check price of '{product}' on {website}",
    "form_fill": "Fill out contact form with my details"
}
```

### Batch Operations
Run multiple tasks in sequence:

```python
tasks = [
    "Open Gmail and check for new emails",
    "Navigate to calendar and check today's appointments", 
    "Update status on LinkedIn"
]

for task in tasks:
    await run_task(task)
```

## Troubleshooting

### Common Issues

1. **"No LLM configured" error**
   - Add LLM configuration via the interface
   - Check API key validity
   - Verify network connectivity

2. **Task execution fails**
   - Check browser installation: `playwright install`
   - Verify website accessibility
   - Review logs for specific errors

3. **Web interface not loading**
   - Check port 7860 is available
   - Try different port: `python launch_web.py --server-port 8000`

4. **Desktop app crashes**
   - Install Qt dependencies: `pip install PyQt5`
   - Check display settings
   - Run from terminal to see error messages

### Debug Mode

Enable debug logging:

```bash
export BROWSER_AI_LOGGING_LEVEL=debug
python launch_web.py
```

### Log Files

Application logs are stored in:
- Web: Browser console and interface logs panel
- Desktop: Application logs panel and console output
- Browser AI: Real-time streaming to both interfaces

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/Sathursan-S/Browser.AI.git
cd Browser.AI

# Install dependencies
pip install -e .
pip install gradio PyQt5

# Run tests
python -m pytest chat_interface/tests/
```

### Adding New LLM Providers

1. Add provider to `LLMProvider` enum
2. Implement in `ConfigManager.create_llm_instance()`
3. Add provider-specific models list
4. Update configuration UI

### Extending UI Features

1. **Web Interface**: Modify `chat_interface/web_app.py`
2. **Desktop Interface**: Modify `chat_interface/desktop_app.py`  
3. **Shared Logic**: Update base classes in respective modules

## License

This project extends the Browser AI library. Please refer to the main project license.

## Support

- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See Browser AI main documentation

## Changelog

### v0.1.0
- Initial release
- Web and desktop chat interfaces
- Multi-LLM provider support
- Real-time log streaming
- Configuration management
- Event-driven architecture