"""
Event Bridge - Integration between new event system and existing components

Provides backward compatibility and migration path from the old log-based
event system to the new structured event system.
"""

import logging
from typing import Optional

from .emitter import EventEmitter, create_event_id, create_timestamp
from .schemas import (
    AgentActionEvent,
    AgentCompleteEvent,
    AgentErrorEvent,
    AgentStartEvent,
    AgentStepEvent,
    BaseEvent,
    EventCategory,
    EventSeverity,
    TaskStateChangeEvent,
)
from .transport import EventTransport
from ..protocol import EventType, LogEvent, LogLevel

logger = logging.getLogger(__name__)


class EventBridge:
    """
    Bridges between old event_adapter and new structured event system
    
    Provides migration utilities and backward compatibility.
    """

    def __init__(self, emitter: EventEmitter, transport: Optional[EventTransport] = None):
        self.emitter = emitter
        self.transport = transport
        
        # Subscribe emitter to transport
        if transport:
            self.emitter.subscribe(self._forward_to_transport)
    
    def _forward_to_transport(self, event: BaseEvent) -> None:
        """Forward structured events to transport layer"""
        if self.transport:
            self.transport.send(event)
    
    def convert_log_event_to_structured(self, log_event: LogEvent) -> Optional[BaseEvent]:
        """
        Convert old LogEvent to new structured event
        
        Args:
            log_event: Old-style log event
            
        Returns:
            New structured event or None if conversion not applicable
        """
        # Map log level to severity
        severity_map = {
            "DEBUG": EventSeverity.DEBUG,
            "INFO": EventSeverity.INFO,
            "WARNING": EventSeverity.WARNING,
            "ERROR": EventSeverity.ERROR,
            "RESULT": EventSeverity.INFO,
        }
        severity = severity_map.get(log_event.level, EventSeverity.INFO)
        
        # Common fields
        event_id = create_event_id()
        timestamp = log_event.timestamp
        
        # Convert based on event type
        event_type_str = log_event.event_type
        
        if event_type_str == "agent_start":
            return AgentStartEvent(
                event_id=event_id,
                event_type="agent.start",
                category=EventCategory.AGENT,
                timestamp=timestamp,
                severity=severity,
                task_description=log_event.message,
                agent_id=log_event.metadata.get("agent_id", "unknown"),
                metadata=log_event.metadata,
            )
        
        elif event_type_str == "agent_step":
            return AgentStepEvent(
                event_id=event_id,
                event_type="agent.step",
                category=EventCategory.AGENT,
                timestamp=timestamp,
                severity=severity,
                step_number=log_event.metadata.get("step_number", 0),
                step_description=log_event.message,
                agent_id=log_event.metadata.get("agent_id", "unknown"),
                metadata=log_event.metadata,
            )
        
        elif event_type_str == "agent_action":
            return AgentActionEvent(
                event_id=event_id,
                event_type="agent.action",
                category=EventCategory.AGENT,
                timestamp=timestamp,
                severity=severity,
                action_type=log_event.metadata.get("action_type", "unknown"),
                action_description=log_event.message,
                agent_id=log_event.metadata.get("agent_id", "unknown"),
                metadata=log_event.metadata,
            )
        
        elif event_type_str == "agent_complete":
            return AgentCompleteEvent(
                event_id=event_id,
                event_type="agent.complete",
                category=EventCategory.AGENT,
                timestamp=timestamp,
                severity=severity,
                agent_id=log_event.metadata.get("agent_id", "unknown"),
                success=True,
                result=log_event.message,
                metadata=log_event.metadata,
            )
        
        elif event_type_str == "agent_error":
            return AgentErrorEvent(
                event_id=event_id,
                event_type="agent.error",
                category=EventCategory.AGENT,
                timestamp=timestamp,
                severity=EventSeverity.ERROR,
                agent_id=log_event.metadata.get("agent_id", "unknown"),
                error_type=log_event.metadata.get("error_type", "unknown"),
                error_message=log_event.message,
                metadata=log_event.metadata,
            )
        
        # Return None for event types we don't convert
        return None
    
    def emit_structured_event(self, event: BaseEvent) -> None:
        """
        Emit a structured event through the emitter
        
        Args:
            event: Structured event to emit
        """
        self.emitter.emit(event)
    
    def create_agent_start_event(
        self,
        task_description: str,
        agent_id: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        configuration: Optional[dict] = None,
    ) -> AgentStartEvent:
        """Helper to create agent start event"""
        return AgentStartEvent(
            event_id=create_event_id(),
            event_type="agent.start",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            severity=EventSeverity.INFO,
            session_id=session_id,
            task_id=task_id,
            task_description=task_description,
            agent_id=agent_id,
            configuration=configuration or {},
        )
    
    def create_agent_complete_event(
        self,
        agent_id: str,
        success: bool,
        result: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        steps_executed: Optional[int] = None,
    ) -> AgentCompleteEvent:
        """Helper to create agent complete event"""
        return AgentCompleteEvent(
            event_id=create_event_id(),
            event_type="agent.complete",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            severity=EventSeverity.INFO if success else EventSeverity.WARNING,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            success=success,
            result=result,
            execution_time_ms=execution_time_ms,
            steps_executed=steps_executed,
        )
    
    def create_agent_error_event(
        self,
        agent_id: str,
        error_type: str,
        error_message: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        error_details: Optional[str] = None,
        recoverable: bool = False,
    ) -> AgentErrorEvent:
        """Helper to create agent error event"""
        return AgentErrorEvent(
            event_id=create_event_id(),
            event_type="agent.error",
            category=EventCategory.AGENT,
            timestamp=create_timestamp(),
            severity=EventSeverity.ERROR,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            error_type=error_type,
            error_message=error_message,
            error_details=error_details,
            recoverable=recoverable,
        )
    
    def create_task_state_change_event(
        self,
        task_description: str,
        old_state: str,
        new_state: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> TaskStateChangeEvent:
        """Helper to create task state change event"""
        return TaskStateChangeEvent(
            event_id=create_event_id(),
            event_type="task.state_change",
            category=EventCategory.TASK,
            timestamp=create_timestamp(),
            severity=EventSeverity.INFO,
            session_id=session_id,
            task_id=task_id,
            task_description=task_description,
            old_state=old_state,
            new_state=new_state,
            agent_id=agent_id,
        )
