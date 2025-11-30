import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """
    Base model for all events, providing common fields like a timestamp.
    Each specific event must define its own topic and name.
    """

    topic: str
    name: str
    timestamp: float = Field(default_factory=time.time)


# ============================================================================
# AGENT EVENTS
# ============================================================================


class AgentStartedEvent(BaseEvent):
    """Emitted when an agent starts executing a task"""

    topic: str = "agent"
    name: str = "agent_started"
    task: str
    agent_id: Optional[str] = None
    use_vision: bool = True


class AgentStepStartedEvent(BaseEvent):
    """Emitted when an agent step begins"""

    topic: str = "agent"
    name: str = "step_started"
    step_number: int
    agent_id: Optional[str] = None


class AgentStepCompletedEvent(BaseEvent):
    """Emitted when an agent step completes successfully"""

    topic: str = "agent"
    name: str = "step_completed"
    step_number: int
    agent_id: Optional[str] = None
    actions_taken: List[Dict[str, Any]]
    result: Optional[str] = None


class AgentStepFailedEvent(BaseEvent):
    """Emitted when an agent step fails"""

    topic: str = "agent"
    name: str = "step_failed"
    step_number: int
    agent_id: Optional[str] = None
    error_message: str
    error_type: str


class AgentCompletedEvent(BaseEvent):
    """Emitted when an agent completes its task"""

    topic: str = "agent"
    name: str = "agent_completed"
    task: str
    agent_id: Optional[str] = None
    total_steps: int
    success: bool
    final_result: Optional[str] = None


class AgentFailedEvent(BaseEvent):
    """Emitted when an agent fails to complete its task"""

    topic: str = "agent"
    name: str = "agent_failed"
    task: str
    agent_id: Optional[str] = None
    error_message: str
    total_steps: int


class AgentRetryEvent(BaseEvent):
    """Emitted when an agent retries after a failure"""

    topic: str = "agent"
    name: str = "agent_retry"
    retry_count: int
    max_retries: int
    agent_id: Optional[str] = None
    reason: str


# ============================================================================
# BROWSER EVENTS
# ============================================================================


class BrowserInitializedEvent(BaseEvent):
    """Emitted when a browser instance is initialized"""

    topic: str = "browser"
    name: str = "browser_initialized"
    browser_id: Optional[str] = None
    headless: bool = False
    disable_security: bool = True


class BrowserClosedEvent(BaseEvent):
    """Emitted when a browser instance is closed"""

    topic: str = "browser"
    name: str = "browser_closed"
    browser_id: Optional[str] = None


class BrowserContextCreatedEvent(BaseEvent):
    """Emitted when a new browser context is created"""

    topic: str = "browser"
    name: str = "context_created"
    context_id: Optional[str] = None
    browser_id: Optional[str] = None


class BrowserContextClosedEvent(BaseEvent):
    """Emitted when a browser context is closed"""

    topic: str = "browser"
    name: str = "context_closed"
    context_id: Optional[str] = None


class PageNavigationStartedEvent(BaseEvent):
    """Emitted when page navigation starts"""

    topic: str = "browser"
    name: str = "navigation_started"
    url: str
    context_id: Optional[str] = None


class PageNavigationCompletedEvent(BaseEvent):
    """Emitted when page navigation completes"""

    topic: str = "browser"
    name: str = "navigation_completed"
    url: str
    context_id: Optional[str] = None
    load_time_ms: Optional[float] = None


class PageNavigationFailedEvent(BaseEvent):
    """Emitted when page navigation fails"""

    topic: str = "browser"
    name: str = "navigation_failed"
    url: str
    context_id: Optional[str] = None
    error_message: str


class PageLoadedEvent(BaseEvent):
    """Emitted when a page is fully loaded"""

    topic: str = "browser"
    name: str = "page_loaded"
    url: str
    context_id: Optional[str] = None
    title: Optional[str] = None


class TabCreatedEvent(BaseEvent):
    """Emitted when a new tab is created"""

    topic: str = "browser"
    name: str = "tab_created"
    tab_index: int
    context_id: Optional[str] = None


class TabSwitchedEvent(BaseEvent):
    """Emitted when switching between tabs"""

    topic: str = "browser"
    name: str = "tab_switched"
    from_tab_index: int
    to_tab_index: int
    context_id: Optional[str] = None


class TabClosedEvent(BaseEvent):
    """Emitted when a tab is closed"""

    topic: str = "browser"
    name: str = "tab_closed"
    tab_index: int
    context_id: Optional[str] = None


class ScreenshotCapturedEvent(BaseEvent):
    """Emitted when a screenshot is captured"""

    topic: str = "browser"
    name: str = "screenshot_captured"
    context_id: Optional[str] = None
    screenshot_size_bytes: Optional[int] = None


# ============================================================================
# DOM EVENTS
# ============================================================================


class DOMTreeBuiltEvent(BaseEvent):
    """Emitted when DOM tree is built"""

    topic: str = "dom"
    name: str = "tree_built"
    total_elements: int
    clickable_elements: int
    context_id: Optional[str] = None


class DOMElementHighlightedEvent(BaseEvent):
    """Emitted when DOM elements are highlighted"""

    topic: str = "dom"
    name: str = "elements_highlighted"
    highlighted_count: int
    context_id: Optional[str] = None


class DOMProcessingStartedEvent(BaseEvent):
    """Emitted when DOM processing starts"""

    topic: str = "dom"
    name: str = "processing_started"
    context_id: Optional[str] = None


class DOMProcessingCompletedEvent(BaseEvent):
    """Emitted when DOM processing completes"""

    topic: str = "dom"
    name: str = "processing_completed"
    context_id: Optional[str] = None
    processing_time_ms: Optional[float] = None


class DOMProcessingFailedEvent(BaseEvent):
    """Emitted when DOM processing fails"""

    topic: str = "dom"
    name: str = "processing_failed"
    context_id: Optional[str] = None
    error_message: str


# ============================================================================
# CONTROLLER & ACTION EVENTS
# ============================================================================


class ControllerInitializedEvent(BaseEvent):
    """Emitted when controller is initialized"""

    topic: str = "controller"
    name: str = "controller_initialized"
    registered_actions: List[str]
    excluded_actions: List[str]


class ActionRegisteredEvent(BaseEvent):
    """Emitted when a custom action is registered"""

    topic: str = "controller"
    name: str = "action_registered"
    action_name: str
    description: str


class ActionExecutionStartedEvent(BaseEvent):
    """Emitted when an action starts executing"""

    topic: str = "controller"
    name: str = "action_started"
    action_name: str
    action_params: Dict[str, Any]
    step_number: Optional[int] = None


class ActionExecutionCompletedEvent(BaseEvent):
    """Emitted when an action completes successfully"""

    topic: str = "controller"
    name: str = "action_completed"
    action_name: str
    action_params: Dict[str, Any]
    result: Optional[str] = None
    is_done: bool = False
    execution_time_ms: Optional[float] = None


class ActionExecutionFailedEvent(BaseEvent):
    """Emitted when an action execution fails"""

    topic: str = "controller"
    name: str = "action_failed"
    action_name: str
    action_params: Dict[str, Any]
    error_message: str
    error_type: str


class MultipleActionsExecutedEvent(BaseEvent):
    """Emitted when multiple actions are executed in one step"""

    topic: str = "controller"
    name: str = "multiple_actions_executed"
    actions_count: int
    action_names: List[str]
    step_number: Optional[int] = None


# ============================================================================
# LLM EVENTS
# ============================================================================


class LLMRequestStartedEvent(BaseEvent):
    """Emitted when an LLM request starts"""

    topic: str = "llm"
    name: str = "request_started"
    model_name: Optional[str] = None
    purpose: str  # 'action', 'planning', 'validation', etc.
    input_tokens_estimate: Optional[int] = None


class LLMRequestCompletedEvent(BaseEvent):
    """Emitted when an LLM request completes"""

    topic: str = "llm"
    name: str = "request_completed"
    model_name: Optional[str] = None
    purpose: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    response_time_ms: Optional[float] = None


class LLMRequestFailedEvent(BaseEvent):
    """Emitted when an LLM request fails"""

    topic: str = "llm"
    name: str = "request_failed"
    model_name: Optional[str] = None
    purpose: str
    error_message: str
    error_type: str  # 'rate_limit', 'timeout', 'validation', etc.


class LLMRateLimitEvent(BaseEvent):
    """Emitted when LLM rate limit is hit"""

    topic: str = "llm"
    name: str = "rate_limit"
    model_name: Optional[str] = None
    retry_after_seconds: Optional[int] = None


class LLMTokenLimitWarningEvent(BaseEvent):
    """Emitted when approaching token limits"""

    topic: str = "llm"
    name: str = "token_limit_warning"
    current_tokens: int
    max_tokens: int
    utilization_percent: float


# ============================================================================
# MESSAGE MANAGER EVENTS
# ============================================================================


class MessageAddedEvent(BaseEvent):
    """Emitted when a message is added to history"""

    topic: str = "messages"
    name: str = "message_added"
    message_type: str  # 'system', 'human', 'ai', 'tool'
    message_length: int
    total_messages: int
    total_tokens: int


class MessageTrimmedEvent(BaseEvent):
    """Emitted when messages are trimmed due to token limits"""

    topic: str = "messages"
    name: str = "messages_trimmed"
    messages_removed: int
    tokens_before: int
    tokens_after: int
    reason: str


class MessageHistoryClearedEvent(BaseEvent):
    """Emitted when message history is cleared"""

    topic: str = "messages"
    name: str = "history_cleared"
    messages_count: int
    reason: str


class ConversationSavedEvent(BaseEvent):
    """Emitted when conversation is saved to file"""

    topic: str = "messages"
    name: str = "conversation_saved"
    file_path: str
    messages_count: int
    file_size_bytes: Optional[int] = None


class ToolCallCreatedEvent(BaseEvent):
    """Emitted when a tool call message is created"""

    topic: str = "messages"
    name: str = "tool_call_created"
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]


class ToolResponseReceivedEvent(BaseEvent):
    """Emitted when a tool response is received"""

    topic: str = "messages"
    name: str = "tool_response_received"
    tool_call_id: str
    tool_name: str
    response_length: int
    success: bool


# ============================================================================
# VALIDATION EVENTS
# ============================================================================


class OutputValidationStartedEvent(BaseEvent):
    """Emitted when output validation starts"""

    topic: str = "validation"
    name: str = "validation_started"
    output_model: Optional[str] = None


class OutputValidationSuccessEvent(BaseEvent):
    """Emitted when output validation succeeds"""

    topic: str = "validation"
    name: str = "validation_success"
    output_model: Optional[str] = None


class OutputValidationFailedEvent(BaseEvent):
    """Emitted when output validation fails"""

    topic: str = "validation"
    name: str = "validation_failed"
    output_model: Optional[str] = None
    validation_errors: List[str]


class ActionParamsValidationFailedEvent(BaseEvent):
    """Emitted when action parameters fail validation"""

    topic: str = "validation"
    name: str = "action_params_validation_failed"
    action_name: str
    validation_errors: List[str]


# ============================================================================
# PLANNING EVENTS
# ============================================================================


class PlanningStartedEvent(BaseEvent):
    """Emitted when planning phase starts"""

    topic: str = "planning"
    name: str = "planning_started"
    task: str
    agent_id: Optional[str] = None


class PlanningCompletedEvent(BaseEvent):
    """Emitted when planning phase completes"""

    topic: str = "planning"
    name: str = "planning_completed"
    plan_steps: List[str]
    agent_id: Optional[str] = None


class PlanningFailedEvent(BaseEvent):
    """Emitted when planning phase fails"""

    topic: str = "planning"
    name: str = "planning_failed"
    error_message: str
    agent_id: Optional[str] = None


class PlanUpdatedEvent(BaseEvent):
    """Emitted when plan is updated during execution"""

    topic: str = "planning"
    name: str = "plan_updated"
    reason: str
    updated_steps: List[str]
    agent_id: Optional[str] = None


# ============================================================================
# MEMORY & STATE EVENTS
# ============================================================================


class StateSnapshotCreatedEvent(BaseEvent):
    """Emitted when a state snapshot is created"""

    topic: str = "state"
    name: str = "snapshot_created"
    step_number: int
    state_type: str  # 'browser', 'agent', 'dom'
    snapshot_size_bytes: Optional[int] = None


class StateRestoredEvent(BaseEvent):
    """Emitted when state is restored from a snapshot"""

    topic: str = "state"
    name: str = "state_restored"
    step_number: int
    state_type: str


class MemoryUpdatedEvent(BaseEvent):
    """Emitted when agent memory is updated"""

    topic: str = "state"
    name: str = "memory_updated"
    memory_content: str
    step_number: int


class HistoryRecordedEvent(BaseEvent):
    """Emitted when history is recorded"""

    topic: str = "state"
    name: str = "history_recorded"
    record_type: str  # 'agent_step', 'browser_state', 'action'
    step_number: int


# ============================================================================
# ERROR & RECOVERY EVENTS
# ============================================================================


class ErrorOccurredEvent(BaseEvent):
    """Emitted when a general error occurs"""

    topic: str = "error"
    name: str = "error_occurred"
    error_type: str
    error_message: str
    component: str  # 'agent', 'browser', 'controller', 'dom', 'llm'
    recoverable: bool = True


class RecoveryAttemptedEvent(BaseEvent):
    """Emitted when recovery is attempted"""

    topic: str = "error"
    name: str = "recovery_attempted"
    error_type: str
    recovery_strategy: str
    attempt_number: int


class RecoverySuccessEvent(BaseEvent):
    """Emitted when recovery succeeds"""

    topic: str = "error"
    name: str = "recovery_success"
    error_type: str
    recovery_strategy: str
    attempts_taken: int


class RecoveryFailedEvent(BaseEvent):
    """Emitted when recovery fails"""

    topic: str = "error"
    name: str = "recovery_failed"
    error_type: str
    recovery_strategy: str
    final_error: str


# ============================================================================
# PERFORMANCE & METRICS EVENTS
# ============================================================================


class PerformanceMetricEvent(BaseEvent):
    """Emitted for performance metrics"""

    topic: str = "metrics"
    name: str = "performance_metric"
    metric_name: str
    metric_value: float
    metric_unit: str  # 'ms', 'bytes', 'count', etc.
    component: str


class ResourceUsageEvent(BaseEvent):
    """Emitted for resource usage tracking"""

    topic: str = "metrics"
    name: str = "resource_usage"
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    active_pages: Optional[int] = None
    active_contexts: Optional[int] = None


class StepDurationEvent(BaseEvent):
    """Emitted when tracking step execution time"""

    topic: str = "metrics"
    name: str = "step_duration"
    step_number: int
    duration_ms: float
    actions_count: int


class TotalExecutionTimeEvent(BaseEvent):
    """Emitted when tracking total execution time"""

    topic: str = "metrics"
    name: str = "total_execution_time"
    total_duration_ms: float
    total_steps: int
    success: bool


# ============================================================================
# USER INTERACTION EVENTS
# ============================================================================


class UserHelpRequestedEvent(BaseEvent):
    """Emitted when agent requests user help"""

    topic: str = "user_interaction"
    name: str = "help_requested"
    request_message: str
    step_number: int


class UserInputReceivedEvent(BaseEvent):
    """Emitted when user provides input"""

    topic: str = "user_interaction"
    name: str = "input_received"
    input_type: str  # 'text', 'confirmation', 'selection'
    input_value: str


class UserConfirmationRequestedEvent(BaseEvent):
    """Emitted when requesting user confirmation"""

    topic: str = "user_interaction"
    name: str = "confirmation_requested"
    confirmation_message: str
    action_to_confirm: str


# ============================================================================
# EXTENSION & INTEGRATION EVENTS
# ============================================================================


class ExtensionConnectedEvent(BaseEvent):
    """Emitted when browser extension connects"""

    topic: str = "extension"
    name: str = "extension_connected"
    extension_id: str
    extension_version: Optional[str] = None


class ExtensionDisconnectedEvent(BaseEvent):
    """Emitted when browser extension disconnects"""

    topic: str = "extension"
    name: str = "extension_disconnected"
    extension_id: str
    reason: Optional[str] = None


class CDPConnectionEstablishedEvent(BaseEvent):
    """Emitted when CDP WebSocket connection is established"""

    topic: str = "extension"
    name: str = "cdp_connected"
    websocket_url: str


class CDPConnectionClosedEvent(BaseEvent):
    """Emitted when CDP WebSocket connection closes"""

    topic: str = "extension"
    name: str = "cdp_disconnected"
    reason: Optional[str] = None


class WebSocketMessageReceivedEvent(BaseEvent):
    """Emitted when WebSocket message is received"""

    topic: str = "extension"
    name: str = "websocket_message_received"
    message_type: str
    message_size_bytes: int


class WebSocketMessageSentEvent(BaseEvent):
    """Emitted when WebSocket message is sent"""

    topic: str = "extension"
    name: str = "websocket_message_sent"
    message_type: str
    message_size_bytes: int
