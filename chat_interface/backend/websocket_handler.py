"""
WebSocket Handler for Browser.AI Chat Interface

Manages WebSocket connections and real-time communication.
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

from .event_adapter import event_adapter, LogEvent
from .task_manager import task_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_tasks: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection established. Total: {len(self.active_connections)}")
        
        # Subscribe to events for this connection
        event_adapter.subscribe(lambda event: self._broadcast_to_client(websocket, event))
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.client_tasks:
            del self.client_tasks[websocket]
            
        logger.info(f"WebSocket connection closed. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
            
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def _broadcast_to_client(self, websocket: WebSocket, event: LogEvent):
        """Broadcast a log event to a specific client"""
        if websocket not in self.active_connections:
            return
            
        message = {
            'type': 'log_event',
            'data': event.to_dict()
        }
        
        await self.send_personal_message(message, websocket)


class WebSocketHandler:
    """Handles WebSocket message processing"""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'start_task':
                await self._handle_start_task(websocket, data)
            elif message_type == 'stop_task':
                await self._handle_stop_task(websocket, data)
            elif message_type == 'get_task_status':
                await self._handle_get_task_status(websocket, data)
            elif message_type == 'get_task_history':
                await self._handle_get_task_history(websocket, data)
            elif message_type == 'ping':
                await self._handle_ping(websocket)
            else:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }, websocket)
                
        except json.JSONDecodeError:
            await self.manager.send_personal_message({
                'type': 'error',
                'message': 'Invalid JSON message'
            }, websocket)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.manager.send_personal_message({
                'type': 'error',
                'message': f'Internal error: {str(e)}'
            }, websocket)
    
    async def _handle_start_task(self, websocket: WebSocket, data: Dict):
        """Handle start task request"""
        try:
            description = data.get('description', '')
            config = data.get('config', {})
            
            if not description:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': 'Task description is required'
                }, websocket)
                return
            
            # Create and start task
            task_id = await task_manager.create_task(description, config)
            success = await task_manager.start_task(task_id)
            
            if success:
                # Associate this client with the task
                self.manager.client_tasks[websocket] = task_id
                
                await self.manager.send_personal_message({
                    'type': 'task_started',
                    'data': {
                        'task_id': task_id,
                        'description': description
                    }
                }, websocket)
            else:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': 'Failed to start task'
                }, websocket)
                
        except Exception as e:
            await self.manager.send_personal_message({
                'type': 'error',
                'message': f'Error starting task: {str(e)}'
            }, websocket)
    
    async def _handle_stop_task(self, websocket: WebSocket, data: Dict):
        """Handle stop task request"""
        try:
            task_id = data.get('task_id')
            
            # If no task_id provided, stop the client's current task
            if not task_id and websocket in self.manager.client_tasks:
                task_id = self.manager.client_tasks[websocket]
            
            if not task_id:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': 'No task to stop'
                }, websocket)
                return
            
            success = await task_manager.stop_task(task_id)
            
            if success:
                if websocket in self.manager.client_tasks:
                    del self.manager.client_tasks[websocket]
                
                await self.manager.send_personal_message({
                    'type': 'task_stopped',
                    'data': {
                        'task_id': task_id
                    }
                }, websocket)
            else:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': 'Failed to stop task or task not found'
                }, websocket)
                
        except Exception as e:
            await self.manager.send_personal_message({
                'type': 'error',
                'message': f'Error stopping task: {str(e)}'
            }, websocket)
    
    async def _handle_get_task_status(self, websocket: WebSocket, data: Dict):
        """Handle get task status request"""
        try:
            task_id = data.get('task_id')
            
            if not task_id:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': 'Task ID is required'
                }, websocket)
                return
            
            task_info = task_manager.get_task_info(task_id)
            
            if task_info:
                await self.manager.send_personal_message({
                    'type': 'task_status',
                    'data': task_info.to_dict()
                }, websocket)
            else:
                await self.manager.send_personal_message({
                    'type': 'error',
                    'message': 'Task not found'
                }, websocket)
                
        except Exception as e:
            await self.manager.send_personal_message({
                'type': 'error',
                'message': f'Error getting task status: {str(e)}'
            }, websocket)
    
    async def _handle_get_task_history(self, websocket: WebSocket, data: Dict):
        """Handle get task history request"""
        try:
            task_id = data.get('task_id')
            
            if task_id:
                events = event_adapter.get_task_events(task_id)
            else:
                # Get all tasks
                tasks = task_manager.get_all_tasks()
                events = []
                for task in tasks:
                    events.extend(event_adapter.get_task_events(task.task_id))
            
            await self.manager.send_personal_message({
                'type': 'task_history',
                'data': {
                    'task_id': task_id,
                    'events': [event.to_dict() for event in events]
                }
            }, websocket)
                
        except Exception as e:
            await self.manager.send_personal_message({
                'type': 'error',
                'message': f'Error getting task history: {str(e)}'
            }, websocket)
    
    async def _handle_ping(self, websocket: WebSocket):
        """Handle ping request"""
        await self.manager.send_personal_message({
            'type': 'pong'
        }, websocket)


# Global instances
connection_manager = ConnectionManager()
websocket_handler = WebSocketHandler(connection_manager)