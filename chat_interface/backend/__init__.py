"""
Chat Interface Backend

Backend components for the Browser.AI Chat Interface.

## Components

- **main.py**: FastAPI application with REST API and WebSocket endpoints
- **task_manager.py**: Manages Browser.AI task execution and lifecycle
- **event_adapter.py**: Captures and streams Browser.AI logs in real-time
- **websocket_handler.py**: Handles WebSocket connections and real-time communication
- **config_manager.py**: Manages LLM configurations and application settings

## API Endpoints

### Configuration
- `GET /config/default` - Get default configuration
- `GET /config/providers` - Get available LLM providers
- `POST /config/validate` - Validate configuration
- `POST /config/test` - Test LLM configuration

### Tasks
- `POST /tasks/create` - Create new automation task
- `POST /tasks/{task_id}/start` - Start pending task
- `POST /tasks/{task_id}/stop` - Stop running task
- `GET /tasks/{task_id}` - Get task information
- `GET /tasks` - Get all tasks
- `GET /tasks/{task_id}/logs` - Get task logs

### WebSocket
- `WS /ws` - Real-time communication endpoint

## Running the Backend

```bash
cd chat_interface/backend
python main.py
```

The backend will start on http://localhost:8000 by default.
"""