"""
FastAPI Backend for Browser.AI Chat Interface

Main application that provides REST API endpoints and WebSocket connections
for the Browser.AI chat interface.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path for Browser.AI imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Import our modules
from .config_manager import config_manager, LLMProvider
from .task_manager import task_manager, TaskStatus
from .event_adapter import event_adapter
from .websocket_handler import connection_manager, websocket_handler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Browser.AI Chat Interface Backend")
    
    # Setup event adapter logging
    event_adapter.setup_browser_ai_logging()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Browser.AI Chat Interface Backend")
    
    # Stop all running tasks
    running_tasks = task_manager.get_running_tasks()
    for task in running_tasks:
        await task_manager.stop_task(task.task_id)
    
    # Cleanup event adapter
    event_adapter.cleanup_logging()


app = FastAPI(
    title="Browser.AI Chat Interface",
    description="Chat interface for Browser.AI automation with real-time updates",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for web app
web_app_path = Path(__file__).parent.parent / "web_app"
if web_app_path.exists():
    app.mount("/static", StaticFiles(directory=web_app_path / "static"), name="static")


# Pydantic models for API
class TaskCreateRequest(BaseModel):
    description: str
    config: Optional[Dict[str, Any]] = None


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str


class ConfigValidationRequest(BaseModel):
    config: Dict[str, Any]


class ConfigValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = []


class ProviderInfo(BaseModel):
    provider: str
    requirements: Dict[str, Any]


# Health check endpoint
@app.get("/")
async def read_root():
    return {"message": "Browser.AI Chat Interface Backend", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(connection_manager.active_connections),
        "running_tasks": len(task_manager.get_running_tasks()),
        "total_tasks": len(task_manager.get_all_tasks())
    }


# Configuration endpoints
@app.get("/config/default")
async def get_default_config():
    """Get default configuration"""
    return config_manager.get_default_config()


@app.get("/config/providers")
async def get_providers() -> List[ProviderInfo]:
    """Get available LLM providers and their requirements"""
    providers = []
    for provider in LLMProvider:
        requirements = config_manager.get_provider_requirements(provider.value)
        providers.append(ProviderInfo(
            provider=provider.value,
            requirements=requirements
        ))
    return providers


@app.post("/config/validate")
async def validate_config(request: ConfigValidationRequest) -> ConfigValidationResponse:
    """Validate configuration"""
    try:
        valid = config_manager.validate_llm_config(request.config)
        errors = []
        
        if not valid:
            llm_config = request.config.get('llm', {})
            provider = llm_config.get('provider')
            
            if not provider:
                errors.append("LLM provider is required")
            elif provider not in [e.value for e in LLMProvider]:
                errors.append(f"Unsupported LLM provider: {provider}")
            else:
                requirements = config_manager.get_provider_requirements(provider)
                if requirements.get('api_key_required') and not llm_config.get('api_key'):
                    errors.append(f"API key is required for {provider}")
        
        return ConfigValidationResponse(valid=valid, errors=errors)
    
    except Exception as e:
        return ConfigValidationResponse(valid=False, errors=[str(e)])


@app.post("/config/test")
async def test_config(request: ConfigValidationRequest):
    """Test configuration by attempting to create LLM instance"""
    try:
        # Create a temporary LLM instance to test configuration
        llm = task_manager.create_llm(request.config['llm'])
        return {"success": True, "message": "Configuration is valid"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Task management endpoints
@app.post("/tasks/create", response_model=TaskCreateResponse)
async def create_task(request: TaskCreateRequest):
    """Create a new automation task"""
    try:
        # Use provided config or default
        config = request.config or config_manager.get_default_config()
        
        # Validate configuration
        if not config_manager.validate_llm_config(config):
            raise HTTPException(status_code=400, detail="Invalid configuration")
        
        task_id = await task_manager.create_task(request.description, config)
        
        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING.value
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{task_id}/start")
async def start_task(task_id: str):
    """Start a pending task"""
    try:
        success = await task_manager.start_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="Task could not be started")
        
        return {"success": True, "task_id": task_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    """Stop a running task"""
    try:
        success = await task_manager.stop_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="Task could not be stopped")
        
        return {"success": True, "task_id": task_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task information"""
    task_info = task_manager.get_task_info(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_info.to_dict()


@app.get("/tasks")
async def get_all_tasks():
    """Get all tasks"""
    tasks = task_manager.get_all_tasks()
    return [task.to_dict() for task in tasks]


@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Get logs for a specific task"""
    events = event_adapter.get_task_events(task_id)
    return [event.to_dict() for event in events]


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            await websocket_handler.handle_message(websocket, data)
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


# Serve web app
@app.get("/app")
async def serve_web_app():
    """Serve the web app interface"""
    web_app_html = Path(__file__).parent.parent / "web_app" / "index.html"
    if web_app_html.exists():
        return HTMLResponse(content=web_app_html.read_text(), status_code=200)
    else:
        return HTMLResponse(content="<h1>Web app not found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    
    # Get settings
    settings = config_manager.settings
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )