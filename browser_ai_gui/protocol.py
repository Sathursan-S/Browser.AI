"""
Browser.AI WebSocket Protocol

Shared protocol definitions for communication between the Chrome extension
and the Browser.AI server over WebSocket connections.

Namespace: /extension

This module defines the data structures and message formats used in the
WebSocket communication protocol to ensure consistency between the Python
server and TypeScript extension client.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union


# ============================================================================
# Enums
# ============================================================================


class LogLevel(Enum):
    """Log levels for events"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    RESULT = "RESULT"


class EventType(Enum):
    """Types of events that can be captured"""

    LOG = "log"
    AGENT_START = "agent_start"
    AGENT_STEP = "agent_step"
    AGENT_ACTION = "agent_action"
    AGENT_RESULT = "agent_result"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    AGENT_PAUSE = "agent_pause"
    AGENT_RESUME = "agent_resume"
    AGENT_STOP = "agent_stop"
    USER_HELP_NEEDED = "user_help_needed"


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class LogEvent:
    """
    Log event broadcast from server to clients

    Attributes:
        timestamp: ISO 8601 formatted timestamp
        level: Log level
        logger_name: Name of the logger that generated this event
        message: Log message content
        event_type: Type of event
        metadata: Optional additional metadata
    """

    timestamp: str
    level: str  # LogLevel value
    logger_name: str
    message: str
    event_type: str  # EventType value
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger_name": self.logger_name,
            "message": self.message,
            "event_type": self.event_type,
            "metadata": self.metadata or {},
        }


@dataclass
class TaskStatus:
    """
    Task status information

    Attributes:
        is_running: Whether a task is currently running
        current_task: Description of current task (None if no task)
        has_agent: Whether an agent instance exists
        is_paused: Whether the task is paused
        cdp_endpoint: CDP WebSocket endpoint being used
    """

    is_running: bool
    current_task: Optional[str]
    has_agent: bool
    is_paused: Optional[bool] = None
    cdp_endpoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "is_running": self.is_running,
            "current_task": self.current_task,
            "has_agent": self.has_agent,
            "is_paused": self.is_paused,
            "cdp_endpoint": self.cdp_endpoint,
        }


@dataclass
class ActionResult:
    """
    Generic action result

    Attributes:
        success: Whether the action succeeded
        message: Optional success message
        error: Optional error message
    """

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {"success": self.success}
        if self.message:
            result["message"] = self.message
        if self.error:
            result["error"] = self.error
        return result


# ============================================================================
# Client -> Server Event Payloads
# ============================================================================


@dataclass
class StartTaskPayload:
    """
    Event: start_task
    Request to start a new Browser.AI task

    Attributes:
        task: Task description
        cdp_endpoint: Optional CDP WebSocket endpoint
        is_extension: Flag to indicate extension mode
    """

    task: str
    cdp_endpoint: Optional[str] = None
    is_extension: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StartTaskPayload":
        """Create from dictionary"""
        return cls(
            task=data.get("task", ""),
            cdp_endpoint=data.get("cdp_endpoint"),
            is_extension=data.get("is_extension"),
        )


# ============================================================================
# Server -> Client Event Payloads
# ============================================================================


@dataclass
class TaskStartedPayload:
    """
    Event: task_started
    Confirmation that task has started

    Attributes:
        message: Status message
        success: Whether task started successfully
        error: Optional error message
    """

    message: str
    success: Optional[bool] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {"message": self.message}
        if self.success is not None:
            result["success"] = self.success
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class ErrorPayload:
    """
    Event: error
    Error message from server

    Attributes:
        message: Error message
        details: Optional additional details
    """

    message: str
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {"message": self.message}
        if self.details:
            result["details"] = self.details
        return result


# ============================================================================
# Protocol Constants
# ============================================================================

WEBSOCKET_NAMESPACE = "/extension"
DEFAULT_SERVER_URL = "http://localhost:5000"
MAX_RECONNECTION_ATTEMPTS = 5
RECONNECTION_DELAY_MS = 1000
MAX_LOGS = 1000


# ============================================================================
# Helper Functions
# ============================================================================


def serialize_log_event(
    timestamp: datetime,
    level: Union[LogLevel, str],
    logger_name: str,
    message: str,
    event_type: Union[EventType, str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Serialize a log event for transmission

    Args:
        timestamp: Event timestamp
        level: Log level (enum or string)
        logger_name: Logger name
        message: Log message
        event_type: Event type (enum or string)
        metadata: Optional metadata

    Returns:
        Dictionary ready for JSON serialization
    """
    log_event = LogEvent(
        timestamp=(
            timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
        ),
        level=level.value if isinstance(level, LogLevel) else level,
        logger_name=logger_name,
        message=message,
        event_type=(
            event_type.value if isinstance(event_type, EventType) else event_type
        ),
        metadata=metadata,
    )
    return log_event.to_dict()


def create_task_status(
    is_running: bool,
    current_task: Optional[str] = None,
    has_agent: bool = False,
    is_paused: Optional[bool] = None,
    cdp_endpoint: Optional[str] = None,
) -> TaskStatus:
    """
    Create a task status object

    Args:
        is_running: Whether a task is running
        current_task: Current task description
        has_agent: Whether an agent exists
        is_paused: Whether the task is paused
        cdp_endpoint: CDP endpoint being used

    Returns:
        TaskStatus object
    """
    return TaskStatus(
        is_running=is_running,
        current_task=current_task,
        has_agent=has_agent,
        is_paused=is_paused,
        cdp_endpoint=cdp_endpoint,
    )


def create_action_result(
    success: bool, message: Optional[str] = None, error: Optional[str] = None
) -> ActionResult:
    """
    Create an action result object

    Args:
        success: Whether the action succeeded
        message: Optional success message
        error: Optional error message

    Returns:
        ActionResult object
    """
    return ActionResult(success=success, message=message, error=error)


def create_error_payload(message: str, details: Optional[str] = None) -> ErrorPayload:
    """
    Create an error payload object

    Args:
        message: Error message
        details: Optional additional details

    Returns:
        ErrorPayload object
    """
    return ErrorPayload(message=message, details=details)
