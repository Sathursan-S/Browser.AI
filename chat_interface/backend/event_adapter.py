"""
Event Adapter for Browser.AI Log Streaming

This module provides a custom logging handler that captures Browser.AI logs
and streams them to connected clients in real-time.
"""

import asyncio
import logging
import json
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import uuid


class LogEvent:
    """Represents a single log event"""
    
    def __init__(self, level: str, message: str, logger_name: str, timestamp: str = None):
        self.id = str(uuid.uuid4())
        self.level = level
        self.message = message
        self.logger_name = logger_name
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'logger_name': self.logger_name,
            'timestamp': self.timestamp
        }


class EventAdapter:
    """Adapter that captures and streams Browser.AI events and logs"""
    
    def __init__(self):
        self.subscribers: List[Callable] = []
        self.log_handler: Optional[logging.Handler] = None
        self.task_events: Dict[str, List[LogEvent]] = {}
        
    def subscribe(self, callback: Callable):
        """Subscribe to log events"""
        self.subscribers.append(callback)
        
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from log events"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    async def emit_event(self, event: LogEvent):
        """Emit an event to all subscribers"""
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in event callback: {e}")
    
    def setup_browser_ai_logging(self):
        """Setup custom logging handler for Browser.AI"""
        if self.log_handler:
            return  # Already setup
            
        class StreamingHandler(logging.Handler):
            def __init__(self, adapter):
                super().__init__()
                self.adapter = adapter
                
            def emit(self, record):
                try:
                    log_entry = LogEvent(
                        level=record.levelname,
                        message=self.format(record),
                        logger_name=record.name
                    )
                    
                    # Run emit_event in the event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.adapter.emit_event(log_entry))
                        else:
                            loop.run_until_complete(self.adapter.emit_event(log_entry))
                    except RuntimeError:
                        # If no event loop is running, store the event for later
                        if hasattr(self.adapter, '_pending_events'):
                            self.adapter._pending_events.append(log_entry)
                except Exception:
                    pass  # Ignore logging errors to prevent recursion
        
        # Setup handler for Browser.AI logger
        self.log_handler = StreamingHandler(self)
        self.log_handler.setFormatter(logging.Formatter('%(levelname)-8s [%(name)s] %(message)s'))
        
        # Get the browser_ai logger
        browser_ai_logger = logging.getLogger('browser_ai')
        browser_ai_logger.addHandler(self.log_handler)
        
        # Also capture root level logs that might be relevant
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
    def cleanup_logging(self):
        """Remove the custom logging handler"""
        if self.log_handler:
            browser_ai_logger = logging.getLogger('browser_ai')
            browser_ai_logger.removeHandler(self.log_handler)
            
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
            
            self.log_handler = None
    
    async def create_task_event(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """Create a task-specific event"""
        event = LogEvent(
            level="INFO",
            message=f"Task {event_type}: {json.dumps(data)}",
            logger_name="task_manager",
        )
        
        if task_id not in self.task_events:
            self.task_events[task_id] = []
        
        self.task_events[task_id].append(event)
        await self.emit_event(event)
    
    def get_task_events(self, task_id: str) -> List[LogEvent]:
        """Get all events for a specific task"""
        return self.task_events.get(task_id, [])
    
    def clear_task_events(self, task_id: str):
        """Clear events for a specific task"""
        if task_id in self.task_events:
            del self.task_events[task_id]


# Global event adapter instance
event_adapter = EventAdapter()