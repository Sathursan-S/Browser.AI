# 🎨 Visual Guide: Stuck Detection & User Help

## The Problem (Before)

```
┌─────────────────────────────────────────────────────────┐
│ Agent Task: "Buy wireless headphones from Amazon"      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Navigate to website     ✅                     │
│  Step 2: Search for "headphones" ❌ (element not found)│
│  Step 3: Search for "headphones" ❌ (element not found)│
│  Step 4: Search for "headphones" ❌ (element not found)│
│  Step 5: Search for "headphones" ❌ (element not found)│
│  Step 6: Search for "headphones" ❌ (element not found)│
│  Step 7: Search for "headphones" ❌ (element not found)│
│  ...                                                    │
│  ... continues indefinitely ...                         │
│  ...                                                    │
│                                                         │
│  ❌ TASK FAILED AFTER 100 STEPS                         │
│                                                         │
│  User: 😤 "Why didn't it just ASK me for help?!"       │
└─────────────────────────────────────────────────────────┘
```

## The Solution (After)

```
┌─────────────────────────────────────────────────────────┐
│ Agent Task: "Buy wireless headphones from Amazon"      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Navigate to website     ✅                     │
│  Step 2: Search for "headphones" ❌ (element not found)│
│  Step 3: Search for "headphones" ❌ (element not found)│
│  Step 4: Search for "headphones" ❌ (element not found)│
│                                                         │
│  🆘 STUCK DETECTED! Asking for help...                 │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 🤔 Agent is stuck (repeating failed search)       │ │
│  │ What should I try instead?                        │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  User: "The search box is at the top right, try       │
│         clicking that first"                           │
│                                                         │
│  Step 5: Click search box (top right) ✅               │
│  Step 6: Type "wireless headphones"   ✅               │
│  Step 7: Click search button          ✅               │
│                                                         │
│  ✅ TASK COMPLETED SUCCESSFULLY                         │
│                                                         │
│  User: 😊 "Great collaboration!"                       │
└─────────────────────────────────────────────────────────┘
```

## Flow Diagram

```
                 Agent Starts Task
                        │
                        ↓
              ┌─────────────────┐
              │  Execute Step   │ ◄──────────┐
              └────────┬────────┘            │
                       │                     │
                       ↓                     │
              ┌─────────────────┐            │
              │ Record Action   │            │
              │  in Detector    │            │
              └────────┬────────┘            │
                       │                     │
                       ↓                     │
              ┌─────────────────┐            │
              │ Is Stuck?       │            │
              └────────┬────────┘            │
                    /     \                  │
                  No       Yes               │
                 /           \               │
                ↓             ↓              │
         Continue?      ┌──────────────┐    │
              ↓         │ Pause & Ask  │    │
              │         │  for Help    │    │
              │         └──────┬───────┘    │
              │                │             │
              │                ↓             │
              │         ┌──────────────┐    │
              │         │ User Responds│    │
              │         └──────┬───────┘    │
              │                │             │
              │                ↓             │
              │         ┌──────────────┐    │
              │         │ Apply User   │    │
              │         │  Guidance    │    │
              │         └──────┬───────┘    │
              │                │             │
              └────────────────┴─────────────┘
                       │
                       ↓
                  Task Done?
                    /     \
                  Yes      No
                  │        │
                  ↓        └──> Continue
              Success!
```

## Detection Triggers (Visual)

### 1️⃣ Repeating Similar Actions

```
Timeline:
  0s ───> search_ecommerce ───> ❌ Failed
  10s ───> search_ecommerce ───> ❌ Failed
  20s ───> search_ecommerce ───> ❌ Failed
                                   ↓
                            🚨 TRIGGER!
                      "Repeating similar actions"
```

### 2️⃣ Long Step Duration

```
Timeline:
  0s ───> click(download_button) ───> ⏳ Processing...
  30s                                  ⏳ Still processing...
  60s                                  ⏳ Still processing...
  90s                                  ⏳ Still processing...
  120s                                 ⏳ Still processing...
                                        ↓
                                  🚨 TRIGGER!
                         "Step taking too long (120s)"
```

### 3️⃣ No Progress Over Time

```
Timeline:
  0s ───> scroll_down ───> ✅ Success
  30s ───> click      ───> ❌ Failed (Element not found)
  60s ───> scroll_down ───> ✅ Success (but no meaningful progress)
  90s ───> click      ───> ❌ Failed
  120s ───> scroll_down ───> ✅ Success (still no progress)
  ...
  300s (5 minutes of no real progress)
                                        ↓
                                  🚨 TRIGGER!
                         "No progress for 300s"
```

### 4️⃣ Consecutive Failures

```
Timeline:
  0s ───> click(submit_button) ───> ❌ Failed (Button disabled)
  10s ───> fill_form(email)    ───> ❌ Failed (Invalid format)
  20s ───> click(checkbox)     ───> ❌ Failed (Element not visible)
                                      ↓
                                🚨 TRIGGER!
                       "Multiple consecutive failures (3)"
```

## Chat Interface Example

### Scenario: Product Not Found

```
┌───────────────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant           [🔄 Reset]   │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 🚀 Starting your shopping task...                   │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ℹ️ Navigating to Amazon...                          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ℹ️ Searching for wireless headphones...             │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ⚠️ Search failed - element not found                │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 🔄 Retrying search...                                │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ⚠️ Search failed again                              │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 🤔 **The agent appears to be stuck**                │ │
│  │                                                     │ │
│  │ **Issue:** Repeating similar actions: search_      │ │
│  │ ecommerce, search_ecommerce, search_ecommerce      │ │
│  │ **Duration:** 45s (3 steps attempted)              │ │
│  │                                                     │ │
│  │ **Recent Actions:**                                 │ │
│  │ 1. `search_ecommerce` - ❌ Failed                  │ │
│  │ 2. `search_ecommerce` - ❌ Failed                  │ │
│  │ 3. `search_ecommerce` - ❌ Failed                  │ │
│  │                                                     │ │
│  │ **Question:** The agent is stuck in a loop.        │ │
│  │ What should it try differently?                    │ │
│  │                                                     │ │
│  │ 💡 You can:                                         │ │
│  │ - Provide specific guidance on what to try         │ │
│  │ - Ask the agent to skip this part and move on      │ │
│  │ - Request a summary of what was accomplished       │ │
│  │ - Stop the task if needed                          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│                        ┌──────────────────────────────┐   │
│                        │ Look for the search icon in  │   │
│                        │ the header, it's a magnifying│   │
│                        │ glass. Click that first.     │   │
│                        └──────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 📝 Thank you! The agent will continue with your    │ │
│  │    guidance.                                        │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ✅ Found search icon! Clicking...                   │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ✅ Typing "wireless headphones"...                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 🎉 Search successful! Found 1,247 results          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Type your message...                                │ │
│ └─────────────────────────────────────────────────────┘ │
│                                             [Send] ➤    │
└───────────────────────────────────────────────────────────┘
```

## Message Types & Colors

### Regular Message
```
┌─────────────────────────────────────────┐
│ ℹ️ Regular information message          │  ← Gray background
└─────────────────────────────────────────┘
```

### Success Message
```
┌─────────────────────────────────────────┐
│ ✅ Action completed successfully        │  ← Green accent
└─────────────────────────────────────────┘
```

### Error Message
```
┌─────────────────────────────────────────┐
│ ❌ Action failed - error details        │  ← Red accent
└─────────────────────────────────────────┘
```

### Help Request Message
```
┌─────────────────────────────────────────┐
│ 🤔 **The agent appears to be stuck**    │  ← Yellow/orange accent
│                                         │     Highlighted border
│ **Issue:** Description of problem      │
│ **Question:** What should I do?        │
└─────────────────────────────────────────┘
```

### User Help Response
```
                  ┌──────────────────────┐
                  │ Try clicking X first │  ← Blue bubble (right)
                  └──────────────────────┘
```

## Code Flow Example

### Backend: Detecting Stuck State

```python
# In websocket_server.py - ExtensionTaskManager._on_agent_step()

def _on_agent_step(self, state, output, step_num):
    """Called after EVERY agent step"""
    
    # 1. Record what happened
    self.stuck_detector.record_action(
        action_name="search_ecommerce",
        success=False,
        error_message="Element not found"
    )
    
    # 2. Check if stuck (every 3 steps)
    if step_num % 3 == 0:
        report = self.stuck_detector.check_if_stuck()
        
        # 3. If stuck, request help
        if report.is_stuck:
            asyncio.create_task(
                self.request_user_help(report)
            )
```

### Backend: Sending Help Request

```python
# In websocket_server.py - ExtensionTaskManager.request_user_help()

async def request_user_help(self, stuck_report):
    """Request help from user"""
    
    # Prepare help message
    help_payload = {
        "reason": "Repeating similar actions",
        "summary": "🤔 **The agent appears to be stuck**\n...",
        "attempted_actions": ["search ❌", "search ❌", "search ❌"],
        "duration": 45,
        "suggestion": "What should it try differently?"
    }
    
    # Send to extension
    self.socketio.emit("agent_needs_help", help_payload)
    
    # Wait for user response (with 5-minute timeout)
    timeout = 300
    while self.user_help_response is None:
        await asyncio.sleep(1)
        if timeout reached:
            return None
    
    # Got response! Continue with guidance
    return self.user_help_response
```

### Frontend: Receiving Help Request

```typescript
// In ConversationMode.tsx

const handleAgentNeedsHelp = (data) => {
  // Display as assistant message
  const helpMessage: Message = {
    role: 'assistant',
    content: data.summary,  // Contains the formatted help request
    timestamp: new Date().toISOString()
  }
  
  setMessages([...messages, helpMessage])
}

// Register listener
socket.on('agent_needs_help', handleAgentNeedsHelp)
```

### Frontend: Sending User Response

```typescript
// In ConversationMode.tsx - handleSendMessage()

const handleSendMessage = () => {
  const lastMessage = messages[messages.length - 1]
  const isHelpRequest = lastMessage.content.includes('🤔 **The agent appears to be stuck**')
  
  if (isHelpRequest) {
    // Send as help response (not regular chat)
    socket.emit('user_help_response', { 
      response: input.trim() 
    })
  } else {
    // Regular chat message
    socket.emit('chat_message', { 
      message: input.trim() 
    })
  }
}
```

## Configuration Examples

### Aggressive (Ask for help quickly)

```python
# In websocket_server.py

self.stuck_detector = StuckDetector(StuckDetectionConfig(
    max_step_duration=60,          # 1 minute per step
    stuck_action_threshold=2,      # 2 similar actions = stuck
    max_time_without_progress=120, # 2 minutes max
    min_help_request_interval=30   # Can ask every 30s
))
```

**Use Case:** Complex tasks where user guidance is expected

### Balanced (Default)

```python
self.stuck_detector = StuckDetector(StuckDetectionConfig(
    max_step_duration=120,         # 2 minutes per step
    stuck_action_threshold=3,      # 3 similar actions = stuck
    max_time_without_progress=300, # 5 minutes max
    min_help_request_interval=60   # Ask max once per minute
))
```

**Use Case:** Most general automation tasks

### Patient (Minimize interruptions)

```python
self.stuck_detector = StuckDetector(StuckDetectionConfig(
    max_step_duration=300,         # 5 minutes per step
    stuck_action_threshold=5,      # 5 similar actions = stuck
    max_time_without_progress=600, # 10 minutes max
    min_help_request_interval=120  # Only ask every 2 minutes
))
```

**Use Case:** Long-running tasks like downloads, data processing

## Testing Checklist

### ✅ Basic Stuck Detection
- [ ] Agent loops on same action 3 times → Help requested
- [ ] Single step takes > 120s → Help requested
- [ ] No progress for 5 minutes → Help requested

### ✅ User Interaction
- [ ] Help request appears in chat as assistant message
- [ ] User can type response
- [ ] Response sent as `user_help_response` event
- [ ] Agent continues after receiving help

### ✅ Edge Cases
- [ ] User doesn't respond → Times out after 5 minutes
- [ ] Multiple help requests → Cooldown prevents spam
- [ ] WebSocket disconnected → Help request queued/retried
- [ ] Agent completes task before help arrives → Graceful handling

### ✅ UI/UX
- [ ] Help request clearly distinguishable from regular messages
- [ ] Help request includes actionable information
- [ ] User response immediately acknowledged
- [ ] Chat history preserved through mode switches

---

**Visual Guide Complete! 🎨**
All scenarios, flows, and examples documented with ASCII diagrams.
