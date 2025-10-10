# 🚀 Quick Start: Testing Stuck Detection Feature

## ⚡ Fast Setup (5 minutes)

### 1. Start Backend Server
```powershell
cd "D:\open projects\Browser.AI"
python -m browser_ai_gui.main web --port 5000
```

**Expected Output:**
```
✅ WebSocket server running on http://localhost:5000
✅ Chatbot service initialized
✅ Stuck detector enabled
```

### 2. Build Extension
```powershell
cd browser_ai_extension\browse_ai
npm run dev
```

**Expected Output:**
```
✅ Built successfully
✅ Output: dist/
```

### 3. Load Extension in Chrome
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select: `D:\open projects\Browser.AI\browser_ai_extension\browse_ai\dist`

**You should see:** Browser.AI extension installed ✅

## 🧪 Test Scenario 1: Repeating Failed Actions

### Setup
1. Open extension side panel
2. Make sure **Chat Mode** is active (toggle at top)
3. Wait for greeting message

### Test Steps
```
You say: "Buy XYZ product from nonexistentwebsite123.com"

Agent will:
Step 1: Try to navigate → ❌ Failed (site doesn't exist)
Step 2: Retry navigation → ❌ Failed  
Step 3: Retry navigation → ❌ Failed

🆘 STUCK DETECTED! (after 3 similar failed attempts)
```

### Expected Result
You should see in chat:
```
┌─────────────────────────────────────────────────┐
│ 🤔 **The agent appears to be stuck**            │
│                                                 │
│ **Issue:** Repeating similar actions           │
│ **Duration:** ~30s (3 steps)                   │
│                                                 │
│ **Recent Actions:**                             │
│ 1. `navigate` - ❌ Failed                      │
│ 2. `navigate` - ❌ Failed                      │
│ 3. `navigate` - ❌ Failed                      │
│                                                 │
│ **Question:** What should it try differently?  │
└─────────────────────────────────────────────────┘
```

### Your Response
```
Type: "Try amazon.com instead"
```

### Expected Outcome
```
┌─────────────────────────────────────────────────┐
│ 📝 Thank you! The agent will continue...       │
└─────────────────────────────────────────────────┘

Agent continues:
Step 4: Navigate to amazon.com → ✅ Success
Step 5: Search for "XYZ product" → ✅ Success
...
```

## 🧪 Test Scenario 2: Element Not Found Loop

### Test Steps
```
You say: "Click the submit button on google.com"

Agent will:
Step 1: Navigate to google.com → ✅ Success
Step 2: Click submit button → ❌ Failed (no submit button exists)
Step 3: Click submit button → ❌ Failed
Step 4: Click submit button → ❌ Failed

🆘 STUCK DETECTED!
```

### Your Response
```
Type: "There is no submit button. Just tell me what's on the page instead."
```

### Expected Outcome
Agent adapts to new instruction and provides page description.

## 🧪 Test Scenario 3: No Progress Detection

### Test Steps
```
You say: "Find and click a hidden element that requires scrolling on a very long page"

Agent will:
Step 1-10: Scroll, click various things, but element truly doesn't exist
After 5 minutes of no meaningful progress...

🆘 STUCK DETECTED! (no progress timeout)
```

### Expected Result
```
┌─────────────────────────────────────────────────┐
│ 🤔 **The agent appears to be stuck**            │
│                                                 │
│ **Issue:** No progress for 300s                │
│ **Duration:** 5m (15 steps)                    │
│                                                 │
│ **Question:** Should it try a different        │
│              approach?                          │
└─────────────────────────────────────────────────┘
```

## 📊 Verification Checklist

After testing, verify:

- [ ] Help request appears in chat after stuck detection
- [ ] Help request contains:
  - [ ] Clear description of issue
  - [ ] List of attempted actions
  - [ ] Specific question for user
  - [ ] Suggestions for what user can do
- [ ] User can type response
- [ ] Response is sent as `user_help_response` event
- [ ] Agent acknowledges and continues
- [ ] Cooldown prevents spam (max 1 request per minute)
- [ ] Works in both Chat Mode and Direct Mode

## 🔍 Debug Mode

### View Stuck Detection Logs

**Backend Terminal:**
```
Look for:
[INFO] 🔄 Stuck detector reset for new task
[INFO] 📍 Step 1
[INFO] 📍 Step 2
[INFO] 📍 Step 3
[WARNING] 🆘 Agent appears stuck: Repeating similar actions
[INFO] 🆘 Requesting user help: Repeating similar actions
[INFO] 📝 User provided help: Try amazon.com instead
```

**Browser Console:**
```javascript
// Open DevTools → Console
// Filter by: agent_needs_help

// You should see:
{
  reason: "Repeating similar actions",
  summary: "🤔 **The agent appears to be stuck**...",
  attempted_actions: ["action1 ❌", "action2 ❌", "action3 ❌"],
  duration: 45,
  suggestion: "What should it try differently?"
}
```

## ⚙️ Configuration Quick Changes

### Make It More Aggressive (Ask for help faster)

**In `browser_ai_gui/websocket_server.py` line ~56:**
```python
# Find this line:
self.stuck_detector = StuckDetector(StuckDetectionConfig())

# Change to:
self.stuck_detector = StuckDetector(StuckDetectionConfig(
    stuck_action_threshold=2,      # Ask after 2 failures (default: 3)
    max_time_without_progress=120  # Ask after 2 min (default: 5 min)
))
```

**Restart backend** to apply changes.

### Make It More Patient (Fewer interruptions)

```python
self.stuck_detector = StuckDetector(StuckDetectionConfig(
    stuck_action_threshold=5,      # Ask after 5 failures (default: 3)
    max_time_without_progress=600  # Ask after 10 min (default: 5 min)
))
```

## 🐛 Common Issues

### Issue: Help request not showing
**Solution:**
1. Check WebSocket connection status (should be green dot)
2. Refresh extension
3. Check backend terminal for errors

### Issue: Agent doesn't continue after help
**Solution:**
1. Check network tab: `user_help_response` event sent?
2. Try typing more specific guidance
3. Check backend logs for response reception

### Issue: Too many help requests
**Solution:**
Increase cooldown:
```python
StuckDetectionConfig(
    min_help_request_interval=120  # 2 minutes between requests
)
```

## 📸 What Success Looks Like

### Chat Interface
```
✅ Greeting message appears when opening extension
✅ You can chat normally
✅ When agent gets stuck, you see formatted help request
✅ You can provide guidance
✅ Agent acknowledges and continues
✅ Chat history preserved when switching modes
```

### Backend Logs
```
✅ "Stuck detector reset for new task"
✅ Step numbers incrementing
✅ "Agent appears stuck" warning when triggered
✅ "Requesting user help" info message
✅ "User provided help" after response
```

### Network Tab
```
✅ WebSocket connection established
✅ agent_needs_help event received
✅ user_help_response event sent
✅ help_response_received event received
```

## 🎯 Next Steps After Testing

1. **Try real tasks:** Shopping, research, form filling
2. **Tune thresholds:** Adjust based on your use cases
3. **Provide feedback:** Note which scenarios work best/worst
4. **Monitor patterns:** See what agents commonly get stuck on

## 📚 Full Documentation

- **Technical Details:** `STUCK_DETECTION_FEATURE.md`
- **Visual Examples:** `STUCK_DETECTION_VISUAL_GUIDE.md`  
- **Implementation Summary:** `STUCK_DETECTION_IMPLEMENTATION_SUMMARY.md`

---

**Ready to test? Run the commands above and try a task!** 🚀
