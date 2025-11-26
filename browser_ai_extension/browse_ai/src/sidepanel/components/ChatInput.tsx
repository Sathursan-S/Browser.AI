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
  onListeningChange?: (isListening: boolean) => void // Prop to notify parent
}

export const ChatInput = ({ onSendMessage, onStopTask, onPauseTask, onResumeTask, disabled = false, isRunning = false, isPaused = false, placeholder, enableVoice = true, onListeningChange }: ChatInputProps) => {
  const [input, setInput] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Notify parent of listening state changes
  useEffect(() => {
    if (onListeningChange) {
      onListeningChange(isListening)
    }
  }, [isListening, onListeningChange])

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

      if (isSupported) {
        voiceRecognition.initialize({
          continuous: false,
          interimResults: true,
          language: 'en-US'
        })
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
    <div className={`
      bg-slate-100 dark:bg-slate-800/50
      border border-slate-200 dark:border-slate-700
      rounded-xl overflow-hidden transition-all duration-200
      ${isFocused
        ? 'border-primary/50 ring-2 ring-primary/10 shadow-lg shadow-primary/5'
        : 'hover:border-slate-300 dark:hover:border-slate-600'
      }
    `}>
      <div className="flex items-end gap-2 p-2">
        <textarea
          ref={textareaRef}
          className={`flex-1 min-h-[32px] max-h-[120px] px-3 py-2 border-0 text-sm bg-transparent resize-none outline-none
            placeholder-slate-400 dark:placeholder-slate-500
            disabled:cursor-not-allowed leading-relaxed scrollbar-hide
            ${interimTranscript ? 'text-primary italic' : 'text-slate-900 dark:text-slate-100 disabled:text-slate-500'}
          `}
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
              : isRunning ? 'Task is running...' :
              isPaused ? 'Task is paused...' :
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
          <div className="absolute bottom-full left-0 right-0 mb-1 px-3 py-1 bg-red-100 dark:bg-red-900/50 border border-red-200 dark:border-red-800 rounded-md text-xs text-red-600 dark:text-red-400">
            Voice error: {voiceError}
          </div>
        )}
        <div className="flex gap-1 shrink-0">
          {enableVoice && voiceRecognition.isRecognitionSupported() && (
            <Button
              onClick={toggleVoiceInput}
              disabled={disabled}
              size="sm"
              className={`w-8 h-8 p-0 rounded-lg transition-all duration-200 border ${
                isListening
                  ? 'bg-red-500 text-white border-red-600 hover:bg-red-600 animate-pulse'
                  : 'bg-transparent text-slate-500 dark:text-slate-400 border-transparent hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
              title={isListening ? 'Stop listening' : 'Start voice input'}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
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
               className="w-8 h-8 p-0 rounded-lg bg-blue-500 text-white hover:bg-blue-600 border border-blue-600 shadow-sm"
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
            className={`w-8 h-8 p-0 rounded-lg transition-all duration-200 shadow-sm border ${
              isRunning && !isPaused
                ? 'bg-red-500 hover:bg-red-600 text-white border-red-600 shadow-red-500/20'
                : isPaused
                ? 'bg-green-500 hover:bg-green-600 text-white border-green-600 shadow-green-500/20'
                : 'bg-primary hover:bg-blue-600 text-white border-blue-600 shadow-blue-500/20'
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
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14m-6-6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
