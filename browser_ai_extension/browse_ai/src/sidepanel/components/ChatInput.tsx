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
