# Shopping Workflow Fix - Auto-Inject Location Detection

## Problem
The agent was **not analyzing country and websites before starting shopping tasks**, even though the prompts contained clear instructions to:
1. Use `detect_location` FIRST
2. Use `find_best_website` SECOND  
3. Only then proceed with shopping actions

**Root Cause**: The LLM was free to choose any action sequence, and would sometimes skip directly to `search_ecommerce` or `go_to_url`, ignoring the location detection workflow.

## Solution
Implemented **automatic shopping task detection** with **forced initial actions** to guarantee the correct workflow.

### Changes Made

#### 1. Enhanced System Prompt (`browser_ai/agent/prompts.py`)
Added critical warning at the top of `important_rules()`:

```python
⚠️ CRITICAL: SHOPPING TASKS MUST START WITH THESE TWO ACTIONS:
   - For ANY shopping/buying task, your FIRST action MUST be: {"detect_location": {}}
   - Your SECOND action MUST be: {"find_best_website": {"purpose": "what you're shopping for", "category": "shopping"}}
   - ONLY THEN proceed with search_ecommerce or navigation
   - This ensures correct currency and regional websites are used
   - Example first step for "buy headphones": [{"detect_location": {}}, {"find_best_website": {"purpose": "wireless headphones", "category": "shopping"}}]
```

#### 2. Auto-Detection & Injection (`browser_ai/agent/service.py`)

**Added Method**: `_auto_detect_shopping_actions()`
- **Location**: Lines 1352-1383 (Utility Methods section)
- **Purpose**: Detects shopping keywords in task and returns initial actions
- **Keywords Detected**: 
  - Transaction: `buy`, `purchase`, `shop`, `order`, `get me`, `find me`
  - Pricing: `price`, `cost`, `best deal`, `cheapest`
  - Products: `laptop`, `phone`, `headphones`, `camera`, `watch`, `shoes`, `clothes`, etc.
  - E-commerce: `ecommerce`, `online store`, `marketplace`

**Modified Initialization** (Lines 188-195):
```python
# Auto-inject location detection for shopping tasks
if initial_actions is None:
    initial_actions = self._auto_detect_shopping_actions()

self.initial_actions = (
    self._convert_initial_actions(initial_actions) if initial_actions else None
)
```

**How It Works**:
1. When Agent is initialized with `task="buy headphones"`:
   - `_auto_detect_shopping_actions()` detects "buy" keyword
   - Returns: `[{"detect_location": {}}, {"find_best_website": {"purpose": "buy headphones", "category": "shopping"}}]`
   - These actions are executed **before the LLM is even consulted**
2. Location detected → Website research completed → Agent has context before shopping
3. LLM then sees location info and website recommendations in state before deciding next action

### Workflow Now Guaranteed

```
User Task: "buy wireless headphones"
    ↓
🔍 Auto-Detect: Contains "buy" keyword → Is Shopping Task
    ↓
🌍 FORCED ACTION 1: detect_location
    → Returns: "Sri Lanka - LKR Rs", recommended sites: [daraz.lk, ikman.lk]
    ↓
🔗 FORCED ACTION 2: find_best_website (purpose="buy wireless headphones", category="shopping")
    → Returns: Google search results for "best websites to buy wireless headphones Sri Lanka"
    ↓
🤖 LLM DECISION: Now has location + website research before choosing next action
    → Can navigate to recommended regional site
    → Can search in correct currency
    → Can consider alternatives if item not found
```

## Benefits

### 1. **Guaranteed Execution**
- No longer relies on LLM following instructions
- Shopping tasks **always** start with location detection
- Website research **always** happens before navigation

### 2. **Better Context**
- LLM sees location info before making decisions
- LLM has website research results to review
- LLM can pick best regional site from research

### 3. **Correct Currency & Regional Sites**
- Prices shown in user's currency (LKR for Sri Lanka, USD for USA)
- Uses region-appropriate sites (daraz.lk vs amazon.com)
- Understands local e-commerce landscape

### 4. **Faster Execution**
- No wasted steps navigating to wrong sites
- No searching in wrong currency
- Less trial-and-error

## Testing

### Test Case 1: Shopping Task
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_ai import Agent

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', temperature=0.0)
agent = Agent(task="buy wireless headphones under $100", llm=llm)

# Expected: Auto-detects shopping → Injects initial_actions
# Step 1: detect_location (forced)
# Step 2: find_best_website (forced)
# Step 3+: LLM decides based on location context

await agent.run()
```

**Expected Logs**:
```
🛍️ Shopping task detected - injecting location detection and website research
Step 1: detect_location → Location: USA - USD $
Step 2: find_best_website → Researched: amazon.com, bestbuy.com, walmart.com
Step 3: LLM chooses to navigate to amazon.com (from research results)
```

### Test Case 2: Non-Shopping Task
```python
agent = Agent(task="check the weather in Tokyo", llm=llm)
# Expected: No auto-detection → No initial_actions injected
# Agent proceeds normally without location detection
```

## Configuration

### Override Behavior
If you want to provide custom initial actions (or prevent auto-injection):

```python
# Disable auto-injection by providing empty list
agent = Agent(
    task="buy headphones",
    llm=llm,
    initial_actions=[]  # Prevents auto-injection
)

# OR provide custom initial actions
agent = Agent(
    task="buy headphones",
    llm=llm,
    initial_actions=[
        {"detect_location": {}},
        {"go_to_url": {"url": "https://amazon.com"}}  # Custom workflow
    ]
)
```

### Add Custom Keywords
To detect additional shopping patterns, edit `_auto_detect_shopping_actions()`:

```python
shopping_keywords = [
    'buy', 'purchase', 'shop',
    'acquire', 'obtain',  # Add custom keywords
    # ... existing keywords
]
```

## Files Modified

1. **`browser_ai/agent/prompts.py`** (Lines 2-10)
   - Added critical warning in `important_rules()`
   - Emphasizes location detection requirement

2. **`browser_ai/agent/service.py`** (Lines 188-195, 1352-1383)
   - Added `_auto_detect_shopping_actions()` method
   - Modified initialization to auto-inject actions
   - Logs when shopping task detected

## Integration Notes

### Works With Existing Features
- ✅ **Stuck Detection**: Still triggers if location detection fails repeatedly
- ✅ **Fast Results**: Still returns 1-2 products immediately (Section 8)
- ✅ **User Help**: Can still request help for CAPTCHAs/payments
- ✅ **Custom Actions**: Users can still override with `initial_actions` parameter

### Backward Compatible
- Non-shopping tasks unaffected
- Existing code using `initial_actions` parameter works as before
- No breaking changes to Agent API

## Future Enhancements

1. **Smart Keyword Detection**: Use LLM to classify task instead of keyword matching
2. **More Task Types**: Auto-inject for downloads, research tasks, etc.
3. **Configurable**: Add `auto_detect_shopping=True` parameter to Agent
4. **Metrics**: Track how often auto-injection is used vs manual workflows

## Summary

The fix ensures that **shopping tasks always start with location detection and website research**, regardless of what the LLM decides. This is achieved by:
1. Detecting shopping keywords in the task
2. Automatically injecting `detect_location` and `find_best_website` as initial actions
3. Executing these actions before consulting the LLM
4. Giving the LLM full location context before it makes shopping decisions

**Result**: No more wrong currencies, no more wrong regional sites, no more skipped location detection! 🎯
