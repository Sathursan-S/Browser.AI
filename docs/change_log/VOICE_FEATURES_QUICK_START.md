# Voice Features - Quick Start Guide

## For Users 👥

### Using Voice Input 🎤

1. **Start Voice Input**:
   - Click the microphone icon (🎤) in the chat input box
   - Browser will ask for microphone permission (first time only)
   - Button turns red and pulses when ready

2. **Speak Your Command**:
   - Speak clearly: "Buy wireless headphones under $100"
   - You'll see your words appear in light gray as you speak
   - Stop speaking when done

3. **Review & Send**:
   - Your spoken text appears in the input box
   - You can edit it if needed
   - Click "Send" or press Ctrl+Enter

4. **Stop Listening**:
   - Click the red pulsing button to stop
   - Or just stop speaking - it will auto-stop

### Using Speech Output 🔊

1. **Enable Voice Responses**:
   - Click the speaker icon (🔊) in the conversation header
   - Button turns purple when active
   - Assistant responses will now be spoken aloud

2. **Listen to Responses**:
   - Assistant messages are automatically read aloud
   - Speaker icon animates while speaking
   - You can still read the text while listening

3. **Disable if Needed**:
   - Click purple speaker icon to turn off
   - Speech stops immediately

### Tips for Best Results:

✅ **DO**:
- Speak clearly and at normal pace
- Use in quiet environment
- Allow microphone permission
- Wait for red button before speaking

❌ **DON'T**:
- Speak too fast or too slow
- Use in noisy environment
- Speak while button is gray

---

## For Developers 💻

### Quick Integration

#### 1. Voice Input (Speech-to-Text)

```typescript
import { voiceRecognition } from './services/VoiceRecognition'

// Initialize
useEffect(() => {
  voiceRecognition.initialize({
    continuous: false,
    interimResults: true,
    language: 'en-US'
  })
  
  return () => voiceRecognition.cleanup()
}, [])

// Start/Stop
const toggleVoiceInput = () => {
  if (isListening) {
    voiceRecognition.stopListening()
  } else {
    voiceRecognition.startListening(
      (result) => {
        if (result.isFinal) {
          setText(prev => prev + ' ' + result.transcript)
        } else {
          setInterimText(result.transcript)
        }
      },
      (error) => setError(error)
    )
  }
}
```

#### 2. Speech Output (Text-to-Speech)

```typescript
import { textToSpeech } from './services/TextToSpeech'

// Speak text
const speakMessage = (text: string) => {
  textToSpeech.speak(
    text,
    { rate: 1.0, pitch: 1.0, volume: 0.9 },
    undefined,
    () => console.log('Done'),
    (error) => console.error(error)
  )
}

// Control playback
textToSpeech.pause()
textToSpeech.resume()
textToSpeech.stop()

// Cleanup
useEffect(() => {
  return () => textToSpeech.stop()
}, [])
```

### API Reference

#### VoiceRecognition

| Method | Parameters | Description |
|--------|-----------|-------------|
| `initialize(options)` | `VoiceRecognitionOptions` | Setup recognition parameters |
| `startListening(onResult, onError, onEnd)` | Callbacks | Start voice recognition |
| `stopListening()` | - | Stop recognition |
| `isRecognitionSupported()` | - | Check browser support |
| `getIsListening()` | - | Check if currently listening |
| `cleanup()` | - | Clean up resources |

#### TextToSpeech

| Method | Parameters | Description |
|--------|-----------|-------------|
| `speak(text, options, onProgress, onEnd, onError)` | Text + options + callbacks | Speak text |
| `pause()` | - | Pause current speech |
| `resume()` | - | Resume paused speech |
| `stop()` | - | Stop current speech |
| `isSynthesisSupported()` | - | Check browser support |
| `getIsSpeaking()` | - | Check if currently speaking |
| `getVoices()` | - | Get available voices |

### Common Patterns

#### Auto-speak New Messages

```typescript
const [lastSpokenIndex, setLastSpokenIndex] = useState(-1)

useEffect(() => {
  if (!speechEnabled) return
  
  const newMessages = messages.filter(m => m.role === 'assistant')
  const latestIndex = newMessages.length - 1
  
  if (latestIndex > lastSpokenIndex) {
    textToSpeech.speak(newMessages[latestIndex].content)
    setLastSpokenIndex(latestIndex)
  }
}, [messages, speechEnabled])
```

#### Clean Text for Speech

```typescript
const cleanForSpeech = (text: string) => {
  return text
    .replace(/\*\*/g, '')                          // Remove bold
    .replace(/#{1,6}\s/g, '')                      // Remove headers
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')     // Links → text
    .replace(/[🎤🔊✅🚀👋❓]/g, '')                  // Remove emojis
    .trim()
}
```

#### Error Handling

```typescript
voiceRecognition.startListening(
  (result) => handleResult(result),
  (error) => {
    switch(error) {
      case 'no-speech':
        showMessage('Please speak into the microphone')
        break
      case 'not-allowed':
        showMessage('Please allow microphone access')
        break
      default:
        showMessage('Voice recognition error')
    }
  }
)
```

### Styling

#### Voice Button States

```css
.voice-btn {
  background: #f3f4f6;
  color: #6b7280;
}

.voice-btn.listening {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}
```

#### Speech Toggle States

```css
.speech-toggle-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.speech-toggle-btn.active svg {
  animation: soundWave 1s infinite;
}

@keyframes soundWave {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

### Browser Support Check

```typescript
// Component-level check
const VoiceFeatures = () => {
  const hasVoiceInput = voiceRecognition.isRecognitionSupported()
  const hasSpeechOutput = textToSpeech.isSynthesisSupported()
  
  return (
    <>
      {hasVoiceInput && <VoiceInputButton />}
      {hasSpeechOutput && <SpeechToggle />}
    </>
  )
}
```

### TypeScript Types

```typescript
interface VoiceRecognitionOptions {
  continuous?: boolean
  interimResults?: boolean
  language?: string
  maxAlternatives?: number
}

interface VoiceRecognitionResult {
  transcript: string
  isFinal: boolean
  confidence: number
}

interface TextToSpeechOptions {
  voice?: SpeechSynthesisVoice
  rate?: number        // 0.1 to 10
  pitch?: number       // 0 to 2
  volume?: number      // 0 to 1
  lang?: string
}
```

### Testing

```typescript
// Unit test example
describe('VoiceRecognition', () => {
  it('should detect browser support', () => {
    expect(voiceRecognition.isRecognitionSupported()).toBeDefined()
  })
  
  it('should handle microphone permission denial', () => {
    const errorHandler = jest.fn()
    voiceRecognition.startListening(
      () => {},
      errorHandler
    )
    // Simulate permission denial
    expect(errorHandler).toHaveBeenCalledWith(
      expect.stringContaining('Microphone access denied')
    )
  })
})
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Mic button not showing | Check `voiceRecognition.isRecognitionSupported()` |
| "Permission denied" | Allow mic access in browser settings |
| No sound output | Check volume, unmute browser tab |
| Speech too fast/slow | Adjust `rate` in options (0.5 = half speed, 2 = double) |
| Wrong language | Set `lang: 'en-GB'` or other BCP-47 code |
| Interim text not showing | Set `interimResults: true` |

### Debug Mode

```typescript
// Enable verbose logging
voiceRecognition.startListening(
  (result) => {
    console.log('Recognition result:', {
      text: result.transcript,
      final: result.isFinal,
      confidence: result.confidence
    })
  },
  (error) => console.error('Recognition error:', error),
  () => console.log('Recognition ended')
)
```

---

## Examples

### Complete Voice-Enabled Chat

```typescript
import { useState, useEffect } from 'react'
import { voiceRecognition } from './services/VoiceRecognition'
import { textToSpeech } from './services/TextToSpeech'

export const VoiceChat = () => {
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechEnabled, setSpeechEnabled] = useState(false)
  const [messages, setMessages] = useState([])

  // Initialize
  useEffect(() => {
    if (voiceRecognition.isRecognitionSupported()) {
      voiceRecognition.initialize({
        continuous: false,
        interimResults: true,
        language: 'en-US'
      })
    }
    return () => {
      voiceRecognition.cleanup()
      textToSpeech.stop()
    }
  }, [])

  // Auto-speak responses
  useEffect(() => {
    if (!speechEnabled) return
    const lastMessage = messages[messages.length - 1]
    if (lastMessage?.role === 'assistant') {
      textToSpeech.speak(lastMessage.content)
    }
  }, [messages, speechEnabled])

  const toggleVoice = () => {
    if (isListening) {
      voiceRecognition.stopListening()
      setIsListening(false)
    } else {
      setIsListening(true)
      voiceRecognition.startListening(
        (result) => {
          if (result.isFinal) {
            setInput(prev => prev + ' ' + result.transcript)
          }
        },
        (error) => alert(error),
        () => setIsListening(false)
      )
    }
  }

  return (
    <div>
      <input value={input} onChange={e => setInput(e.target.value)} />
      <button onClick={toggleVoice}>
        {isListening ? 'Stop' : 'Start'} Voice
      </button>
      <button onClick={() => setSpeechEnabled(!speechEnabled)}>
        {speechEnabled ? 'Mute' : 'Unmute'} Responses
      </button>
    </div>
  )
}
```

---

## Resources

- [Web Speech API Docs](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Browser Compatibility](https://caniuse.com/speech-recognition)
- [BCP-47 Language Codes](https://www.techonthenet.com/js/language_tags.php)
- [SpeechSynthesis Voices](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice)

---

**Made with ❤️ for Browser.AI**
