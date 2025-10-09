import { useState, useRef, useEffect } from 'react'
import { Button } from '../../ui/Button'
import { voiceRecognition } from '../../services/VoiceRecognition'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  onStopTask?: () => void
  onPauseTask?: () => void
  onResumeTask?: () => void
  disabled?: boolean
  isRunning?: boolean
  isPaused?: boolean
  placeholder?: string
  enableVoice?: boolean // Optional voice input toggle
}

export const ChatInput = ({ onSendMessage, onStopTask, onPauseTask, onResumeTask, disabled = false, isRunning = false, isPaused = false, placeholder, enableVoice = true }: ChatInputProps) => {
  const [input, setInput] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [voiceError, setVoiceError] = useState<string | null>(null)
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

  // Initialize voice recognition
  useEffect(() => {
    if (enableVoice) {
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
    }

    return () => {
      if (enableVoice) {
        voiceRecognition.cleanup()
      }
    }
  }, [enableVoice])

  const handleSubmit = () => {
    if (isRunning && onStopTask) {
      onStopTask()
    } else if (isPaused && onResumeTask) {
      onResumeTask()
    } else if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
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

  // Voice input handler
  const toggleVoiceInput = () => {
    if (!enableVoice || !voiceRecognition.isRecognitionSupported()) {
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
            setInput(prev => (prev + ' ' + result.transcript).trim())
            setInterimTranscript('')
          } else {
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
          className={`flex-1 min-h-[32px] max-h-[120px] px-3 py-2 border-0 text-sm bg-transparent resize-none outline-none placeholder-white/50 disabled:cursor-not-allowed leading-relaxed scrollbar-hide ${
            interimTranscript ? 'text-blue-400 italic' : 'text-white disabled:text-white/50'
          }`}
          aria-label={placeholder || 'What would you like me to do?'}
          value={interimTranscript || input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={
            disabled
              ? "Agent is running..."
              : isListening
              ? "Listening... Speak now or click the mic to stop"
              : isRunning ? 'Task is running... Click Stop to cancel' :
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
          <div className="absolute bottom-full left-0 right-0 mb-1 px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-md text-xs text-red-400">
            Voice error: {voiceError}
          </div>
        )}
        <div className="flex gap-1 shrink-0">
          {enableVoice && voiceRecognition.isRecognitionSupported() && (
            <Button
              onClick={toggleVoiceInput}
              disabled={disabled}
              size="sm"
              className={`w-8 h-8 p-0 transition-all duration-200 shadow-lg border ${
                isListening
                  ? 'bg-gradient-to-r from-[#f44336] to-[#d32f2f] hover:from-[#d32f2f] hover:to-[#c62828] text-white shadow-red-500/30 border-red-400/30 animate-pulse'
                  : 'bg-gradient-to-r from-[#9c27b0] to-[#7b1fa2] hover:from-[#7b1fa2] hover:to-[#6a1b9a] text-white shadow-purple-500/30 border-purple-400/30'
              }`}
              title={isListening ? 'Stop listening' : 'Start voice input'}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                {isListening ? (
                  <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
                ) : (
                  <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" fill="currentColor" />
                )}
                <path d="M19 10v1a7 7 0 0 1-14 0v-1m7 9v3m-3 0h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
              </svg>
            </Button>
          )}
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
