# 🎨 Visual Guide: Chatbot Feature

## UI Overview

### Header - Mode Toggle
```
┌─────────────────────────────────────────────────────────┐
│  🤖 Browser.AI    [💬 Chat Mode] ⚙️  ● Connected       │
└─────────────────────────────────────────────────────────┘
                         ↑
                   Click to toggle:
                   💬 Chat Mode ←→ ⚡ Direct Mode
```

## Chat Mode Interface

### Initial State
```
┌───────────────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant           [🔄 Reset]   │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 👋 Hi! I'm your Browser.AI assistant.              │ │
│  │ What would you like me to help you                 │ │
│  │ automate today? I can help with shopping,          │ │
│  │ downloads, research, form filling, and more!       │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│                                                           │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Type your message...                                │ │
│ │ (Ctrl+Enter to send)                                │ │
│ └─────────────────────────────────────────────────────┘ │
│                                             [Send] ➤    │
├───────────────────────────────────────────────────────────┤
│ 💡 Tip: Be specific about what you want to automate     │
│ 📝 The assistant will ask clarifying questions if needed │
└───────────────────────────────────────────────────────────┘
```

### During Conversation
```
┌───────────────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant           [🔄 Reset]   │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 👋 Hi! I'm your Browser.AI assistant...            │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│                        ┌──────────────────────────────┐   │
│                        │ I want to buy headphones     │   │
│                        └──────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Sure! I can help you find headphones.              │ │
│  │ Let me ask a few questions:                        │ │
│  │  - What's your budget range?                       │ │
│  │  - Do you prefer any specific website?             │ │
│  │  - Are you looking for wireless or wired?          │ │
│  │  - Any specific features you need?                 │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│                        ┌──────────────────────────────┐   │
│                        │ Under $100, Amazon, wireless │   │
│                        └──────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ● ● ●  [Typing...]                                 │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Task Ready State
```
┌───────────────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant           [🔄 Reset]   │
├───────────────────────────────────────────────────────────┤
│  ... (previous messages) ...                             │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Perfect! So you want wireless headphones from       │ │
│  │ Amazon for under $100. Let me confirm:              │ │
│  │                                                     │ │
│  │ I'll search Amazon for wireless headphones under    │ │
│  │ $100 and show you the top options with prices       │ │
│  │ and reviews. Sound good?                            │ │
│  │                                                     │ │
│  │ ╔═══════════════════════════════════════════════╗  │ │
│  │ ║ Proposed Task:                                ║  │ │
│  │ ║ Go to Amazon.com, search for wireless        ║  │ │
│  │ ║ headphones under $100, filter by customer    ║  │ │
│  │ ║ rating (4+ stars), and show me the top 5     ║  │ │
│  │ ║ options with their prices, ratings, and      ║  │ │
│  │ ║ key features                                  ║  │ │
│  │ ╚═══════════════════════════════════════════════╝  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┐│
│ │ ✅ Ready to start automation!  Confidence: 90%        ││
│ │                                 [🚀 Start Automation] ││
│ └───────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────┘
```

### Automation Started
```
┌───────────────────────────────────────────────────────────┐
│ 🤖 Chat with Browser.AI Assistant           [🔄 Reset]   │
├───────────────────────────────────────────────────────────┤
│  ... (previous conversation) ...                         │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 🚀 Perfect! Starting the automation now...          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## Direct Mode Interface

### Direct Mode View
```
┌───────────────────────────────────────────────────────────┐
│  🤖 Browser.AI    [⚡ Direct Mode] ⚙️  ● Connected        │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Status: Idle                                       │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  [⏸️ Pause]  [▶️ Resume]  [⏹️ Stop]                       │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Execution Logs                      [Clear Logs]   │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │  No tasks running...                                │ │
│  │                                                     │ │
│  │                                                     │ │
│  │                                                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ What would you like me to do?                       │ │
│ │ (e.g., 'Search for Python tutorials')               │ │
│ └─────────────────────────────────────────────────────┘ │
│                                             [Send] ➤    │
└───────────────────────────────────────────────────────────┘
```

## Interaction Flow Diagram

```
   User Opens Extension
           │
           ↓
   ┌──────────────────┐
   │  Default Mode:   │
   │  💬 Chat Mode    │
   └────────┬─────────┘
           │
           ↓
   ┌──────────────────────────┐
   │ Greeting Message Shows:  │
   │ "Hi! I'm your Browser.AI │
   │  assistant..."           │
   └────────┬─────────────────┘
           │
           ↓
   ┌──────────────────┐
   │  User Types:     │
   │ "buy headphones" │
   └────────┬─────────┘
           │
           ↓
   ┌──────────────────────────┐
   │ AI Asks Questions:       │
   │ "Budget? Website? Type?" │
   └────────┬─────────────────┘
           │
           ↓
   ┌──────────────────────────┐
   │  User Answers:           │
   │ "$100, Amazon, wireless" │
   └────────┬─────────────────┘
           │
           ↓
   ┌──────────────────────────┐
   │ AI Shows Task Preview:   │
   │ "✅ READY TO START"      │
   │ TASK: Search Amazon...   │
   └────────┬─────────────────┘
           │
           ↓
   ┌──────────────────────────┐
   │ Confirmation Box Shows:  │
   │ [🚀 Start Automation]    │
   └────────┬─────────────────┘
           │
   User Clicks ↓
           │
   ┌──────────────────────────┐
   │ Automation Starts!       │
   │ Browser opens & executes │
   └──────────────────────────┘
```

## Message Types Visual

### User Message (Right-aligned, Blue)
```
                        ┌──────────────────────────┐
                        │ I want to buy headphones │
                        └──────────────────────────┘
```

### Assistant Message (Left-aligned, Gray)
```
┌─────────────────────────────────────────────────┐
│ Sure! I can help you find headphones.          │
│ Let me ask a few questions:                    │
│  - What's your budget range?                   │
│  - Do you prefer any specific website?         │
└─────────────────────────────────────────────────┘
```

### Task Preview Message
```
┌─────────────────────────────────────────────────┐
│ Perfect! Looking for wireless headphones from   │
│ Amazon under $100.                              │
│                                                 │
│ ╔═══════════════════════════════════════════╗  │
│ ║ Proposed Task:                            ║  │
│ ║ Go to Amazon.com, search for wireless     ║  │
│ ║ headphones under $100, and show top 5     ║  │
│ ║ options with prices and reviews           ║  │
│ ╚═══════════════════════════════════════════╝  │
└─────────────────────────────────────────────────┘
```

### Typing Indicator
```
┌─────────────────────────────────────────────────┐
│ ● ● ●                                           │
│  ↑  ↑  ↑                                        │
│  Animated dots showing AI is thinking...        │
└─────────────────────────────────────────────────┘
```

## Color Scheme

```css
Background:       #1e1e1e  (Dark gray)
User Messages:    #0078d4  (Blue)
AI Messages:      #2d2d30  (Medium gray)
Task Preview:     rgba(0, 120, 212, 0.1) (Light blue bg)
Borders:          #3e3e42  (Light gray)
Text:             #e0e0e0  (Off-white)
Accent:           #0078d4  (Blue)
```

## Button States

### Normal State
```
┌─────────────────────┐
│ 🚀 Start Automation │  ← Blue background
└─────────────────────┘
```

### Hover State
```
┌─────────────────────┐
│ 🚀 Start Automation │  ← Darker blue, slightly raised
└─────────────────────┘     (transform: translateY(-1px))
```

### Disabled State
```
┌─────────────────────┐
│ 🚀 Start Automation │  ← Grayed out, not clickable
└─────────────────────┘     (opacity: 0.5)
```

## Mode Toggle Visual

### Chat Mode Active
```
[💬 Chat Mode] ⚙️
      ↑
  Highlighted with
  white background
```

### Direct Mode Active
```
[⚡ Direct Mode] ⚙️
       ↑
   Highlighted with
   white background
```

## Complete Interface Layouts

### Side-by-Side Comparison

```
┌───────── CHAT MODE ─────────┐  ┌───────── DIRECT MODE ─────────┐
│ 💬 Chat Mode   ⚙️ Connected │  │ ⚡ Direct Mode  ⚙️ Connected  │
├──────────────────────────────┤  ├───────────────────────────────┤
│                              │  │                               │
│ ┌──────────────────────────┐│  │ Status: Running               │
│ │ AI: Hi! What can I help? ││  │ [⏸️] [▶️] [⏹️]                 │
│ └──────────────────────────┘│  │                               │
│                              │  │ ┌───────────────────────────┐│
│ ┌──────────────────────────┐│  │ │ Logs:                     ││
│ │      User: Buy laptop    ││  │ │ • Task started            ││
│ └──────────────────────────┘│  │ │ • Navigating to Amazon    ││
│                              │  │ │ • Searching products      ││
│ ┌──────────────────────────┐│  │ │ • Found 25 results        ││
│ │ AI: Budget? Website?     ││  │ └───────────────────────────┘│
│ └──────────────────────────┘│  │                               │
│                              │  │ ┌───────────────────────────┐│
│ [Type message...] [Send]     │  │ │ Enter task...     [Send]  ││
│                              │  │ └───────────────────────────┘│
└──────────────────────────────┘  └───────────────────────────────┘

    Conversational & clarifying       Immediate & technical
```

## Animation Examples

### Message Fade-In
```
Frame 1:  opacity: 0, translateY(10px)
Frame 2:  opacity: 0.5, translateY(5px)
Frame 3:  opacity: 1, translateY(0px)
          ↑
        Smooth entrance
```

### Typing Indicator
```
Time 0.0s:  ● ○ ○
Time 0.2s:  ○ ● ○
Time 0.4s:  ○ ○ ●
Time 0.6s:  ● ○ ○  (repeats)
            ↑
        Animated dots
```

### Button Hover
```
Normal:  translateY(0px)
Hover:   translateY(-1px) + shadow
         ↑
       Subtle lift effect
```

---

This visual guide shows exactly what users will see and experience with the new chatbot feature!
