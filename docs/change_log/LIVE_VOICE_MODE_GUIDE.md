# 🎙️ Live Voice Mode - Hands-Free Conversation

## Overview

The Live Voice Mode transforms Browser.AI's voice chat into a natural, hands-free conversation experience similar to Gemini Live or ChatGPT Voice Mode. No more clicking buttons - just speak naturally and have a real conversation with your AI assistant!

## ✨ Key Features

### 1. **Automatic Turn-Taking**
- **Auto-send on silence**: Your message is automatically sent after you stop speaking (1.5 second pause)
- **No manual clicking**: Say what you want, pause, and the AI responds automatically
- **Continuous listening**: After the AI speaks, it automatically starts listening again

### 2. **Natural Interruption**
- **Interrupt the AI**: Start speaking while the AI is talking to interrupt it
- **Immediate response**: The AI stops speaking and starts listening when you begin talking
- **Fluid conversation**: Have natural back-and-forth without waiting for complete responses

### 3. **Visual Feedback**
The status bar shows exactly what's happening:
- **🎤 Listening** (Blue pulse): AI is waiting for you to speak
- **🤔 Processing** (Orange pulse): AI is thinking about your message
- **🔊 Speaking** (Green pulse): AI is responding to you
- **⏸️ Idle** (Gray): Conversation is paused

### 4. **Live Transcript Display**
- See your words in real-time as you speak
- Interim results update as you talk
- Final transcript before sending

## 🚀 How to Use

### Starting Live Voice Mode

1. **Click "Go Live" button** in the conversation header
   - The button turns red with a pulsing animation when active
   - Status bar appears showing current state

2. **Start speaking naturally**
   - Just talk - no need to hold any buttons
   - Pause for 1.5 seconds when you're done
   - Your message is automatically sent

3. **Listen to the response**
   - AI speaks the response automatically
   - After speaking, it starts listening again
   - You can interrupt at any time by speaking

4. **Exit when done**
   - Click "Exit Live Mode" button
   - Returns to normal text/manual voice input mode

### Tips for Best Results

✅ **DO:**
- Speak clearly and at a normal pace
- Pause naturally when you finish a thought
- Let complete sentences finish before the 1.5s timeout
- Interrupt the AI if it's going off-track

❌ **DON'T:**
- Don't speak too quickly without pauses
- Don't stop mid-sentence (wait for natural breaks)
- Don't forget you're in Live Mode (no typing needed!)

## 🎯 Use Cases

### Perfect for:
- **Hands-free browsing**: Control Browser.AI while doing other tasks
- **Quick queries**: Fast back-and-forth without clicking
- **Natural exploration**: Discover what Browser.AI can do conversationally
- **Accessibility**: Great for users who prefer voice over typing
- **Multitasking**: Talk to AI while looking at the browser

### Examples:
```
👤 "Find the best deals on laptops under $1000"
🤖 [AI speaks and shows results]
👤 "Filter for gaming laptops only"
🤖 [AI refines search]
👤 "Add the top one to my cart"
🤖 [AI adds to cart and confirms]
```

## ⚙️ Technical Details

### Configuration
Default settings (can be customized in `VoiceConversation.ts`):
```typescript
{
  autoSendOnFinal: true,        // Auto-send when user stops
  silenceThreshold: 1500,       // ms before considering speech ended
  autoRestartListening: true,   // Restart after bot speaks
  interruptOnSpeech: true,      // Allow user to interrupt
  language: 'en-US',            // Speech recognition language
  speechRate: 1.0,              // TTS speaking rate
  speechPitch: 1.0,             // TTS pitch
  speechVolume: 0.9             // TTS volume
}
```

### Browser Support
Requires both:
- ✅ Web Speech API (Speech Recognition)
- ✅ Speech Synthesis API (Text-to-Speech)

**Supported Browsers:**
- ✅ Chrome/Edge (Full support)
- ✅ Safari (Full support)
- ❌ Firefox (Limited - no continuous recognition)
- ❌ CDP Mode (Use regular Chrome for voice features)

### State Flow
```
┌─────────┐
│  Idle   │◄────────────────────┐
└────┬────┘                     │
     │ User clicks "Go Live"    │
     ▼                          │
┌──────────┐                    │
│Listening │◄────────┐          │
└────┬─────┘         │          │
     │ Speech ends   │          │
     ▼               │          │
┌───────────┐        │          │
│Processing │        │          │
└────┬──────┘        │          │
     │ Response ready│          │
     ▼               │          │
┌─────────┐          │          │
│Speaking │──────────┘          │
└────┬────┘                     │
     │ Speech complete          │
     │ Auto-restart listening   │
     ├──────────────────────────┘
     │ OR User exits
     └──────────────► [Exit]
```

## 🔧 Implementation Architecture

### Core Components

1. **VoiceConversation.ts** - Orchestration service
   - Manages conversation state machine
   - Handles auto-send logic with silence detection
   - Coordinates between STT and TTS
   - Implements interruption handling

2. **ConversationMode.tsx** - UI integration
   - Live voice mode toggle
   - State visualization
   - Real-time transcript display
   - Message auto-sending

3. **VoiceRecognition.ts** - Speech-to-Text
   - Continuous listening mode
   - Interim and final results
   - Error handling

4. **TextToSpeech.ts** - Text-to-Speech
   - Natural voice synthesis
   - Female voice preference
   - Interrupt support

### Key Features Implementation

#### Auto-Send on Silence
```typescript
// When final transcript received
if (result.isFinal) {
  pendingTranscript += result.transcript
  
  // Wait for silence threshold (1.5s)
  setTimeout(() => {
    if (pendingTranscript.trim()) {
      sendMessage(pendingTranscript)
    }
  }, 1500)
}
```

#### Interruption Handling
```typescript
// If user speaks while bot is talking
if (state === 'speaking' && interruptOnSpeech) {
  textToSpeech.stop()
  updateState('listening')
}
```

#### Auto-Restart Listening
```typescript
// After bot finishes speaking
textToSpeech.speak(message, options, undefined, () => {
  if (autoRestartListening) {
    setTimeout(() => {
      startListening()
    }, 500) // Small delay for natural transition
  }
})
```

## 🎨 UI/UX Design

### Visual States
- **Pulsing indicators**: Show active state (listening/processing/speaking)
- **Color coding**: Blue (listening), Orange (processing), Green (speaking)
- **Live transcript**: Real-time feedback of what you're saying
- **Prominent toggle**: Easy to see when in Live Mode

### Accessibility
- Clear visual indicators for deaf/hard-of-hearing users
- Keyboard shortcut support could be added
- Screen reader compatible status updates

## 📊 Benefits Over Manual Mode

| Feature | Manual Mode | Live Voice Mode |
|---------|-------------|-----------------|
| Click to send | ✅ Required | ❌ Automatic |
| Voice button | ✅ Hold/Click | ❌ Always listening |
| Interruption | ❌ Not possible | ✅ Supported |
| Hands-free | ❌ No | ✅ Yes |
| Speed | ⚡ Slower | ⚡⚡⚡ Much faster |
| Natural feel | 🤖 Robotic | 💬 Conversational |

## 🐛 Troubleshooting

### "Voice input not supported"
- **Cause**: CDP mode or unsupported browser
- **Solution**: Use regular Chrome (not via CDP endpoint)

### "Auto-send not working"
- **Cause**: Speaking too continuously without pauses
- **Solution**: Pause for 1.5 seconds after completing your thought

### "Can't interrupt AI"
- **Cause**: Microphone not detecting voice
- **Solution**: Check mic permissions and volume

### "AI keeps listening but not responding"
- **Cause**: Silence threshold too long
- **Solution**: Be patient or adjust `silenceThreshold` config

## 🔮 Future Enhancements

Potential improvements:
- [ ] Configurable silence threshold in UI
- [ ] Voice activity detection visualization (waveform)
- [ ] Multiple language support toggle
- [ ] Voice speed/pitch controls
- [ ] Keyboard shortcut to toggle (e.g., Space to talk)
- [ ] Push-to-talk option in Live Mode
- [ ] Background noise cancellation
- [ ] Emotion detection in voice
- [ ] Multi-turn context preservation
- [ ] Voice commands (e.g., "stop", "repeat", "go back")

## 📝 Code Example

### Using Live Voice Mode Programmatically

```typescript
import { voiceConversation } from '../../services/VoiceConversation'

// Start live voice mode
voiceConversation.start(
  // State changes
  (stateInfo) => {
    console.log('State:', stateInfo.state)
    console.log('Transcript:', stateInfo.transcript)
  },
  
  // Message ready to send
  (message) => {
    console.log('Sending:', message)
    sendToBackend(message)
  },
  
  // Errors
  (error) => {
    console.error('Error:', error)
  }
)

// When bot responds
voiceConversation.handleBotResponse(botMessage)

// Stop when done
voiceConversation.stop()
```

## 🎓 Lessons Learned

### Design Decisions

1. **1.5s silence threshold**: 
   - Short enough to feel responsive
   - Long enough to allow natural pauses in speech
   
2. **Auto-restart listening**:
   - Creates truly continuous conversation
   - Reduces cognitive load on user
   
3. **Interrupt support**:
   - Critical for natural conversation flow
   - Prevents frustration with long AI responses
   
4. **Visual state indicators**:
   - Users need to know what the system is doing
   - Pulsing animations create sense of "aliveness"

### Challenges Solved

- ✅ Preventing message fragments from being sent too early
- ✅ Handling overlapping speech (user + AI)
- ✅ Managing state transitions smoothly
- ✅ Browser API limitations (continuous recognition)
- ✅ Cleanup on mode exit

---

**Built with ❤️ for natural AI conversations**

*Part of Browser.AI Extension - Making the web accessible to AI agents*
