import { useState } from 'react'
import './ChatInput.css'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export const ChatInput = ({ onSendMessage, disabled = false, placeholder }: ChatInputProps) => {
  const [input, setInput] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className={`chat-input-container ${isFocused ? 'focused' : ''}`}>
      <div className="chat-input-wrapper">
        <textarea
          className="chat-input-field"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder || 'What would you like me to do?'}
          rows={3}
          disabled={disabled}
        />
        <div className="chat-input-footer">
          <span className="chat-hint">
            {disabled ? 'Task is running...' : 'Press Ctrl+Enter to send'}
          </span>
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
  )
}
