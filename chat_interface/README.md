# Browser.AI Chat Interface

A chat interface for Browser.AI automation, similar to GitHub Copilot, providing real-time task execution and logging.

## Features

- **Chat Interface**: Intuitive chat interface for automation tasks
- **Real-time Updates**: Live logging and status updates during automation
- **Configuration Management**: Easy LLM and API key configuration
- **Task Control**: Start and stop automation tasks seamlessly
- **Multiple Interfaces**: Both Streamlit GUI and Web App options

## Installation

```bash
# Install Browser.AI first
pip install -e .

# Install chat interface dependencies
pip install -r chat_interface/requirements.txt
```

## Quick Start

### Streamlit GUI
```bash
cd chat_interface/streamlit_gui
streamlit run main.py
```

### Web App
```bash
cd chat_interface
python backend/main.py
# Then open web_app/index.html
```

## Architecture

- **Backend**: FastAPI with WebSocket support for real-time communication
- **Event Adapter**: Custom logging handler for Browser.AI log streaming
- **Task Manager**: Orchestration service for automation tasks
- **Configuration**: Environment-based LLM and API key management

## Usage

1. Configure your LLM provider and API keys
2. Start a chat session
3. Describe your automation task
4. Monitor real-time progress and logs
5. Stop tasks gracefully when needed