# Event Integration Guide

This guide shows where to emit events in the Browser.AI codebase.

## Agent Service (`browser_ai/agent/service.py`)

### In `__init__` method:
```python
from browser_ai.event_bus.core import EventManager
from browser_ai.event_bus.events import AgentStartedEvent

# After initialization
event_manager = EventManager()
event = AgentStartedEvent(
    task=task,
    agent_id=str(id(self)),
    use_vision=use_vision
)
await event_manager.publish_async("agent", event)
```

### In `run` method (start):
```python
from browser_ai.event_bus.events import AgentStartedEvent

event = AgentStartedEvent(
    task=self.task,
    agent_id=str(id(self)),
    use_vision=self.use_vision
)
await self.event_manager.publish_async("agent", event)
```

### In `run` method (completion):
```python
from browser_ai.event_bus.events import AgentCompletedEvent

event = AgentCompletedEvent(
    task=self.task,
    agent_id=str(id(self)),
    total_steps=len(self.history),
    success=True,
    final_result=result
)
await self.event_manager.publish_async("agent", event)
```

### In `run` method (failure):
```python
from browser_ai.event_bus.events import AgentFailedEvent

event = AgentFailedEvent(
    task=self.task,
    agent_id=str(id(self)),
    error_message=str(error),
    total_steps=len(self.history)
)
await self.event_manager.publish_async("agent", event)
```

### In `step` method (start):
```python
from browser_ai.event_bus.events import AgentStepStartedEvent

event = AgentStepStartedEvent(
    step_number=len(self.history) + 1,
    agent_id=str(id(self))
)
await self.event_manager.publish_async("agent", event)
```

### In `step` method (completion):
```python
from browser_ai.event_bus.events import AgentStepCompletedEvent

event = AgentStepCompletedEvent(
    step_number=len(self.history),
    agent_id=str(id(self)),
    actions_taken=actions,
    result=result
)
await self.event_manager.publish_async("agent", event)
```

### In retry logic:
```python
from browser_ai.event_bus.events import AgentRetryEvent

event = AgentRetryEvent(
    retry_count=current_retry,
    max_retries=self.max_failures,
    agent_id=str(id(self)),
    reason=str(error)
)
await self.event_manager.publish_async("agent", event)
```

## Controller Service (`browser_ai/controller/service.py`)

### In `__init__` method:
```python
from browser_ai.event_bus.core import EventManager
from browser_ai.event_bus.events import ControllerInitializedEvent

event = ControllerInitializedEvent(
    registered_actions=list(self.registry.registry.keys()),
    excluded_actions=exclude_actions
)
EventManager().publish("controller", event)
```

### When registering custom actions:
```python
from browser_ai.event_bus.events import ActionRegisteredEvent

event = ActionRegisteredEvent(
    action_name=action_name,
    description=description
)
EventManager().publish("controller", event)
```

### In `act` method (action start):
```python
from browser_ai.event_bus.events import ActionExecutionStartedEvent

event = ActionExecutionStartedEvent(
    action_name=action_name,
    action_params=params.dict(),
    step_number=step_number
)
await EventManager().publish_async("controller", event)
```

### In `act` method (action completion):
```python
from browser_ai.event_bus.events import ActionExecutionCompletedEvent
import time

start_time = time.time()
# ... execute action ...
execution_time = (time.time() - start_time) * 1000

event = ActionExecutionCompletedEvent(
    action_name=action_name,
    action_params=params.dict(),
    result=result.extracted_content,
    is_done=result.is_done,
    execution_time_ms=execution_time
)
await EventManager().publish_async("controller", event)
```

### In `act` method (action failure):
```python
from browser_ai.event_bus.events import ActionExecutionFailedEvent

event = ActionExecutionFailedEvent(
    action_name=action_name,
    action_params=params.dict(),
    error_message=str(error),
    error_type=type(error).__name__
)
await EventManager().publish_async("controller", event)
```

### For multiple actions:
```python
from browser_ai.event_bus.events import MultipleActionsExecutedEvent

event = MultipleActionsExecutedEvent(
    actions_count=len(actions),
    action_names=[action.action_name for action in actions],
    step_number=step_number
)
await EventManager().publish_async("controller", event)
```

## Browser Service (`browser_ai/browser/browser.py`)

### In `_init` method:
```python
from browser_ai.event_bus.core import EventManager
from browser_ai.event_bus.events import BrowserInitializedEvent

event = BrowserInitializedEvent(
    browser_id=str(id(self)),
    headless=self.config.headless,
    disable_security=self.config.disable_security
)
await EventManager().publish_async("browser", event)
```

### In `close` method:
```python
from browser_ai.event_bus.events import BrowserClosedEvent

event = BrowserClosedEvent(
    browser_id=str(id(self))
)
await EventManager().publish_async("browser", event)
```

### In `new_context` method:
```python
from browser_ai.event_bus.events import BrowserContextCreatedEvent

event = BrowserContextCreatedEvent(
    context_id=str(id(context)),
    browser_id=str(id(self))
)
await EventManager().publish_async("browser", event)
```

## Browser Context (`browser_ai/browser/context.py`)

### In navigation methods (goto, etc.):
```python
from browser_ai.event_bus.events import (
    PageNavigationStartedEvent,
    PageNavigationCompletedEvent,
    PageNavigationFailedEvent
)
import time

# Before navigation
event = PageNavigationStartedEvent(
    url=url,
    context_id=str(id(self))
)
await EventManager().publish_async("browser", event)

start_time = time.time()
try:
    await page.goto(url)
    load_time = (time.time() - start_time) * 1000
    
    # After successful navigation
    event = PageNavigationCompletedEvent(
        url=url,
        context_id=str(id(self)),
        load_time_ms=load_time
    )
    await EventManager().publish_async("browser", event)
except Exception as e:
    # On navigation failure
    event = PageNavigationFailedEvent(
        url=url,
        context_id=str(id(self)),
        error_message=str(e)
    )
    await EventManager().publish_async("browser", event)
```

### When page loads:
```python
from browser_ai.event_bus.events import PageLoadedEvent

page = await self.get_current_page()
event = PageLoadedEvent(
    url=page.url,
    context_id=str(id(self)),
    title=await page.title()
)
await EventManager().publish_async("browser", event)
```

### Tab operations:
```python
from browser_ai.event_bus.events import (
    TabCreatedEvent,
    TabSwitchedEvent,
    TabClosedEvent
)

# Creating tab
event = TabCreatedEvent(
    tab_index=len(self._pages),
    context_id=str(id(self))
)
await EventManager().publish_async("browser", event)

# Switching tabs
event = TabSwitchedEvent(
    from_tab_index=current_index,
    to_tab_index=new_index,
    context_id=str(id(self))
)
await EventManager().publish_async("browser", event)

# Closing tab
event = TabClosedEvent(
    tab_index=index,
    context_id=str(id(self))
)
await EventManager().publish_async("browser", event)
```

### Taking screenshots:
```python
from browser_ai.event_bus.events import ScreenshotCapturedEvent

screenshot_bytes = await page.screenshot()
event = ScreenshotCapturedEvent(
    context_id=str(id(self)),
    screenshot_size_bytes=len(screenshot_bytes)
)
await EventManager().publish_async("browser", event)
```

## DOM Service (`browser_ai/dom/service.py`)

### In `get_clickable_elements` method:
```python
from browser_ai.event_bus.events import (
    DOMProcessingStartedEvent,
    DOMTreeBuiltEvent,
    DOMElementHighlightedEvent,
    DOMProcessingCompletedEvent,
    DOMProcessingFailedEvent
)
import time

# Start processing
event = DOMProcessingStartedEvent(
    context_id=context_id
)
await EventManager().publish_async("dom", event)

start_time = time.time()
try:
    element_tree, selector_map = await self._build_dom_tree(...)
    
    # Tree built
    event = DOMTreeBuiltEvent(
        total_elements=count_elements(element_tree),
        clickable_elements=len(selector_map),
        context_id=context_id
    )
    await EventManager().publish_async("dom", event)
    
    if highlight_elements:
        event = DOMElementHighlightedEvent(
            highlighted_count=len(selector_map),
            context_id=context_id
        )
        await EventManager().publish_async("dom", event)
    
    processing_time = (time.time() - start_time) * 1000
    
    # Processing completed
    event = DOMProcessingCompletedEvent(
        context_id=context_id,
        processing_time_ms=processing_time
    )
    await EventManager().publish_async("dom", event)
    
except Exception as e:
    # Processing failed
    event = DOMProcessingFailedEvent(
        context_id=context_id,
        error_message=str(e)
    )
    await EventManager().publish_async("dom", event)
```

## Message Manager (`browser_ai/agent/message_manager/service.py`)

### When adding messages:
```python
from browser_ai.event_bus.events import MessageAddedEvent

event = MessageAddedEvent(
    message_type=message.__class__.__name__.replace('Message', '').lower(),
    message_length=len(str(message.content)),
    total_messages=len(self.history.messages),
    total_tokens=self.history.total_tokens
)
EventManager().publish("messages", event)
```

### When trimming messages:
```python
from browser_ai.event_bus.events import MessageTrimmedEvent

tokens_before = self.history.total_tokens
# ... trim messages ...
tokens_after = self.history.total_tokens

event = MessageTrimmedEvent(
    messages_removed=removed_count,
    tokens_before=tokens_before,
    tokens_after=tokens_after,
    reason="Exceeded max token limit"
)
EventManager().publish("messages", event)
```

### When saving conversation:
```python
from browser_ai.event_bus.events import ConversationSavedEvent
import os

# After saving
file_size = os.path.getsize(file_path)
event = ConversationSavedEvent(
    file_path=file_path,
    messages_count=len(self.history.messages),
    file_size_bytes=file_size
)
EventManager().publish("messages", event)
```

### Tool calls:
```python
from browser_ai.event_bus.events import (
    ToolCallCreatedEvent,
    ToolResponseReceivedEvent
)

# Creating tool call
event = ToolCallCreatedEvent(
    tool_call_id=tool_call['id'],
    tool_name=tool_call['name'],
    arguments=tool_call['args']
)
EventManager().publish("messages", event)

# Receiving response
event = ToolResponseReceivedEvent(
    tool_call_id=tool_call_id,
    tool_name=tool_name,
    response_length=len(response),
    success=True
)
EventManager().publish("messages", event)
```

## LLM Interactions (in Agent or Message Manager)

### Before LLM call:
```python
from browser_ai.event_bus.events import LLMRequestStartedEvent

event = LLMRequestStartedEvent(
    model_name=self.llm.model_name if hasattr(self.llm, 'model_name') else None,
    purpose='action',  # or 'planning', 'validation'
    input_tokens_estimate=estimated_tokens
)
await EventManager().publish_async("llm", event)
```

### After successful LLM call:
```python
from browser_ai.event_bus.events import LLMRequestCompletedEvent
import time

start_time = time.time()
response = await self.llm.ainvoke(messages)
response_time = (time.time() - start_time) * 1000

event = LLMRequestCompletedEvent(
    model_name=self.llm.model_name if hasattr(self.llm, 'model_name') else None,
    purpose='action',
    input_tokens=response.response_metadata.get('token_usage', {}).get('prompt_tokens'),
    output_tokens=response.response_metadata.get('token_usage', {}).get('completion_tokens'),
    total_tokens=response.response_metadata.get('token_usage', {}).get('total_tokens'),
    response_time_ms=response_time
)
await EventManager().publish_async("llm", event)
```

### On rate limit:
```python
from browser_ai.event_bus.events import LLMRateLimitEvent

event = LLMRateLimitEvent(
    model_name=model_name,
    retry_after_seconds=retry_delay
)
await EventManager().publish_async("llm", event)
```

### Token limit warning:
```python
from browser_ai.event_bus.events import LLMTokenLimitWarningEvent

utilization = (current_tokens / max_tokens) * 100
if utilization > 80:
    event = LLMTokenLimitWarningEvent(
        current_tokens=current_tokens,
        max_tokens=max_tokens,
        utilization_percent=utilization
    )
    EventManager().publish("llm", event)
```

## Error Handling (throughout the system)

### When an error occurs:
```python
from browser_ai.event_bus.events import ErrorOccurredEvent

event = ErrorOccurredEvent(
    error_type=type(error).__name__,
    error_message=str(error),
    component='agent',  # or 'browser', 'controller', 'dom', 'llm'
    recoverable=True
)
await EventManager().publish_async("error", event)
```

### During recovery:
```python
from browser_ai.event_bus.events import (
    RecoveryAttemptedEvent,
    RecoverySuccessEvent,
    RecoveryFailedEvent
)

# Starting recovery
event = RecoveryAttemptedEvent(
    error_type=error_type,
    recovery_strategy='restart_browser',
    attempt_number=attempt
)
await EventManager().publish_async("error", event)

# Success
event = RecoverySuccessEvent(
    error_type=error_type,
    recovery_strategy='restart_browser',
    attempts_taken=attempt
)
await EventManager().publish_async("error", event)

# Failure
event = RecoveryFailedEvent(
    error_type=error_type,
    recovery_strategy='restart_browser',
    final_error=str(final_error)
)
await EventManager().publish_async("error", event)
```

## Performance Metrics

### Tracking performance:
```python
from browser_ai.event_bus.events import (
    PerformanceMetricEvent,
    StepDurationEvent,
    TotalExecutionTimeEvent
)

# Generic metric
event = PerformanceMetricEvent(
    metric_name='dom_build_time',
    metric_value=125.5,
    metric_unit='ms',
    component='dom'
)
EventManager().publish("metrics", event)

# Step duration
event = StepDurationEvent(
    step_number=step_num,
    duration_ms=duration,
    actions_count=len(actions)
)
await EventManager().publish_async("metrics", event)

# Total execution
event = TotalExecutionTimeEvent(
    total_duration_ms=total_time,
    total_steps=len(history),
    success=True
)
await EventManager().publish_async("metrics", event)
```

## Extension Integration (`browser_ai_gui/websocket_server.py`)

### WebSocket events:
```python
from browser_ai.event_bus.events import (
    ExtensionConnectedEvent,
    ExtensionDisconnectedEvent,
    WebSocketMessageReceivedEvent,
    WebSocketMessageSentEvent
)

# Connection
event = ExtensionConnectedEvent(
    extension_id=extension_id,
    extension_version=version
)
await EventManager().publish_async("extension", event)

# Message received
event = WebSocketMessageReceivedEvent(
    message_type=message['type'],
    message_size_bytes=len(json.dumps(message))
)
await EventManager().publish_async("extension", event)
```

## Quick Reference: Event Manager Usage

```python
from browser_ai.event_bus.core import EventManager
from browser_ai.event_bus.events import YourEvent

# Get singleton instance
event_manager = EventManager()

# Synchronous publish (for non-async contexts)
event_manager.publish("topic_name", event)

# Asynchronous publish (preferred in async contexts)
await event_manager.publish_async("topic_name", event)

# Subscribe to events
event_manager.subscribe("topic_name", your_handler)

# Unsubscribe
event_manager.unsubscribe("topic_name", your_handler)
```

## Testing Events

Create a test handler to verify events are being emitted:

```python
from browser_ai.event_bus.core import EventHandler, EventManager
from browser_ai.event_bus.events import BaseEvent

class DebugEventHandler(EventHandler):
    def handle(self, event: BaseEvent):
        print(f"[DEBUG] {event.topic}.{event.name}: {event.model_dump_json(indent=2)}")

# Subscribe to all topics you want to monitor
event_manager = EventManager()
debug_handler = DebugEventHandler()

for topic in ["agent", "browser", "dom", "controller", "llm", "messages"]:
    event_manager.subscribe(topic, debug_handler)
```
