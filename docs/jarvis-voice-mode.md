# JARVIS Voice Conversation Mode

Browser.AI now includes a JARVIS-inspired voice conversation interface that allows you to interact with the AI assistant using natural language, both through voice and text.

## Overview

The JARVIS (Just A Rather Very Intelligent System) conversation mode provides:
- **Natural voice-based interaction** - Speak your requests naturally
- **Multi-language support** - English, Tamil (தமிழ்), and Sinhala (සිංහල)
- **JARVIS-like persona** - Intelligent, helpful, and personable assistant
- **Task planning through dialogue** - Clarifies requirements before executing
- **Free and locally runnable** - Uses browser's Web Speech API for voice recognition

## Features

### 1. Voice Conversation
- Click the orb or press **Space** to start speaking
- The assistant will respond with both text and voice
- Press **Escape** to cancel recording

### 2. Multi-Language Support

| Language | Code | Speech Recognition | Display |
|----------|------|-------------------|---------|
| English | `en` | en-US, en-GB | English |
| Tamil | `ta` | ta-IN, ta-LK | தமிழ் |
| Sinhala | `si` | si-LK | සිංහල |

### 3. JARVIS Persona
The AI assistant embodies the JARVIS persona:
- Sophisticated and intelligent responses
- Professional yet warm and approachable
- Proactive in understanding user needs
- Clear explanations of complex tasks
- Occasional light wit (never at user's expense)

### 4. Task Planning
JARVIS will:
1. Understand your request
2. Ask clarifying questions ONE AT A TIME
3. Confirm understanding before execution
4. Execute the task through Browser.AI

## Getting Started

### Access the Interface
1. Start the Browser.AI web application
2. Navigate to `/jarvis` endpoint
3. Or click "JARVIS Mode" from the main interface

### Basic Interaction Flow

```
You: "I want to buy headphones"
JARVIS: "Good day! I can help you find headphones. What's your budget range?"

You: "Under $100"
JARVIS: "Excellent! Are you looking for wireless or wired headphones?"

You: "Wireless with noise cancellation"
JARVIS: "Very well. Let me confirm: You'd like wireless noise-cancelling headphones under $100 with good reviews. Shall I proceed?

✅ READY TO EXECUTE
TASK: Find and compare wireless noise-cancelling headphones under $100 with good customer reviews"
```

## Technical Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    JARVIS Interface                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Voice     │  │   Text      │  │  Language   │         │
│  │   Input     │  │   Input     │  │  Selector   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                  │
│         └────────────────┴────────────────┘                  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           VoiceConversationService                    │  │
│  │  ┌────────────────┐  ┌────────────────────────────┐  │  │
│  │  │ ConversationSession │  │ JarvisPersona (Prompts) │  │  │
│  │  └────────┬───────┘  └────────────────────────────┘  │  │
│  │           │                                          │  │
│  │           ▼                                          │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │         LLM (Gemini/OpenAI/etc.)           │     │  │
│  │  └────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              TaskManager + Agent                      │  │
│  │         (Browser Automation Execution)                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Speech Recognition
- Uses browser's **Web Speech API** (free, local processing)
- Supported in Chrome, Edge, Safari, and Opera
- Requires microphone permission
- Works offline for speech recognition (speech synthesis requires network)

### Text-to-Speech
- Uses browser's **Speech Synthesis API** (free, local)
- Voice selection available in settings
- Automatic language detection based on conversation language

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jarvis` | GET | JARVIS interface page |
| `/api/jarvis/session` | POST | Create new session |
| `/api/jarvis/start/<session_id>` | POST | Start conversation |
| `/api/jarvis/message` | POST | Send message to JARVIS |
| `/api/jarvis/language` | POST | Change language |
| `/api/jarvis/execute` | POST | Execute planned task |
| `/api/jarvis/history/<session_id>` | GET | Get conversation history |
| `/api/jarvis/languages` | GET | Get supported languages |

## Configuration

### Environment Variables
```env
# LLM API Key (Gemini recommended for conversation)
GEMINI_API_KEY=your_api_key_here

# Or use OpenAI
OPENAI_API_KEY=your_openai_key
```

### Settings Panel
Access via the ⚙️ icon:
- **LLM Provider**: Select AI model provider
- **API Key**: Configure API key
- **Speech Language**: Set speech recognition language
- **Text-to-Speech**: Enable/disable voice responses
- **TTS Voice**: Select voice for responses

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Toggle voice recording |
| Enter | Send text message |
| Escape | Cancel recording |

## Browser Compatibility

| Browser | Voice Input | Voice Output |
|---------|-------------|--------------|
| Chrome | ✅ Full | ✅ Full |
| Edge | ✅ Full | ✅ Full |
| Safari | ⚠️ Limited | ✅ Full |
| Firefox | ❌ None | ✅ Full |
| Opera | ✅ Full | ✅ Full |

## Examples

### Shopping Task
```
"Find me the best laptop under $1000 for programming"
```

### Research Task
```
"Research the latest developments in AI and create a summary"
```

### Form Automation
```
"Fill out the contact form on example.com with my business details"
```

### Multi-Language Example (Tamil)
```
"$100 க்கு கீழ் ஹெட்போன்கள் கண்டுபிடிக்க உதவுங்கள்"
(Help me find headphones under $100)
```

## Troubleshooting

### Voice Input Not Working
1. Ensure microphone permission is granted
2. Use Chrome or Edge for best compatibility
3. Check that microphone is not in use by another app
4. Try the diagnostic tool in the interface

### No Voice Output
1. Check browser volume settings
2. Ensure Text-to-Speech is enabled in settings
3. Select a compatible voice in settings
4. Try a different TTS voice

### Language Not Recognized
1. Ensure the correct speech recognition language is selected
2. Speak clearly and at normal pace
3. Check for background noise
4. Try switching to text input

## Future Enhancements

- [ ] Offline speech recognition using Whisper
- [ ] Additional language support
- [ ] Voice activity detection
- [ ] Conversation history persistence
- [ ] Custom persona configuration
