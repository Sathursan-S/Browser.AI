# 🚀 Quick Start: Conversational Chatbot Mode

## What's New?

Browser.AI extension now has a **conversational chatbot** that helps you clarify what you want to automate before starting the browser!

## How to Use (3 Simple Steps)

### 1. Open the Extension
- Click the Browser.AI extension icon
- You'll see the chat interface

### 2. Tell the AI What You Want
Just type naturally - don't worry about being specific!

```
"I want to buy headphones"
```

### 3. Answer the Questions
The AI will ask clarifying questions:

```
AI: "Sure! A few questions:
- What's your budget?
- Which website?
- Wireless or wired?
- Any specific features?"

You: "Under $100, Amazon, wireless"

AI: "Perfect! ✅ READY TO START
TASK: Search Amazon for wireless headphones under $100..."
```

### 4. Click "Start Automation"
Review the task and click the button - done!

## 💬 Chat Mode vs ⚡ Direct Mode

**Chat Mode** (Default - Recommended):
- Asks questions to clarify your intent
- Ensures specific, accurate tasks
- Better success rate
- Great for beginners

**Direct Mode**:
- Immediate execution
- No clarification
- For power users who know exact tasks

Toggle between modes with the button in the header!

## 🎯 Example Conversations

### Shopping
```
You: "need shoes"
AI: "What kind? Budget? Website?"
You: "Running shoes, $120, Nike, Amazon"
AI: ✅ "I'll search Amazon for Nike running shoes under $120"
```

### Downloads
```
You: "download python tutorial"
AI: "PDF or video? Beginner or advanced?"
You: "PDF, beginner"
AI: ✅ "I'll find beginner Python tutorial PDFs from reputable sources"
```

### Research
```
You: "find info about AI"
AI: "What aspect of AI? What source?"
You: "Latest news, last 30 days"
AI: ✅ "I'll search for AI news from the past month"
```

## ⚙️ Setup (One-Time)

### Get Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Add to `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```

### Start the Server
```bash
python -m browser_ai_gui.main web --port 5000
```

## 💡 Tips

✅ **Do**:
- Start with a general request
- Answer the AI's questions
- Review the task before starting
- Use reset button if conversation gets confusing

❌ **Don't**:
- Worry about being too vague initially
- Skip the AI's questions
- Click start without reviewing
- Give up if first message isn't perfect

## 🐛 Troubleshooting

**Chatbot not responding?**
- Check GEMINI_API_KEY in .env
- Verify server is running
- Check connection status (top right)

**Want instant mode?**
- Toggle to ⚡ Direct Mode

**Conversation stuck?**
- Click 🔄 Reset button

## 🎉 That's It!

You're ready to use Browser.AI's intelligent chatbot! Just open the extension, tell it what you want, and let it help you create perfect automation tasks.

**Happy automating!** 🤖✨
