"""
Browser.AI Event Bus - Real-time Event Streaming System

A versatile, extensible, and loosely-coupled event streaming emitter
for real-time logging, status updates, LLM outputs, and agent execution
tracking. Designed for UI integration and various subscriber levels.

Usage:
    from browser_ai.event_bus import emit, emit_async, subscribe, EventLevel
    from browser_ai.event_bus import AgentStartedEvent, AgentCompletedEvent

    # Subscribe to events
    subscribe("agent", my_handler)

    # Emit events (sync or async)
    emit(AgentStartedEvent(task="my task"))
    await emit_async(AgentCompletedEvent(task="my task", success=True, total_steps=5))
"""

from browser_ai.event_bus.core import EventHandler, EventManager
from browser_ai.event_bus.emitter import (
    AsyncEventHandler,
    EventLevel,
    FilteredEventHandler,
    StreamingEventHandler,
    emit,
    emit_async,
    get_event_manager,
    subscribe,
    unsubscribe,
)
from browser_ai.event_bus.events import (
    # Base
    BaseEvent,
    # Agent Events
    AgentCompletedEvent,
    AgentFailedEvent,
    AgentRetryEvent,
    AgentStartedEvent,
    AgentStepCompletedEvent,
    AgentStepFailedEvent,
    AgentStepStartedEvent,
    # Browser Events
    BrowserClosedEvent,
    BrowserContextClosedEvent,
    BrowserContextCreatedEvent,
    BrowserInitializedEvent,
    PageLoadedEvent,
    PageNavigationCompletedEvent,
    PageNavigationFailedEvent,
    PageNavigationStartedEvent,
    ScreenshotCapturedEvent,
    TabClosedEvent,
    TabCreatedEvent,
    TabSwitchedEvent,
    # Controller Events
    ActionExecutionCompletedEvent,
    ActionExecutionFailedEvent,
    ActionExecutionStartedEvent,
    ActionRegisteredEvent,
    ControllerInitializedEvent,
    MultipleActionsExecutedEvent,
    # DOM Events
    DOMElementHighlightedEvent,
    DOMProcessingCompletedEvent,
    DOMProcessingFailedEvent,
    DOMProcessingStartedEvent,
    DOMTreeBuiltEvent,
    # Error Events
    ErrorOccurredEvent,
    RecoveryAttemptedEvent,
    RecoveryFailedEvent,
    RecoverySuccessEvent,
    # LLM Events
    LLMRateLimitEvent,
    LLMRequestCompletedEvent,
    LLMRequestFailedEvent,
    LLMRequestStartedEvent,
    LLMTokenLimitWarningEvent,
    # Message Events
    ConversationSavedEvent,
    MessageAddedEvent,
    MessageHistoryClearedEvent,
    MessageTrimmedEvent,
    ToolCallCreatedEvent,
    ToolResponseReceivedEvent,
    # Metrics Events
    PerformanceMetricEvent,
    ResourceUsageEvent,
    StepDurationEvent,
    TotalExecutionTimeEvent,
    # Planning Events
    PlanningCompletedEvent,
    PlanningFailedEvent,
    PlanningStartedEvent,
    PlanUpdatedEvent,
    # State Events
    HistoryRecordedEvent,
    MemoryUpdatedEvent,
    StateRestoredEvent,
    StateSnapshotCreatedEvent,
    # User Interaction Events
    UserConfirmationRequestedEvent,
    UserHelpRequestedEvent,
    UserInputReceivedEvent,
    # Validation Events
    ActionParamsValidationFailedEvent,
    OutputValidationFailedEvent,
    OutputValidationStartedEvent,
    OutputValidationSuccessEvent,
    # Extension Events
    CDPConnectionClosedEvent,
    CDPConnectionEstablishedEvent,
    ExtensionConnectedEvent,
    ExtensionDisconnectedEvent,
    WebSocketMessageReceivedEvent,
    WebSocketMessageSentEvent,
)

__all__ = [
    # Core
    "EventManager",
    "EventHandler",
    "BaseEvent",
    # Emitter functions
    "emit",
    "emit_async",
    "subscribe",
    "unsubscribe",
    "get_event_manager",
    "EventLevel",
    # Handler classes
    "AsyncEventHandler",
    "StreamingEventHandler",
    "FilteredEventHandler",
    # Agent Events
    "AgentStartedEvent",
    "AgentStepStartedEvent",
    "AgentStepCompletedEvent",
    "AgentStepFailedEvent",
    "AgentCompletedEvent",
    "AgentFailedEvent",
    "AgentRetryEvent",
    # Browser Events
    "BrowserInitializedEvent",
    "BrowserClosedEvent",
    "BrowserContextCreatedEvent",
    "BrowserContextClosedEvent",
    "PageNavigationStartedEvent",
    "PageNavigationCompletedEvent",
    "PageNavigationFailedEvent",
    "PageLoadedEvent",
    "TabCreatedEvent",
    "TabSwitchedEvent",
    "TabClosedEvent",
    "ScreenshotCapturedEvent",
    # DOM Events
    "DOMTreeBuiltEvent",
    "DOMElementHighlightedEvent",
    "DOMProcessingStartedEvent",
    "DOMProcessingCompletedEvent",
    "DOMProcessingFailedEvent",
    # Controller Events
    "ControllerInitializedEvent",
    "ActionRegisteredEvent",
    "ActionExecutionStartedEvent",
    "ActionExecutionCompletedEvent",
    "ActionExecutionFailedEvent",
    "MultipleActionsExecutedEvent",
    # LLM Events
    "LLMRequestStartedEvent",
    "LLMRequestCompletedEvent",
    "LLMRequestFailedEvent",
    "LLMRateLimitEvent",
    "LLMTokenLimitWarningEvent",
    # Message Events
    "MessageAddedEvent",
    "MessageTrimmedEvent",
    "MessageHistoryClearedEvent",
    "ConversationSavedEvent",
    "ToolCallCreatedEvent",
    "ToolResponseReceivedEvent",
    # Validation Events
    "OutputValidationStartedEvent",
    "OutputValidationSuccessEvent",
    "OutputValidationFailedEvent",
    "ActionParamsValidationFailedEvent",
    # Planning Events
    "PlanningStartedEvent",
    "PlanningCompletedEvent",
    "PlanningFailedEvent",
    "PlanUpdatedEvent",
    # State Events
    "StateSnapshotCreatedEvent",
    "StateRestoredEvent",
    "MemoryUpdatedEvent",
    "HistoryRecordedEvent",
    # Error Events
    "ErrorOccurredEvent",
    "RecoveryAttemptedEvent",
    "RecoverySuccessEvent",
    "RecoveryFailedEvent",
    # Metrics Events
    "PerformanceMetricEvent",
    "ResourceUsageEvent",
    "StepDurationEvent",
    "TotalExecutionTimeEvent",
    # User Interaction Events
    "UserHelpRequestedEvent",
    "UserInputReceivedEvent",
    "UserConfirmationRequestedEvent",
    # Extension Events
    "ExtensionConnectedEvent",
    "ExtensionDisconnectedEvent",
    "CDPConnectionEstablishedEvent",
    "CDPConnectionClosedEvent",
    "WebSocketMessageReceivedEvent",
    "WebSocketMessageSentEvent",
]
