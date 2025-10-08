"""
Event Schemas - Structured event definitions for Browser.AI

Defines all event types with their schemas following a consistent structure.
Each event is strongly typed and self-describing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EventCategory(Enum):
    """High-level event categories"""

    AGENT = "agent"  # Agent lifecycle and execution events
    TASK = "task"  # Task management events
    LLM = "llm"  # LLM interaction events
    BROWSER = "browser"  # Browser control events
    PROGRESS = "progress"  # Progress tracking events
    SYSTEM = "system"  # System-level events


class EventSeverity(Enum):
    """Event severity levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class BaseEvent:
    """
    Base class for all structured events
    
    All events inherit from this base and add their own specific fields.
    This ensures consistency and enables generic event handling.
    """

    # Core event metadata
    event_id: str
    event_type: str
    category: EventCategory
    timestamp: str  # ISO 8601 format
    severity: EventSeverity = EventSeverity.INFO

    # Contextual information
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "category": self.category.value,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "metadata": self.metadata,
        }


# ============================================================================
# Agent Events
# ============================================================================


@dataclass
class AgentStartEvent(BaseEvent):
    """Event emitted when an agent starts a task"""

    task_description: str = ""
    agent_id: str = ""
    configuration: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = "agent.start"
        self.category = EventCategory.AGENT

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "task_description": self.task_description,
                "agent_id": self.agent_id,
                "configuration": self.configuration,
            }
        )
        return base


@dataclass
class AgentStepEvent(BaseEvent):
    """Event emitted for each agent step/iteration"""

    step_number: int = 0
    step_description: str = ""
    agent_id: str = ""
    total_steps: Optional[int] = None

    def __post_init__(self):
        self.event_type = "agent.step"
        self.category = EventCategory.AGENT

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "step_number": self.step_number,
                "step_description": self.step_description,
                "agent_id": self.agent_id,
                "total_steps": self.total_steps,
            }
        )
        return base


@dataclass
class AgentActionEvent(BaseEvent):
    """Event emitted when agent performs an action"""

    action_type: str = ""
    action_description: str = ""
    agent_id: str = ""
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    action_result: Optional[str] = None

    def __post_init__(self):
        self.event_type = "agent.action"
        self.category = EventCategory.AGENT

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "action_type": self.action_type,
                "action_description": self.action_description,
                "agent_id": self.agent_id,
                "action_parameters": self.action_parameters,
                "action_result": self.action_result,
            }
        )
        return base


@dataclass
class AgentProgressEvent(BaseEvent):
    """Event emitted to report agent progress"""

    agent_id: str = ""
    progress_percentage: float = 0.0  # 0.0 to 100.0
    current_step: int = 0
    total_steps: Optional[int] = None
    status_message: Optional[str] = None

    def __post_init__(self):
        self.event_type = "agent.progress"
        self.category = EventCategory.PROGRESS

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "progress_percentage": self.progress_percentage,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "status_message": self.status_message,
            }
        )
        return base


@dataclass
class AgentStateEvent(BaseEvent):
    """Event emitted when agent state changes"""

    agent_id: str = ""
    old_state: str = ""
    new_state: str = ""
    state_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = "agent.state_change"
        self.category = EventCategory.AGENT

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "old_state": self.old_state,
                "new_state": self.new_state,
                "state_data": self.state_data,
            }
        )
        return base


@dataclass
class AgentCompleteEvent(BaseEvent):
    """Event emitted when agent completes a task"""

    agent_id: str = ""
    success: bool = False
    result: Optional[str] = None
    execution_time_ms: Optional[float] = None
    steps_executed: Optional[int] = None

    def __post_init__(self):
        self.event_type = "agent.complete"
        self.category = EventCategory.AGENT
        self.severity = EventSeverity.INFO if self.success else EventSeverity.WARNING

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "success": self.success,
                "result": self.result,
                "execution_time_ms": self.execution_time_ms,
                "steps_executed": self.steps_executed,
            }
        )
        return base


@dataclass
class AgentErrorEvent(BaseEvent):
    """Event emitted when agent encounters an error"""

    agent_id: str = ""
    error_type: str = ""
    error_message: str = ""
    error_details: Optional[str] = None
    recoverable: bool = False

    def __post_init__(self):
        self.event_type = "agent.error"
        self.category = EventCategory.AGENT
        self.severity = EventSeverity.ERROR

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "error_type": self.error_type,
                "error_message": self.error_message,
                "error_details": self.error_details,
                "recoverable": self.recoverable,
            }
        )
        return base


# ============================================================================
# LLM Events
# ============================================================================


@dataclass
class LLMOutputEvent(BaseEvent):
    """Event emitted for LLM interactions"""

    agent_id: str = ""
    llm_provider: str = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_name: Optional[str] = None
    response_preview: Optional[str] = None  # First 200 chars
    latency_ms: Optional[float] = None

    def __post_init__(self):
        self.event_type = "llm.output"
        self.category = EventCategory.LLM

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "llm_provider": self.llm_provider,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "model_name": self.model_name,
                "response_preview": self.response_preview,
                "latency_ms": self.latency_ms,
            }
        )
        return base


# ============================================================================
# Task Events
# ============================================================================


@dataclass
class TaskStateChangeEvent(BaseEvent):
    """Event emitted when task state changes"""

    task_description: str = ""
    old_state: str = ""
    new_state: str = ""
    agent_id: Optional[str] = None

    def __post_init__(self):
        self.event_type = "task.state_change"
        self.category = EventCategory.TASK

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "task_description": self.task_description,
                "old_state": self.old_state,
                "new_state": self.new_state,
                "agent_id": self.agent_id,
            }
        )
        return base
