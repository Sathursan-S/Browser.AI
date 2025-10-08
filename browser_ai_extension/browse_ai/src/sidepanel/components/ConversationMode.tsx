import { useState, useEffect, useRef } from 'react'
import './ConversationMode.css'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface Intent {
  task_description: string
  is_ready: boolean
  confidence: number
}

interface ConversationModeProps {
  socket: any
  connected: boolean
  onStartTask: (task: string, cdpEndpoint: string) => void
  cdpEndpoint: string
  messages: Message[]
  setMessages: (messages: Message[]) => void
  intent: Intent | null
  setIntent: (intent: Intent | null) => void
}

export const ConversationMode = ({ 
  socket, 
  connected, 
  onStartTask, 
  cdpEndpoint,
  messages,
  setMessages,
  intent,
  setIntent 
}: ConversationModeProps) => {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Listen for chatbot responses
  useEffect(() => {
    if (!socket) return

    const handleChatResponse = (data: { role: string; content: string; intent?: Intent }) => {
      setIsProcessing(false)
      
      const message: Message = {
        role: data.role as 'user' | 'assistant',
        content: data.content,
        timestamp: new Date().toISOString()
      }
      
      setMessages([...messages, message])
      
      if (data.intent && data.intent.is_ready) {
        setIntent(data.intent)
      }
    }

    const handleConversationReset = (data: { role: string; content: string }) => {
      setMessages([{
        role: data.role as 'assistant',
        content: data.content,
        timestamp: new Date().toISOString()
      }])
      setIntent(null)
    }

    const handleAgentNeedsHelp = (data: {
      reason: string
      summary: string
      attempted_actions: string[]
      duration: number
      suggestion: string
    }) => {
      // Add help request as assistant message
      const helpMessage: Message = {
        role: 'assistant',
        content: data.summary,
        timestamp: new Date().toISOString()
      }
      
      setMessages([...messages, helpMessage])
      setIsProcessing(false)
    }

    socket.on('chat_response', handleChatResponse)
    socket.on('conversation_reset', handleConversationReset)
    socket.on('agent_needs_help', handleAgentNeedsHelp)

    // Initial greeting when connected
    if (connected && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: '👋 Hi! I\'m your Browser.AI assistant. What would you like me to help you automate today? I can help with shopping, downloads, research, form filling, and more!',
        timestamp: new Date().toISOString()
      }])
    }

    return () => {
      socket.off('chat_response', handleChatResponse)
      socket.off('conversation_reset', handleConversationReset)
      socket.off('agent_needs_help', handleAgentNeedsHelp)
    }
  }, [socket, connected, messages, setMessages, setIntent])

  const handleSendMessage = () => {
    if (!input.trim() || !connected || isProcessing) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages([...messages, userMessage])
    setIsProcessing(true)

    // Check if last message was a help request (contains "🤔 **The agent appears to be stuck**")
    const lastMessage = messages[messages.length - 1]
    const isHelpRequest = lastMessage && lastMessage.content.includes('🤔 **The agent appears to be stuck**')

    if (isHelpRequest) {
      // Send as help response
      socket.emit('user_help_response', { response: input.trim() })
    } else {
      // Send as regular chat message
      socket.emit('chat_message', { message: input.trim() })
    }
    
    setInput('')
  }

  const handleStartAutomation = () => {
    if (!intent) return

    // Start the automation task
    socket.emit('start_clarified_task', {
      task: intent.task_description,
      cdp_endpoint: cdpEndpoint,
      is_extension: true
    })

    // Clear intent after starting
    setIntent(null)
    
    // Add confirmation message
    setMessages([...messages, {
      role: 'assistant',
      content: '🚀 Perfect! Starting the automation now...',
      timestamp: new Date().toISOString()
    }])
  }

  const handleResetConversation = () => {
    socket.emit('reset_conversation')
    setIntent(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user'
    
    // Check if this is a "ready to start" message
    const isReadyMessage = message.content.includes('✅ READY TO START')
    const parts = isReadyMessage ? message.content.split('TASK:') : [message.content]
    const conversationPart = parts[0].replace('✅ READY TO START', '').trim()
    const taskPart = parts[1]?.trim()
    
    return (
      <div key={index} className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
        <div className={`message-bubble ${isUser ? 'user-message' : 'assistant-message'}`}>
          {isReadyMessage ? (
            <>
              <div className="conversation-text">{conversationPart}</div>
              {taskPart && (
                <div className="task-preview">
                  <div className="task-label">Proposed Task:</div>
                  <div className="task-text">{taskPart}</div>
                </div>
              )}
            </>
          ) : (
            <div className="message-text">{message.content}</div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="conversation-mode">
      <div className="conversation-header">
        <h3>🤖 Chat with Browser.AI Assistant</h3>
        <button 
          className="reset-btn"
          onClick={handleResetConversation}
          disabled={!connected || isProcessing}
          title="Start new conversation"
        >
          🔄 Reset
        </button>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => renderMessage(msg, idx))}
        {isProcessing && (
          <div className="message-wrapper assistant">
            <div className="message-bubble assistant-message typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {intent && intent.is_ready && (
        <div className="intent-confirmation">
          <div className="intent-message">
            ✅ Ready to start automation!
            <div className="confidence">Confidence: {(intent.confidence * 100).toFixed(0)}%</div>
          </div>
          <button 
            className="start-automation-btn"
            onClick={handleStartAutomation}
            disabled={!connected}
          >
            🚀 Start Automation
          </button>
        </div>
      )}

      <div className="input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isProcessing ? "Assistant is typing..." : "Type your message... (Ctrl+Enter to send)"}
          rows={3}
          disabled={!connected || isProcessing}
        />
        <button 
          className="send-btn"
          onClick={handleSendMessage}
          disabled={!input.trim() || !connected || isProcessing}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor" />
          </svg>
          Send
        </button>
      </div>

      <div className="conversation-hints">
        <div className="hint">💡 <strong>Tip:</strong> Be specific about what you want to automate</div>
        <div className="hint">📝 The assistant will ask clarifying questions if needed</div>
      </div>
    </div>
  )
}
