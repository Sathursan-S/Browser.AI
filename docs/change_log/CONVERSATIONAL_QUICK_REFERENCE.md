# 🚀 Conversational Agent - Quick Reference

## Installation
```python
from browser_ai import ConversationalAgent
from langchain_openai import ChatOpenAI
```

## Basic Usage

### Interactive Mode (Terminal)
```python
llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
agent = ConversationalAgent(llm=llm, use_vision=True)

result = await agent.run_with_clarification(
    initial_prompt="buy something online",
    interactive=True,
    max_steps=100
)
```

### Programmatic Mode (GUI/API)
```python
async def get_user_input(questions: str) -> str:
    # Your logic to get user response
    return user_response

agent = ConversationalAgent(
    llm=llm,
    clarification_callback=get_user_input,
    use_vision=True
)

result = await agent.run_with_clarification(
    initial_prompt="download tutorial",
    interactive=False
)
```

### Manual Control
```python
agent = ConversationalAgent(llm=llm)

# Step 1: Clarify
clarification = await agent.clarify_task("vague prompt")

# Step 2: Check if questions needed
if clarification.needs_clarification:
    for q in clarification.questions:
        print(q)
    
    # Step 3: Process response
    user_answer = input("Your answer: ")
    result = await agent.process_user_response(user_answer)
    
# Step 4: Execute when ready
if clarification.ready_to_execute:
    task = clarification.task_understood
    # Now run with regular Agent or continue
```

## Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `clarify_task(prompt)` | Analyze if clarification needed | `ClarificationResponse` |
| `process_user_response(answer)` | Process user's answer | `ClarificationResponse` |
| `run_with_clarification(...)` | Full flow: clarify → execute | Agent result |
| `get_conversation_history()` | Get conversation | `List[Dict]` |
| `clear_conversation()` | Reset state | None |

## Response Object

```python
ClarificationResponse(
    needs_clarification: bool,    # True if questions needed
    questions: List[str],          # List of questions
    task_understood: str,          # Clarified task (if ready)
    ready_to_execute: bool         # Can start automation
)
```

## Common Patterns

### Pattern 1: Shopping
```python
"buy something"
→ Agent asks: product, budget, site
→ User answers
→ Execute: Search on specified site
```

### Pattern 2: Download
```python
"download a file"
→ Agent asks: type, format, source
→ User answers
→ Execute: Download from source
```

### Pattern 3: Research
```python
"find information"
→ Agent asks: topic, detail level, sources
→ User answers
→ Execute: Search and extract
```

## When to Use

### ✅ Use ConversationalAgent
- Vague user prompts
- GUI/chat interfaces
- Multiple parameters needed
- First-time users
- Interactive applications

### ✅ Use Regular Agent
- Clear, specific tasks
- Automated scripts
- Batch processing
- No user interaction

## Testing
```bash
python test_conversational_agent.py
```

## Examples
```bash
python examples/conversational_mode.py
```

## Full Documentation
See: `CONVERSATIONAL_AGENT_GUIDE.md`

---

## Cheat Sheet

```python
# Quick setup
from browser_ai import ConversationalAgent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
agent = ConversationalAgent(llm=llm)

# Interactive (terminal)
await agent.run_with_clarification("buy laptop", interactive=True)

# Programmatic (GUI)
agent = ConversationalAgent(llm=llm, clarification_callback=my_callback)
await agent.run_with_clarification("buy laptop", interactive=False)

# Manual steps
clarify = await agent.clarify_task("buy laptop")
if clarify.needs_clarification:
    response = await agent.process_user_response(user_input)
```

## Conversation Flow

```
User Input (vague)
    ↓
Agent analyzes
    ↓
Needs clarification? ─NO→ Execute task
    ↓ YES
Agent asks questions
    ↓
User responds
    ↓
Agent processes response
    ↓
Ready? ─NO→ Ask more questions
    ↓ YES
Execute clarified task
```

## Tips

💡 **Start vague** - Let agent guide you
💡 **Provide details when asked** - Be specific in responses
💡 **Review understanding** - Check agent's summary
💡 **Same instance** - Use one agent for full conversation
💡 **Clear between tasks** - Reset for unrelated tasks

---

**Quick Example:**
```python
agent = ConversationalAgent(llm=ChatOpenAI(model='gpt-4o'))
result = await agent.run_with_clarification("buy earbuds", interactive=True)
# Agent will ask about budget, features, site, etc.
# Then execute with full understanding
```

**That's it! 🎉**
