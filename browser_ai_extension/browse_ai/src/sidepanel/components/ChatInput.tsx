import { useState, useEffect } from 'react'
import './ChatInput.css'
import { voiceRecognition } from '../../services/VoiceRecognition'
import { useState, useRef, useEffect } from 'react'
import { Button } from '../../ui/Button'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  onStopTask?: () => void
  onPauseTask?: () => void
  onResumeTask?: () => void
  disabled?: boolean
  isRunning?: boolean
  isPaused?: boolean
  placeholder?: string
}

export const ChatInput = ({ onSendMessage, onStopTask, onPauseTask, onResumeTask, disabled = false, isRunning = false, isPaused = false, placeholder }: ChatInputProps) => {
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
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Hide scrollbar styles
  useEffect(() => {
    const styleElement = document.createElement('style')
    styleElement.textContent = `
      .scrollbar-hide::-webkit-scrollbar {
        display: none;
      }
      
      .scrollbar-hide {
        -ms-overflow-style: none;
        scrollbar-width: none;
      }
    `
    document.head.appendChild(styleElement)

    return () => {
      if (document.head.contains(styleElement)) {
        document.head.removeChild(styleElement)
      }
    }
  }, [])

  const handleSubmit = () => {
    if (isRunning && onStopTask) {
      onStopTask()
    } else if (isPaused && onResumeTask) {
      onResumeTask()
    } else if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
      setInterimTranscript('')
    }
  }

  const handlePause = () => {
    if (isRunning && onPauseTask) {
      onPauseTask()
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
  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  // Reset height when input is cleared
  useEffect(() => {
    if (input === '' && textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [input])

  return (
    <div className={`bg-white/10 border border-white/20 rounded-lg overflow-hidden transition-all duration-200 backdrop-blur-sm ${
      isFocused 
        ? 'border-white/30 shadow-lg shadow-black/20' 
        : 'shadow-md shadow-black/10'
    }`}>
      <div className="flex items-end gap-2 p-2">
        <textarea
          ref={textareaRef}
          className="flex-1 min-h-[32px] max-h-[120px] px-3 py-2 border-0 text-sm text-white bg-transparent resize-none outline-none placeholder-white/50 disabled:cursor-not-allowed disabled:text-white/50 leading-relaxed scrollbar-hide"
          aria-label={placeholder || 'What would you like me to do?'}
          value={displayText}
          onChange={(e) => setInput(e.target.value)}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={
            isRunning ? 'Task is running... Click Stop to cancel' : 
            isPaused ? 'Task is paused... Click Resume to continue' : 
            placeholder || 'What would you like me to do?'
          }
          rows={1}
          disabled={disabled || (isRunning && !isPaused)}
          style={{ 
            height: 'auto',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none'
          }}
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
        <div className="flex gap-1 shrink-0">
          {isRunning && !isPaused && (
            <Button
              onClick={handlePause}
              size="sm"
              className="w-8 h-8 p-0 transition-all duration-200 bg-gradient-to-r from-[#2196f3] to-[#1976d2] hover:from-[#1976d2] hover:to-[#1565c0] text-white shadow-lg shadow-blue-500/30 border border-blue-400/30"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" />
                <rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" />
              </svg>
            </Button>
          )}
          <Button
            onClick={handleSubmit}
            disabled={!isRunning && !isPaused && (!input.trim() || disabled)}
            size="sm"
            className={`w-8 h-8 p-0 transition-all duration-200 shadow-lg border ${
              isRunning && !isPaused
                ? 'bg-gradient-to-r from-[#f44336] to-[#d32f2f] hover:from-[#d32f2f] hover:to-[#c62828] text-white shadow-red-500/30 border-red-400/30' 
                : isPaused
                ? 'bg-gradient-to-r from-[#4caf50] to-[#388e3c] hover:from-[#388e3c] hover:to-[#2e7d32] text-white shadow-green-500/30 border-green-400/30'
                : 'bg-gradient-to-r from-[#2196f3] to-[#1976d2] hover:from-[#1976d2] hover:to-[#1565c0] text-white shadow-blue-500/30 border-blue-400/30'
            }`}
          >
            {isRunning && !isPaused ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
              </svg>
            ) : isPaused ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <polygon points="8,5 19,12 8,19" fill="currentColor" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor" />
              </svg>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
