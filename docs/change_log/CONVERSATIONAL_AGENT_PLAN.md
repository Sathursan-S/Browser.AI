# Conversational Agent - Ask Questions One by One

## Overview
Enable the Browser.AI agent to ask clarifying questions **during task execution** in Chat Mode, creating an interactive conversational experience where the agent can gather missing information step-by-step.

## Current State vs Desired State

### Current Behavior
- **Chatbot (Pre-Execution)**: Asks questions BEFORE starting automation to clarify task
- **Agent (During Execution)**: Only uses `request_user_help` for technical interventions (CAPTCHA, login, payment)
- **Problem**: Agent makes assumptions or fails when lacking information instead of asking user

### Desired Behavior
- **Agent asks questions ONE AT A TIME** when it needs clarification
- **Conversational flow**: Question → User Answer → Continue → Next Question (if needed)
- **Examples**:
  - "What's your budget for headphones?" (when shopping without budget)
  - "Which website would you prefer?" (when multiple options available)
  - "Do you want wireless or wired?" (when specification unclear)

## Implementation Plan

### ✅ Step 1: Create Action Model (DONE)
**File**: `browser_ai/controller/views.py`

Added `AskUserQuestionAction` model:
```python
class AskUserQuestionAction(BaseModel):
    question: str  # The specific question
    context: str  # Why this is needed
    options: list[str] = []  # Suggested answers (optional)
```

### ✅ Step 2: Register Agent Action (DONE)
**File**: `browser_ai/controller/service.py`

Added `ask_user_question` action:
- Logs the question and context
- Returns `ActionResult` with `requires_user_action=True`
- Includes `user_input_request` dict with question details

### ✅ Step 3: Update ActionResult Model (DONE)
**File**: `browser_ai/agent/views.py`

Added field to `ActionResult`:
```python
user_input_request: Optional[dict] = None
```

Structure:
```python
{
    'type': 'question',  # or 'intervention'
    'question': str,
    'context': str,
    'options': [str]
}
```

### ✅ Step 4: Update Agent Prompts (DONE)
**File**: `browser_ai/agent/prompts.py`

Added new section: **"ASK CLARIFYING QUESTIONS"** with:
- **When to ask**: Ambiguous tasks, multiple options, missing preferences
- **How to ask**: One question at a time, provide context, offer options
- **Examples**: Shopping scenarios with budget, website choice, specifications
- **Flow**: Ask → Wait for answer → Use answer → Continue

### 🔧 Step 5: Handle Questions in WebSocket Server (TODO)
**File**: `browser_ai_gui/websocket_server.py`

**Modifications Needed**:

#### 5.1: Monitor Agent Steps for Questions
In `ExtensionTaskManager._on_agent_step()` or similar callback:
```python
def _on_agent_step(self, state, output, step_num):
    # Check if any action result requires user input
    if hasattr(output, 'action_results'):
        for result in output.action_results:
            if result.requires_user_action and result.user_input_request:
                await self._handle_user_question(result.user_input_request)
```

#### 5.2: Emit Question to Frontend
```python
async def _handle_user_question(self, request_data):
    """Pause agent and send question to frontend"""
    # Pause the agent
    if self.current_agent:
        self.current_agent.pause()
    
    # Emit question event to extension
    self.socketio.emit('agent_question', {
        'type': request_data['type'],
        'question': request_data['question'],
        'context': request_data['context'],
        'options': request_data.get('options', []),
        'timestamp': datetime.now().isoformat()
    }, namespace='/extension')
    
    # Wait for user response (stored in self.user_question_answer)
    self.waiting_for_user_answer = True
```

#### 5.3: Handle User's Answer
```python
@socketio.on('user_answer')
def handle_user_answer(data):
    """Receive user's answer to agent's question"""
    answer = data.get('answer', '')
    
    # Store answer for agent to access
    self.user_question_answer = answer
    self.waiting_for_user_answer = False
    
    # Add answer to agent's message manager
    if self.current_agent:
        self.current_agent.message_manager.add_user_response(answer)
    
    # Resume agent
    if self.current_agent:
        self.current_agent.resume()
    
    # Emit confirmation
    emit('answer_received', {'success': True})
```

### 🔧 Step 6: Update Agent Message Manager (TODO)
**File**: `browser_ai/agent/message_manager/service.py`

**Add Method**:
```python
def add_user_response(self, response: str):
    """Add user's answer to the conversation history"""
    message = HumanMessage(
        content=f"[User Response]: {response}"
    )
    self.add_message(message)
```

### 🔧 Step 7: Frontend UI Changes (TODO)
**File**: `browser_ai_extension/browse_ai/src/sidepanel/components/ConversationMode.tsx`

**Add Question Handling**:
```typescript
// Listen for agent questions
socket.on('agent_question', (data) => {
  // Show question UI
  setAgentQuestion({
    question: data.question,
    context: data.context,
    options: data.options
  });
  
  // Pause regular message flow
  setWaitingForAnswer(true);
});

// Handle user's answer
const handleSubmitAnswer = (answer: string) => {
  socket.emit('user_answer', { answer });
  setWaitingForAnswer(false);
  setAgentQuestion(null);
  
  // Add to conversation
  addMessage({ role: 'user', content: answer });
};
```

**UI Component**:
```tsx
{agentQuestion && (
  <div className="agent-question-card">
    <h4>❓ Agent Question</h4>
    <p className="question">{agentQuestion.question}</p>
    <p className="context">{agentQuestion.context}</p>
    
    {agentQuestion.options.length > 0 ? (
      <div className="options">
        {agentQuestion.options.map(option => (
          <button 
            key={option}
            onClick={() => handleSubmitAnswer(option)}
          >
            {option}
          </button>
        ))}
      </div>
    ) : (
      <div className="free-text-answer">
        <input 
          type="text"
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          placeholder="Type your answer..."
        />
        <button onClick={() => handleSubmitAnswer(userAnswer)}>
          Submit
        </button>
      </div>
    )}
  </div>
)}
```

### 🔧 Step 8: Test End-to-End Flow (TODO)

**Test Scenario**:
```
User: "buy headphones"
  ↓
Agent: detect_location → Sri Lanka
Agent: find_best_website → daraz.lk, ikman.lk
  ↓
Agent: {"ask_user_question": {
  "question": "What's your budget range?",
  "context": "I found headphones ranging from Rs 2,000 to Rs 50,000. Knowing your budget helps me show the best options.",
  "options": ["Under Rs 5,000", "Rs 5,000 - Rs 15,000", "Above Rs 15,000"]
}}
  ↓
[AGENT PAUSES - Question shown in UI]
  ↓
User clicks: "Rs 5,000 - Rs 15,000"
  ↓
[Answer sent via WebSocket, added to conversation]
  ↓
Agent: search_ecommerce with budget filter
Agent: Finds 2 products → done
```

## Benefits

1. **Interactive Shopping**: Agent can clarify budget, preferences, specifications
2. **Better Decisions**: User guides agent instead of agent making wrong assumptions
3. **Conversational UX**: Feels like talking to a real assistant
4. **Error Prevention**: Reduces failed tasks due to missing information
5. **User Control**: User stays involved in the automation process

## Edge Cases to Handle

1. **No Response Timeout**: If user doesn't answer within X minutes, agent should timeout
2. **Multiple Questions**: Agent should ask ONE at a time, not overwhelm user
3. **Question Loop**: Prevent agent from asking same question repeatedly
4. **Task Cancellation**: User should be able to cancel while waiting for question
5. **Context Preservation**: When resuming, agent should remember all previous answers

## Next Steps (Priority Order)

1. ✅ **Create action model and controller** (DONE)
2. ✅ **Update prompts** (DONE)
3. 🔧 **Add WebSocket event handlers** (IN PROGRESS)
4. 🔧 **Update message manager to store answers**
5. 🔧 **Build frontend question UI**
6. 🔧 **Test with real shopping task**
7. 📝 **Document usage examples**

## Files Modified

- ✅ `browser_ai/controller/views.py` - Added `AskUserQuestionAction`
- ✅ `browser_ai/controller/service.py` - Added `ask_user_question` action + import
- ✅ `browser_ai/agent/views.py` - Added `user_input_request` field
- ✅ `browser_ai/agent/prompts.py` - Added "ASK CLARIFYING QUESTIONS" section
- 🔧 `browser_ai_gui/websocket_server.py` - Need to add question handling
- 🔧 `browser_ai/agent/message_manager/service.py` - Need `add_user_response()`
- 🔧 `browse_ai/src/sidepanel/components/ConversationMode.tsx` - Need question UI

## Status: 60% Complete
- ✅ Backend action infrastructure ready
- ✅ Prompts guide agent to ask questions
- 🔧 Need WebSocket communication layer
- 🔧 Need frontend UI components
- 🔧 Need end-to-end testing
