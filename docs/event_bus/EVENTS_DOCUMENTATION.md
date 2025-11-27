# Browser.AI Events Documentation

This document describes all events available in the Browser.AI event system. Events are organized by topic and can be used to track, monitor, and respond to various scenarios throughout the system.

## Event Topics

- **agent**: Agent lifecycle and execution events
- **browser**: Browser and page navigation events
- **dom**: DOM tree processing events
- **controller**: Action registration and execution events
- **llm**: Language model interaction events
- **messages**: Message history and conversation management events
- **validation**: Output and parameter validation events
- **planning**: Task planning and plan updates events
- **state**: State snapshots and memory management events
- **error**: Error handling and recovery events
- **metrics**: Performance monitoring and resource tracking events
- **user_interaction**: User input and help request events
- **extension**: Browser extension and WebSocket events

## Agent Events (topic: "agent")

### AgentStartedEvent
Emitted when an agent starts executing a task.
- **Fields**: `task`, `agent_id`, `use_vision`

### AgentStepStartedEvent
Emitted when an agent step begins.
- **Fields**: `step_number`, `agent_id`

### AgentStepCompletedEvent
Emitted when an agent step completes successfully.
- **Fields**: `step_number`, `agent_id`, `actions_taken`, `result`

### AgentStepFailedEvent
Emitted when an agent step fails.
- **Fields**: `step_number`, `agent_id`, `error_message`, `error_type`

### AgentCompletedEvent
Emitted when an agent completes its task.
- **Fields**: `task`, `agent_id`, `total_steps`, `success`, `final_result`

### AgentFailedEvent
Emitted when an agent fails to complete its task.
- **Fields**: `task`, `agent_id`, `error_message`, `total_steps`

### AgentRetryEvent
Emitted when an agent retries after a failure.
- **Fields**: `retry_count`, `max_retries`, `agent_id`, `reason`

## Browser Events (topic: "browser")

### BrowserInitializedEvent
Emitted when a browser instance is initialized.
- **Fields**: `browser_id`, `headless`, `disable_security`

### BrowserClosedEvent
Emitted when a browser instance is closed.
- **Fields**: `browser_id`

### BrowserContextCreatedEvent
Emitted when a new browser context is created.
- **Fields**: `context_id`, `browser_id`

### BrowserContextClosedEvent
Emitted when a browser context is closed.
- **Fields**: `context_id`

### PageNavigationStartedEvent
Emitted when page navigation starts.
- **Fields**: `url`, `context_id`

### PageNavigationCompletedEvent
Emitted when page navigation completes.
- **Fields**: `url`, `context_id`, `load_time_ms`

### PageNavigationFailedEvent
Emitted when page navigation fails.
- **Fields**: `url`, `context_id`, `error_message`

### PageLoadedEvent
Emitted when a page is fully loaded.
- **Fields**: `url`, `context_id`, `title`

### TabCreatedEvent
Emitted when a new tab is created.
- **Fields**: `tab_index`, `context_id`

### TabSwitchedEvent
Emitted when switching between tabs.
- **Fields**: `from_tab_index`, `to_tab_index`, `context_id`

### TabClosedEvent
Emitted when a tab is closed.
- **Fields**: `tab_index`, `context_id`

### ScreenshotCapturedEvent
Emitted when a screenshot is captured.
- **Fields**: `context_id`, `screenshot_size_bytes`

## DOM Events (topic: "dom")

### DOMTreeBuiltEvent
Emitted when DOM tree is built.
- **Fields**: `total_elements`, `clickable_elements`, `context_id`

### DOMElementHighlightedEvent
Emitted when DOM elements are highlighted.
- **Fields**: `highlighted_count`, `context_id`

### DOMProcessingStartedEvent
Emitted when DOM processing starts.
- **Fields**: `context_id`

### DOMProcessingCompletedEvent
Emitted when DOM processing completes.
- **Fields**: `context_id`, `processing_time_ms`

### DOMProcessingFailedEvent
Emitted when DOM processing fails.
- **Fields**: `context_id`, `error_message`

## Controller & Action Events (topic: "controller")

### ControllerInitializedEvent
Emitted when controller is initialized.
- **Fields**: `registered_actions`, `excluded_actions`

### ActionRegisteredEvent
Emitted when a custom action is registered.
- **Fields**: `action_name`, `description`

### ActionExecutionStartedEvent
Emitted when an action starts executing.
- **Fields**: `action_name`, `action_params`, `step_number`

### ActionExecutionCompletedEvent
Emitted when an action completes successfully.
- **Fields**: `action_name`, `action_params`, `result`, `is_done`, `execution_time_ms`

### ActionExecutionFailedEvent
Emitted when an action execution fails.
- **Fields**: `action_name`, `action_params`, `error_message`, `error_type`

### MultipleActionsExecutedEvent
Emitted when multiple actions are executed in one step.
- **Fields**: `actions_count`, `action_names`, `step_number`

## LLM Events (topic: "llm")

### LLMRequestStartedEvent
Emitted when an LLM request starts.
- **Fields**: `model_name`, `purpose`, `input_tokens_estimate`
- **Purpose values**: 'action', 'planning', 'validation', etc.

### LLMRequestCompletedEvent
Emitted when an LLM request completes.
- **Fields**: `model_name`, `purpose`, `input_tokens`, `output_tokens`, `total_tokens`, `response_time_ms`

### LLMRequestFailedEvent
Emitted when an LLM request fails.
- **Fields**: `model_name`, `purpose`, `error_message`, `error_type`
- **Error types**: 'rate_limit', 'timeout', 'validation', etc.

### LLMRateLimitEvent
Emitted when LLM rate limit is hit.
- **Fields**: `model_name`, `retry_after_seconds`

### LLMTokenLimitWarningEvent
Emitted when approaching token limits.
- **Fields**: `current_tokens`, `max_tokens`, `utilization_percent`

## Message Manager Events (topic: "messages")

### MessageAddedEvent
Emitted when a message is added to history.
- **Fields**: `message_type`, `message_length`, `total_messages`, `total_tokens`
- **Message types**: 'system', 'human', 'ai', 'tool'

### MessageTrimmedEvent
Emitted when messages are trimmed due to token limits.
- **Fields**: `messages_removed`, `tokens_before`, `tokens_after`, `reason`

### MessageHistoryClearedEvent
Emitted when message history is cleared.
- **Fields**: `messages_count`, `reason`

### ConversationSavedEvent
Emitted when conversation is saved to file.
- **Fields**: `file_path`, `messages_count`, `file_size_bytes`

### ToolCallCreatedEvent
Emitted when a tool call message is created.
- **Fields**: `tool_call_id`, `tool_name`, `arguments`

### ToolResponseReceivedEvent
Emitted when a tool response is received.
- **Fields**: `tool_call_id`, `tool_name`, `response_length`, `success`

## Validation Events (topic: "validation")

### OutputValidationStartedEvent
Emitted when output validation starts.
- **Fields**: `output_model`

### OutputValidationSuccessEvent
Emitted when output validation succeeds.
- **Fields**: `output_model`

### OutputValidationFailedEvent
Emitted when output validation fails.
- **Fields**: `output_model`, `validation_errors`

### ActionParamsValidationFailedEvent
Emitted when action parameters fail validation.
- **Fields**: `action_name`, `validation_errors`

## Planning Events (topic: "planning")

### PlanningStartedEvent
Emitted when planning phase starts.
- **Fields**: `task`, `agent_id`

### PlanningCompletedEvent
Emitted when planning phase completes.
- **Fields**: `plan_steps`, `agent_id`

### PlanningFailedEvent
Emitted when planning phase fails.
- **Fields**: `error_message`, `agent_id`

### PlanUpdatedEvent
Emitted when plan is updated during execution.
- **Fields**: `reason`, `updated_steps`, `agent_id`

## State & Memory Events (topic: "state")

### StateSnapshotCreatedEvent
Emitted when a state snapshot is created.
- **Fields**: `step_number`, `state_type`, `snapshot_size_bytes`
- **State types**: 'browser', 'agent', 'dom'

### StateRestoredEvent
Emitted when state is restored from a snapshot.
- **Fields**: `step_number`, `state_type`

### MemoryUpdatedEvent
Emitted when agent memory is updated.
- **Fields**: `memory_content`, `step_number`

### HistoryRecordedEvent
Emitted when history is recorded.
- **Fields**: `record_type`, `step_number`
- **Record types**: 'agent_step', 'browser_state', 'action'

## Error & Recovery Events (topic: "error")

### ErrorOccurredEvent
Emitted when a general error occurs.
- **Fields**: `error_type`, `error_message`, `component`, `recoverable`
- **Components**: 'agent', 'browser', 'controller', 'dom', 'llm'

### RecoveryAttemptedEvent
Emitted when recovery is attempted.
- **Fields**: `error_type`, `recovery_strategy`, `attempt_number`

### RecoverySuccessEvent
Emitted when recovery succeeds.
- **Fields**: `error_type`, `recovery_strategy`, `attempts_taken`

### RecoveryFailedEvent
Emitted when recovery fails.
- **Fields**: `error_type`, `recovery_strategy`, `final_error`

## Performance & Metrics Events (topic: "metrics")

### PerformanceMetricEvent
Emitted for performance metrics.
- **Fields**: `metric_name`, `metric_value`, `metric_unit`, `component`
- **Metric units**: 'ms', 'bytes', 'count', etc.

### ResourceUsageEvent
Emitted for resource usage tracking.
- **Fields**: `memory_mb`, `cpu_percent`, `active_pages`, `active_contexts`

### StepDurationEvent
Emitted when tracking step execution time.
- **Fields**: `step_number`, `duration_ms`, `actions_count`

### TotalExecutionTimeEvent
Emitted when tracking total execution time.
- **Fields**: `total_duration_ms`, `total_steps`, `success`

## User Interaction Events (topic: "user_interaction")

### UserHelpRequestedEvent
Emitted when agent requests user help.
- **Fields**: `request_message`, `step_number`

### UserInputReceivedEvent
Emitted when user provides input.
- **Fields**: `input_type`, `input_value`
- **Input types**: 'text', 'confirmation', 'selection'

### UserConfirmationRequestedEvent
Emitted when requesting user confirmation.
- **Fields**: `confirmation_message`, `action_to_confirm`

## Extension & Integration Events (topic: "extension")

### ExtensionConnectedEvent
Emitted when browser extension connects.
- **Fields**: `extension_id`, `extension_version`

### ExtensionDisconnectedEvent
Emitted when browser extension disconnects.
- **Fields**: `extension_id`, `reason`

### CDPConnectionEstablishedEvent
Emitted when CDP WebSocket connection is established.
- **Fields**: `websocket_url`

### CDPConnectionClosedEvent
Emitted when CDP WebSocket connection closes.
- **Fields**: `reason`

### WebSocketMessageReceivedEvent
Emitted when WebSocket message is received.
- **Fields**: `message_type`, `message_size_bytes`

### WebSocketMessageSentEvent
Emitted when WebSocket message is sent.
- **Fields**: `message_type`, `message_size_bytes`

## Usage Examples

### Publishing Events

```python
from browser_ai.event_bus.core import EventManager
from browser_ai.event_bus.events import AgentStartedEvent, ActionExecutionCompletedEvent

# Get the event manager singleton
event_manager = EventManager()

# Publish an agent started event
event = AgentStartedEvent(
    task="Search for products on Amazon",
    agent_id="agent_123",
    use_vision=True
)
await event_manager.publish_async("agent", event)

# Publish an action completed event
action_event = ActionExecutionCompletedEvent(
    action_name="search_google",
    action_params={"query": "best laptops 2025"},
    result="Search completed successfully",
    is_done=False,
    execution_time_ms=1250.5
)
event_manager.publish("controller", action_event)
```

### Subscribing to Events

```python
from browser_ai.event_bus.core import EventHandler, EventManager
from browser_ai.event_bus.events import BaseEvent, AgentStepCompletedEvent

class MyCustomHandler(EventHandler):
    def handle(self, event: BaseEvent):
        if isinstance(event, AgentStepCompletedEvent):
            print(f"Step {event.step_number} completed with {len(event.actions_taken)} actions")

# Subscribe to agent events
event_manager = EventManager()
handler = MyCustomHandler()
event_manager.subscribe("agent", handler)
```

### Async Event Handler

```python
from browser_ai.event_bus.core import EventHandler
from browser_ai.event_bus.events import BaseEvent, LLMRequestCompletedEvent

class LLMMetricsHandler(EventHandler):
    async def handle(self, event: BaseEvent):
        if isinstance(event, LLMRequestCompletedEvent):
            # Save metrics to database
            await self.save_metrics({
                'model': event.model_name,
                'tokens': event.total_tokens,
                'time': event.response_time_ms
            })
    
    async def save_metrics(self, data):
        # Your async database operation
        pass
```

## Event Lifecycle

1. **Creation**: Event is instantiated with required data
2. **Publishing**: Event is published to a specific topic via `EventManager`
3. **Distribution**: All handlers subscribed to that topic receive the event
4. **Processing**: Each handler processes the event (sync or async)
5. **Completion**: Event processing completes

## Best Practices

1. **Use appropriate topics**: Always publish events to their designated topic
2. **Include context**: Provide context_id, agent_id, etc. when available
3. **Timestamp**: All events automatically include a timestamp
4. **Error handling**: Use specific error events rather than generic ones
5. **Performance**: Consider async handlers for I/O operations
6. **Filtering**: Handlers should check event type before processing
7. **Documentation**: Document custom events if you extend the system

## Event Flow Examples

### Typical Agent Execution Flow

```
AgentStartedEvent
  → PlanningStartedEvent
  → PlanningCompletedEvent
  → AgentStepStartedEvent
    → DOMProcessingStartedEvent
    → DOMTreeBuiltEvent
    → DOMProcessingCompletedEvent
    → LLMRequestStartedEvent
    → LLMRequestCompletedEvent
    → ActionExecutionStartedEvent
    → PageNavigationStartedEvent
    → PageNavigationCompletedEvent
    → ActionExecutionCompletedEvent
  → AgentStepCompletedEvent
  → AgentCompletedEvent
```

### Error Recovery Flow

```
ActionExecutionFailedEvent
  → ErrorOccurredEvent
  → RecoveryAttemptedEvent
  → RecoverySuccessEvent
  → ActionExecutionStartedEvent (retry)
  → ActionExecutionCompletedEvent
```

### Browser Navigation Flow

```
PageNavigationStartedEvent
  → PageLoadedEvent
  → DOMProcessingStartedEvent
  → DOMTreeBuiltEvent
  → DOMElementHighlightedEvent
  → DOMProcessingCompletedEvent
  → ScreenshotCapturedEvent
  → PageNavigationCompletedEvent
```
