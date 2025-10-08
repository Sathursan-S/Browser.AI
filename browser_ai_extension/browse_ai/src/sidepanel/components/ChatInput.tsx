import { useState, useEffect } from 'react'
import './ChatInput.css'
import { voiceRecognition } from '../../services/VoiceRecognition'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export const ChatInput = ({ onSendMessage, disabled = false, placeholder }: ChatInputProps) => {
  const [input, setInput] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [voiceError, setVoiceError] = useState<string | null>(null)

  // Initialize voice recognition
  useEffect(() => {
    const isSupported = voiceRecognition.isRecognitionSupported()
    console.log('🎤 Voice Recognition Support Check:', isSupported)
    
    if (isSupported) {
      voiceRecognition.initialize({
        continuous: false,
        interimResults: true,
        language: 'en-US'
      })
      console.log('🎤 Voice Recognition Initialized')
    } else {
      console.warn('🎤 Voice Recognition not available - button will be hidden')
    }

    return () => {
      voiceRecognition.cleanup()
    }
  }, [])

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
      setInterimTranscript('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const toggleVoiceInput = () => {
    if (!voiceRecognition.isRecognitionSupported()) {
      setVoiceError('Voice input not supported in this browser')
      return
    }

    if (isListening) {
      // Stop listening
      voiceRecognition.stopListening()
      setIsListening(false)
      setInterimTranscript('')
    } else {
      // Start listening
      setVoiceError(null)
      setIsListening(true)
      
      voiceRecognition.startListening(
        (result) => {
          if (result.isFinal) {
            // Final result - append to input
            setInput(prev => {
              const newText = prev ? `${prev} ${result.transcript}` : result.transcript
              return newText
            })
            setInterimTranscript('')
          } else {
            // Interim result - show as preview
            setInterimTranscript(result.transcript)
          }
        },
        (error) => {
          setVoiceError(error)
          setIsListening(false)
          setInterimTranscript('')
        },
        () => {
          // Recognition ended
          setIsListening(false)
          setInterimTranscript('')
        }
      )
    }
  }

  const displayText = input + (interimTranscript ? ` ${interimTranscript}` : '')

  return (
    <div className={`chat-input-container ${isFocused ? 'focused' : ''}`}>
      <div className="chat-input-wrapper">
        <textarea
          className="chat-input-field"
          aria-label={placeholder || 'What would you like me to do?'}
          value={displayText}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder || 'What would you like me to do?'}
          rows={3}
          disabled={disabled}
        />
        {voiceError && (
          <div className="voice-error">{voiceError}</div>
        )}
        <div className="chat-input-footer">
          <div className="chat-input-left">
            <span className="chat-hint">
              {disabled ? 'Task is running...' : isListening ? '🎤 Listening...' : 'Press Ctrl+Enter to send'}
            </span>
          </div>
          <div className="chat-input-actions">
            {/* Always show voice button - let it handle unsupported browsers */}
            <button
              className={`voice-btn ${isListening ? 'listening' : ''} ${!voiceRecognition.isRecognitionSupported() ? 'unsupported' : ''}`}
              onClick={toggleVoiceInput}
              disabled={disabled || !voiceRecognition.isRecognitionSupported()}
              title={
                !voiceRecognition.isRecognitionSupported() 
                  ? 'Voice input not supported in CDP mode - use regular Chrome' 
                  : isListening 
                    ? 'Stop listening' 
                    : 'Start voice input'
              }
              aria-label={isListening ? 'Stop listening' : 'Start voice input'}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                {isListening ? (
                  // Stop icon
                  <rect x="6" y="6" width="12" height="12" fill="currentColor" />
                ) : (
                  // Microphone icon
                  <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14ZM17.91 11C17.91 14.39 15.16 17.14 11.77 17.14C8.38 17.14 5.63 14.39 5.63 11H4C4 14.93 7.04 18.16 10.86 18.71V22H13.14V18.71C16.96 18.16 20 14.93 20 11H17.91Z" fill="currentColor" />
                )}
              </svg>
            </button>
            <button
              className="chat-send-btn"
              onClick={handleSubmit}
              disabled={!input.trim() || disabled}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor" />
              </svg>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
