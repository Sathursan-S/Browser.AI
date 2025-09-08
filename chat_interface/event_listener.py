"""
Event listener adapter for Browser AI logging system.

This module provides real-time log streaming capabilities by hooking into 
the existing Browser AI logging infrastructure without modifying core library code.
"""

import asyncio
import logging
import queue
import threading
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from browser_ai.agent.views import ActionResult, AgentHistory
from browser_ai.browser.views import BrowserState


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    RESULT = "result"


class TaskStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LogEvent:
    """Represents a log event with metadata"""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    step_number: Optional[int] = None
    task_status: TaskStatus = TaskStatus.IDLE
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskUpdate:
    """Represents a task progress update"""
    task_id: str
    status: TaskStatus
    step_number: int
    total_steps: Optional[int]
    current_action: Optional[str]
    result: Optional[str]
    error: Optional[str]
    timestamp: datetime


class LogEventListener:
    """
    Event listener that hooks into Browser AI logging system to capture
    real-time events for streaming to chat interfaces.
    """
    
    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self._events: queue.Queue = queue.Queue(maxsize=max_events)
        self._subscribers: List[Callable[[LogEvent], None]] = []
        self._task_subscribers: List[Callable[[TaskUpdate], None]] = []
        self._logger_handler: Optional[logging.Handler] = None
        self._current_task_id: Optional[str] = None
        self._current_step: int = 0
        self._task_status: TaskStatus = TaskStatus.IDLE
        self._lock = threading.Lock()
    
    def start_listening(self):
        """Start listening to Browser AI logs"""
        # Create custom handler for browser_ai logger
        self._logger_handler = LogCaptureHandler(self)
        
        # Get the browser_ai logger and add our handler
        browser_ai_logger = logging.getLogger('browser_ai')
        browser_ai_logger.addHandler(self._logger_handler)
        browser_ai_logger.setLevel(logging.DEBUG)
        
    def stop_listening(self):
        """Stop listening to logs"""
        if self._logger_handler:
            browser_ai_logger = logging.getLogger('browser_ai')
            browser_ai_logger.removeHandler(self._logger_handler)
            self._logger_handler = None
    
    def subscribe_to_logs(self, callback: Callable[[LogEvent], None]):
        """Subscribe to log events"""
        with self._lock:
            self._subscribers.append(callback)
    
    def subscribe_to_tasks(self, callback: Callable[[TaskUpdate], None]):
        """Subscribe to task progress updates"""
        with self._lock:
            self._task_subscribers.append(callback)
    
    def unsubscribe_from_logs(self, callback: Callable[[LogEvent], None]):
        """Unsubscribe from log events"""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
    
    def unsubscribe_from_tasks(self, callback: Callable[[TaskUpdate], None]):
        """Unsubscribe from task updates"""
        with self._lock:
            if callback in self._task_subscribers:
                self._task_subscribers.remove(callback)
    
    def _emit_log_event(self, event: LogEvent):
        """Emit log event to all subscribers"""
        try:
            # Add to queue
            if not self._events.full():
                self._events.put_nowait(event)
            else:
                # Remove oldest event to make space
                try:
                    self._events.get_nowait()
                    self._events.put_nowait(event)
                except queue.Empty:
                    pass
            
            # Notify subscribers
            with self._lock:
                for callback in self._subscribers:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"Error in log subscriber callback: {e}")
        except Exception as e:
            print(f"Error emitting log event: {e}")
    
    def _emit_task_update(self, update: TaskUpdate):
        """Emit task update to all subscribers"""
        with self._lock:
            for callback in self._task_subscribers:
                try:
                    callback(update)
                except Exception as e:
                    print(f"Error in task subscriber callback: {e}")
    
    def get_recent_events(self, count: int = 50) -> List[LogEvent]:
        """Get recent log events"""
        events = []
        temp_queue = queue.Queue()
        
        # Move events to temp queue while collecting them
        while not self._events.empty() and len(events) < count:
            try:
                event = self._events.get_nowait()
                events.append(event)
                temp_queue.put(event)
            except queue.Empty:
                break
        
        # Put events back
        while not temp_queue.empty():
            try:
                self._events.put_nowait(temp_queue.get_nowait())
            except queue.Full:
                break
        
        return list(reversed(events))  # Most recent first
    
    def set_task_status(self, task_id: str, status: TaskStatus, step_number: int = 0):
        """Update task status and emit update"""
        self._current_task_id = task_id
        self._task_status = status
        self._current_step = step_number
        
        update = TaskUpdate(
            task_id=task_id,
            status=status,
            step_number=step_number,
            total_steps=None,
            current_action=None,
            result=None,
            error=None,
            timestamp=datetime.now()
        )
        self._emit_task_update(update)
    
    def handle_agent_step(self, state: 'BrowserState', output: Any, step: int):
        """Handle agent step callback"""
        self._current_step = step
        
        # Create log event for step
        event = LogEvent(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message=f"Step {step}: {getattr(output.current_state, 'next_goal', 'Processing...') if output and hasattr(output, 'current_state') else 'Processing...'}",
            source="agent",
            step_number=step,
            task_status=TaskStatus.RUNNING,
            metadata={
                'url': state.url if state else None,
                'title': state.title if state else None,
                'action_count': len(getattr(output, 'action', [])) if output else 0
            }
        )
        self._emit_log_event(event)
        
        # Emit task update
        if self._current_task_id:
            update = TaskUpdate(
                task_id=self._current_task_id,
                status=TaskStatus.RUNNING,
                step_number=step,
                total_steps=None,
                current_action=getattr(output.current_state, 'next_goal', 'Processing...') if output and hasattr(output, 'current_state') else 'Processing...',
                result=None,
                error=None,
                timestamp=datetime.now()
            )
            self._emit_task_update(update)
    
    def handle_agent_done(self, history: List[AgentHistory]):
        """Handle agent completion callback"""
        if history and len(history) > 0:
            last_item = history[-1]
            if last_item.result and len(last_item.result) > 0:
                last_result = last_item.result[-1]
                if last_result.is_done:
                    # Task completed successfully
                    event = LogEvent(
                        timestamp=datetime.now(),
                        level=LogLevel.RESULT,
                        message=f"Task completed: {last_result.extracted_content}",
                        source="agent",
                        step_number=self._current_step,
                        task_status=TaskStatus.COMPLETED,
                        metadata={'result': last_result.extracted_content}
                    )
                    self._emit_log_event(event)
                    
                    if self._current_task_id:
                        update = TaskUpdate(
                            task_id=self._current_task_id,
                            status=TaskStatus.COMPLETED,
                            step_number=self._current_step,
                            total_steps=None,
                            current_action=None,
                            result=last_result.extracted_content,
                            error=None,
                            timestamp=datetime.now()
                        )
                        self._emit_task_update(update)


class LogCaptureHandler(logging.Handler):
    """Custom logging handler to capture Browser AI logs"""
    
    def __init__(self, event_listener: LogEventListener):
        super().__init__()
        self.event_listener = event_listener
        self.setFormatter(logging.Formatter('%(message)s'))
    
    def emit(self, record):
        """Emit log record as LogEvent"""
        try:
            # Map logging levels to our LogLevel enum
            level_mapping = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                35: LogLevel.RESULT,  # Custom RESULT level
            }
            
            level = level_mapping.get(record.levelno, LogLevel.INFO)
            
            # Extract step number from message if present
            step_number = None
            message = self.format(record)
            
            # Look for step pattern in message
            if "Step " in message:
                try:
                    step_part = message.split("Step ")[1].split(":")[0].split(" ")[0]
                    step_number = int(step_part)
                except (IndexError, ValueError):
                    pass
            
            # Create log event
            event = LogEvent(
                timestamp=datetime.fromtimestamp(record.created),
                level=level,
                message=message,
                source=record.name.replace('browser_ai.', ''),
                step_number=step_number,
                task_status=self.event_listener._task_status,
                metadata={
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
            )
            
            self.event_listener._emit_log_event(event)
            
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Error in log capture handler: {e}")