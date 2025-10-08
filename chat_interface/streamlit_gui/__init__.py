# Streamlit GUI Components

This directory contains the Streamlit-based GUI components for the Browser.AI Chat Interface.

## Components

- **main.py**: Main Streamlit application entry point
- **components/**: UI components
  - **chat_interface.py**: GitHub Copilot-like chat interface
  - **config_panel.py**: LLM and browser configuration panel
  - **status_display.py**: Real-time status and log display
- **utils/**: Utility modules
  - **websocket_client.py**: WebSocket client for real-time communication

## Features

- **GitHub Copilot-like Interface**: Familiar chat interface for describing automation tasks
- **Real-time Updates**: Live status updates and log streaming
- **Configuration Management**: Easy setup of LLM providers and API keys
- **Task Control**: Start, stop, and monitor automation tasks
- **History View**: Browse past tasks and their results

## Running the GUI

1. Make sure the backend is running:
   ```bash
   cd ../backend
   python main.py
   ```

2. Start the Streamlit GUI:
   ```bash
   streamlit run main.py
   ```

3. Open your browser to http://localhost:8501

## Usage

1. **Configure your LLM** in the configuration panel
2. **Test your configuration** to ensure it's working
3. **Describe your automation task** in the chat interface
4. **Monitor progress** in real-time via the sidebar and logs
5. **Stop tasks** if needed using the stop button

## Examples

- "Navigate to Google and search for 'Browser.AI automation'"
- "Go to Amazon, search for 'wireless headphones', and add the first result to cart"
- "Visit GitHub, find the Browser.AI repository, and star it"
- "Open LinkedIn, go to my profile, and update my headline"