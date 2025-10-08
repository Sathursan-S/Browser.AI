# Voice Features - Visual Guide

## 🎤 Voice Input Button Location

```
┌─────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant    🔊  🔄    │
├─────────────────────────────────────────────────┤
│                                                 │
│  👤 Buy wireless headphones                     │
│                                                 │
│  🤖 Great! What's your budget?                  │
│                                                 │
│  👤 Under $100                                  │
│                                                 │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────┐ │
│ │ What would you like me to do?               │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Press Ctrl+Enter to send           🎤  📤 Send │
└─────────────────────────────────────────────────┘
                                      ↑
                        VOICE INPUT BUTTON HERE
```

## 🔊 Speech Toggle Location

```
┌─────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant    🔊  🔄    │
├─────────────────────────────────────────────────┤
                                      ↑
                          SPEECH TOGGLE HERE
```

## Button States

### Voice Input Button 🎤

#### State 1: Idle (Ready)
```
┌─────┐
│ 🎤  │  ← Gray background
└─────┘    Click to start listening
```

#### State 2: Listening (Active)
```
┌─────┐
│ ⏹️  │  ← Red background with pulse animation
└─────┘    Click to stop listening
   💫 Pulsing...
```

#### State 3: Disabled (Task Running)
```
┌─────┐
│ 🎤  │  ← Grayed out, not clickable
└─────┘    Task is running...
```

### Speech Toggle Button 🔊

#### State 1: Disabled (Muted)
```
┌─────┐
│ 🔇  │  ← Gray background
└─────┘    Click to enable voice output
```

#### State 2: Enabled (Active)
```
┌─────┐
│ 🔊  │  ← Purple gradient background
└─────┘    Click to disable voice output
```

#### State 3: Speaking (Playing)
```
┌─────┐
│ 📊  │  ← Purple background with animation
└─────┘    Speaking assistant response...
   🎵 Animated sound waves
```

## Visual Flow Diagrams

### Voice Input Flow

```
┌─────────────┐
│ User clicks │
│  🎤 button  │
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│ Browser asks for    │
│ microphone access   │
│ (first time only)   │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Button turns RED    │
│ and starts PULSING  │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ User speaks:        │
│ "Buy headphones"    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Interim text shown  │
│ (light gray):       │
│ "Buy headphones"    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ User stops speaking │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Final text added:   │
│ "Buy headphones"    │
│ (black text)        │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Button returns to   │
│ gray (idle)         │
└─────────────────────┘
```

### Speech Output Flow

```
┌─────────────┐
│ User clicks │
│  🔊 toggle  │
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│ Button turns PURPLE │
│ (speech enabled)    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ User sends message: │
│ "Buy headphones"    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Bot responds:       │
│ "Great! What's      │
│  your budget?"      │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Text appears in     │
│ chat window         │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Voice synthesis     │
│ speaks the text     │
│ 🔊 Animated icon    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Speech finishes     │
│ Icon returns to     │
│ static purple       │
└─────────────────────┘
```

## Color Coding

### Button Colors

| State | Color | Visual |
|-------|-------|--------|
| Idle | Gray (#f3f4f6) | `░░░` |
| Active (Voice) | Red Gradient (#ef4444→#dc2626) | `▓▓▓` |
| Active (Speech) | Purple Gradient (#667eea→#764ba2) | `▓▓▓` |
| Disabled | Light Gray (50% opacity) | `░ ░` |
| Error | Red Background (#fef2f2) | `▓ ▓` |

### Text Colors

| Type | Color | Example |
|------|-------|---------|
| User Message | Black | "Buy headphones" |
| Bot Message | White on dark | "Great! What's your budget?" |
| Interim Speech | Light Gray | "Buy head..." |
| Error Message | Red (#dc2626) | "No microphone found" |
| Hint Text | Gray (#6b7280) | "Press Ctrl+Enter to send" |

## Animation Details

### Voice Input Pulse
```
Time:  0s ─────────────── 1.5s ─────────────── 3s
       
       ⭕ Small         ⭕⭕⭕ Large       ⭕ Small
       
Shadow: Tight          Spread          Tight
Color:  rgba(239,68,68,0.4)
Timing: ease-in-out
Loop:   Infinite
```

### Speech Output Wave
```
Time:  0s ────── 0.5s ────── 1s
       
Icon:   🔊 1.0x    🔊 1.1x   🔊 1.0x

Scale:  Normal     Larger    Normal
Timing: ease-in-out
Loop:   While speaking
```

## Error Messages Location

```
┌─────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────┐ │
│ │ What would you like me to do?               │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ ⚠️ No microphone found. Check your device. │ │ ← ERROR HERE
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Press Ctrl+Enter to send           🎤  📤 Send │
└─────────────────────────────────────────────────┘
```

## Complete Interaction Example

### Scenario: User asks about headphones using voice

```
Step 1: Enable Speech Output
┌─────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant   [🔊] 🔄    │ ← Click speaker
└─────────────────────────────────────────────────┘
                                       ↓
                                   Turns purple

Step 2: Click Microphone
┌─────────────────────────────────────────────────┐
│ Press Ctrl+Enter to send          [🎤] 📤 Send │ ← Click mic
└─────────────────────────────────────────────────┘
                                       ↓
                                   Turns red & pulses

Step 3: Speak
"Buy wireless headphones under $100"
                                       ↓
┌─────────────────────────────────────────────────┐
│ Buy wireless headphones under $100              │ ← Interim (gray)
└─────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────┐
│ Buy wireless headphones under $100              │ ← Final (black)
└─────────────────────────────────────────────────┘

Step 4: Send Message
                                       ↓
┌─────────────────────────────────────────────────┐
│ 👤 Buy wireless headphones under $100           │
└─────────────────────────────────────────────────┘

Step 5: Bot Responds (Text + Speech)
┌─────────────────────────────────────────────────┐
│ 🤖 Great! What's your budget?                   │ ← Text appears
└─────────────────────────────────────────────────┘
       +
   [📊] ← Speaker animates
   "Great! Whats your budget?" ← Voice plays

Step 6: Continue Conversation
                                       ↓
                                   Repeat steps 2-5
```

## Keyboard Shortcuts

```
┌────────────────────┬──────────────────────────────┐
│ Shortcut           │ Action                       │
├────────────────────┼──────────────────────────────┤
│ Ctrl + Enter       │ Send message                 │
│ Tab                │ Navigate to next button      │
│ Enter/Space        │ Activate focused button      │
│ Esc                │ Stop voice input (planned)   │
└────────────────────┴──────────────────────────────┘
```

## Mobile View (Future)

```
┌────────────────────┐
│ 🤖 Chat    🔊  🔄 │
├────────────────────┤
│                    │
│ 👤 Message         │
│                    │
│ 🤖 Response        │
│                    │
└────────────────────┘
┌────────────────────┐
│ ┌────────────────┐ │
│ │ Type message   │ │
│ └────────────────┘ │
│        🎤  📤      │ ← Stacked on mobile
└────────────────────┘
```

## Permission Prompts

### First Time Microphone Access
```
┌─────────────────────────────────────────────┐
│  🔒 https://extension wants to:             │
│                                             │
│  📷 Use your microphone                     │
│                                             │
│         [ Block ]    [ Allow ]              │
│                                             │
│  ℹ️ Browser.AI needs microphone access     │
│     for voice input                         │
└─────────────────────────────────────────────┘
```

## Troubleshooting Visual Guide

### Problem: Button is grayed out

```
❌ WRONG:
┌─────┐
│ 🎤  │  ← Gray and disabled
└─────┘

✅ CHECK:
1. Is task running? → Wait for it to finish
2. Browser support? → Check Chrome/Edge
3. Permissions? → Check chrome://settings/content
```

### Problem: No sound output

```
❌ SYMPTOM:
┌─────┐
│ 🔊  │  ← Purple but no sound
└─────┘

✅ FIX:
1. Check system volume 🔊
2. Unmute browser tab 🔈
3. Check browser settings 🎛️
4. Try different voice ⚙️
```

## Best Practices

### DO ✅

```
1. Speak clearly and naturally
   👤 "Buy wireless headphones" ← Good

2. Wait for red button before speaking
   [🎤] → Click → [⏹️] → Speak

3. Enable speech for better UX
   [🔇] → Click → [🔊]

4. Use in quiet environment
   🔇 Quiet room = Better recognition
```

### DON'T ❌

```
1. Don't speak too fast
   👤 "buywirel3ssheadph0nes" ← Bad

2. Don't speak while button is gray
   [🎤] ← Don't speak yet!

3. Don't use in noisy places
   🔊📢🎵 = Poor recognition

4. Don't forget to allow mic access
   🔒 Always click "Allow"
```

## Success Indicators

### Voice Input Working:
```
✅ Microphone button visible
✅ Button turns red when clicked
✅ Button pulses while listening
✅ Text appears as you speak
✅ Final text is black (not gray)
✅ Can click Send after speaking
```

### Speech Output Working:
```
✅ Speaker button visible
✅ Button turns purple when clicked
✅ Icon animates while speaking
✅ Can hear assistant responses
✅ Speech matches text in chat
✅ Can toggle on/off anytime
```

---

## Quick Reference Card

```
╔═══════════════════════════════════════════════╗
║         VOICE FEATURES QUICK REFERENCE        ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  🎤 VOICE INPUT                               ║
║  ─────────────                                ║
║  Location: Bottom-right of chat input         ║
║  Click: Start/stop listening                  ║
║  Visual: Gray → Red (pulsing)                 ║
║  Interim: Gray text while speaking            ║
║  Final: Black text when done                  ║
║                                               ║
║  🔊 SPEECH OUTPUT                             ║
║  ───────────────                              ║
║  Location: Top-right header                   ║
║  Click: Enable/disable voice                  ║
║  Visual: Gray → Purple (with waves)           ║
║  Auto: Speaks new bot messages                ║
║  Stop: Click toggle or reset chat             ║
║                                               ║
║  ⚠️ TROUBLESHOOTING                           ║
║  ──────────────                               ║
║  No mic: Allow permissions                    ║
║  No sound: Check volume/mute                  ║
║  Gray button: Check browser support           ║
║  Errors: Read inline error messages           ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

---

**This visual guide covers all UI elements and user interactions! 🎨**
