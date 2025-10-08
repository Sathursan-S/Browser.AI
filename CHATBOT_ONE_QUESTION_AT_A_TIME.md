# Chatbot One-Question-At-A-Time Conversation Flow

## Problem
The chatbot was asking **multiple questions at once** in a single response, which:
- Overwhelmed users with too much to answer at once
- Felt unnatural and robotic (like filling out a form)
- Made it harder for users to engage in conversation
- Required users to remember and answer all questions

**Example of OLD behavior:**
```
User: "I want to buy headphones"
Bot: "Sure! I can help you find headphones. Let me ask a few questions:
- What's your budget range?
- Do you prefer any specific website (Amazon, eBay, etc.)?
- Are you looking for wireless or wired headphones?
- Any specific features you need?"
```

## Solution
Updated chatbot to ask **ONE question at a time**, creating a natural conversational flow.

**Example of NEW behavior:**
```
User: "I want to buy headphones"
Bot: "Great! I can help you find headphones. 🎧 What's your budget range?"

User: "Under $100"
Bot: "Perfect! Are you looking for wireless or wired headphones?"

User: "Wireless"
Bot: "Nice choice! Any specific features you need? (e.g., noise cancellation, long battery life, gaming, sports)"

User: "Noise cancellation"
Bot: "Excellent! Let me confirm what I understood:
- Wireless headphones
- With noise cancellation
- Budget: Under $100

I'll find the best wireless noise-cancelling headphones under $100 with good reviews. Sound good?

✅ READY TO START
TASK: Buy wireless noise-cancelling headphones under $100 with good customer reviews and ratings"
```

## Changes Made

### File: `browser_ai_gui/chatbot_service.py`

#### Updated `SYSTEM_PROMPT` with:

1. **New Guideline #1: "Ask Questions ONE AT A TIME"**
   - Explicitly instructs: "NEVER ask multiple questions in a single response"
   - Emphasizes: "Ask the MOST IMPORTANT question first"
   - Creates natural conversation flow

2. **Question Priority Order** (for shopping tasks):
   ```
   a) What are they looking for (if vague)?
   b) Budget/price range
   c) Specific features or preferences
   d) Website preference (optional - auto-detected)
   e) Confirm and summarize
   ```

3. **Updated Examples**:
   - Shows multi-turn conversation with ONE question per turn
   - Demonstrates natural back-and-forth dialogue
   - Shows confirmation step before starting automation

4. **Simplified Task Format**:
   - No longer requires specifying website (auto-detected by location service)
   - Focus on: Product + Budget + Key Features
   - Example: "Buy wireless noise-cancelling headphones under $100"

5. **Updated Response Format**:
   - "Ask ONE question per response (unless you have all the info)"
   - Encourages natural conversation pace

## Benefits

### 1. **Natural Conversation Flow**
- Feels like chatting with a real assistant
- User can think about each question individually
- Less cognitive load per response

### 2. **Better User Engagement**
- Users are more likely to answer one question than a list
- Easier to course-correct if user changes their mind
- More interactive and engaging experience

### 3. **Higher Quality Answers**
- Users provide more thoughtful answers to single questions
- Can ask follow-up questions based on previous answers
- Adaptive questioning based on user's needs

### 4. **Reduced Overwhelm**
- New users aren't intimidated by long lists of questions
- Progressive disclosure of information needs
- Users can see progress through the conversation

### 5. **Better Task Clarity**
- Systematic gathering of information
- Priority-based questioning ensures critical info first
- Easier to identify when enough info is collected

## Integration with Location Detection

The updated prompt mentions:
> "You don't need to specify the website - the system will auto-detect user's location and find the best websites"

This integrates with our location detection feature:
- Chatbot focuses on **what** user wants (product, budget, features)
- Agent handles **where** to find it (location-based website selection)
- Cleaner separation of concerns

## Question Priority Logic

### For Shopping Tasks:
1. **Product Clarity** (if vague)
   - "What product are you looking for?"
   - "Can you be more specific about the headphones?"

2. **Budget** (critical for filtering)
   - "What's your budget range?"
   - "How much are you willing to spend?"

3. **Key Features** (refinement)
   - "Wireless or wired?"
   - "Any specific features needed?"

4. **Confirmation** (before starting)
   - Summarize all gathered info
   - Ask "Sound good?" or "Ready to proceed?"

### For Other Task Types:
- **Downloads**: File type → Purpose → Quality
- **Research**: Topic → Specific info → Sources
- **Form Filling**: Form type → Data needed → Special requirements

## Testing

### Test Case 1: Shopping (Complete Flow)
```
User: "buy headphones"
Bot: "Great! 🎧 What's your budget range?"
User: "$100"
Bot: "Are you looking for wireless or wired?"
User: "wireless"
Bot: "Any specific features? (noise cancellation, sports, gaming)"
User: "noise cancellation"
Bot: "Perfect! 
- Wireless headphones
- Noise cancellation
- Under $100

✅ READY TO START
TASK: Buy wireless noise-cancelling headphones under $100"
```

### Test Case 2: Vague Request
```
User: "I need something"
Bot: "I'd love to help! 😊 What are you looking to do or find?"
User: "Find a laptop"
Bot: "Got it! What's your budget for the laptop?"
User: "$800"
Bot: "What will you mainly use it for? (work, gaming, student, etc.)"
...
```

### Test Case 3: User Provides All Info Upfront
```
User: "Buy wireless headphones under $100 with noise cancellation"
Bot: "Perfect! I have all the details I need:
- Wireless headphones
- Noise cancellation
- Budget: $100

✅ READY TO START
TASK: Buy wireless noise-cancelling headphones under $100"
```

## Conversation State Management

The chatbot service already maintains conversation history:
```python
self.conversations: Dict[str, List[ConversationMessage]] = {}
```

This allows:
- ✅ Remembering previous answers
- ✅ Building context across multiple questions
- ✅ Adaptive questioning based on chat history
- ✅ Session-based conversations

## User Experience Improvements

### Before (Overwhelming):
```
Bot: [Asks 4 questions at once]
User: [Has to remember all questions]
User: [Provides incomplete answers or gets confused]
Bot: [Still missing information]
```

### After (Natural):
```
Bot: [Asks 1 question]
User: [Answers clearly]
Bot: [Acknowledges, asks next question]
User: [Answers]
Bot: [Progressive conversation]
```

## Compatibility

- ✅ Works with existing chatbot UI in extension
- ✅ Compatible with conversation history persistence
- ✅ Integrates with "Start Task" button workflow
- ✅ No breaking changes to API or data structures

## Future Enhancements

1. **Smart Question Skipping**
   - If user volunteers information, skip that question
   - Parse user messages for implicit answers
   - Example: "I want cheap wireless headphones" → Skip budget and type questions

2. **Context-Aware Questions**
   - Adapt questions based on task type (shopping vs research vs download)
   - Different priority orders for different scenarios

3. **Validation Feedback**
   - Acknowledge good answers: "Great choice!"
   - Ask for clarification on vague answers: "Could you be more specific?"

4. **Progress Indicators**
   - Show users how many more questions (optional)
   - "Just a couple more questions..."

## Summary

**Changed**: Chatbot now asks **ONE question at a time** instead of multiple questions
**File**: `browser_ai_gui/chatbot_service.py` (updated `SYSTEM_PROMPT`)
**Result**: More natural, engaging, and effective pre-task conversations
**Integration**: Works seamlessly with location detection and agent automation

Users now experience a friendly, conversational assistant that guides them step-by-step to create clear automation tasks! 🎯
