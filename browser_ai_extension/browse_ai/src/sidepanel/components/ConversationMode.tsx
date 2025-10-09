import { useState, useEffect, useRef } from 'react'
import './ConversationMode.css'
import { textToSpeech } from '../../services/TextToSpeech'
import { voiceRecognition } from '../../services/VoiceRecognition'

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
  onSwitchToAgent?: () => void
}

export const ConversationMode = ({ 
  socket, 
  connected, 
  onStartTask, 
  cdpEndpoint,
  messages,
  setMessages,
  intent,
  setIntent,
  onSwitchToAgent
}: ConversationModeProps) => {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeechEnabled, setIsSpeechEnabled] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastSpokenIndexRef = useRef<number>(-1)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Speak new assistant messages when speech is enabled
  useEffect(() => {
    if (!isSpeechEnabled || !textToSpeech.isSynthesisSupported()) return
    
    // Find new assistant messages that haven't been spoken yet
    const assistantMessages = messages.filter(m => m.role === 'assistant')
    const lastMessageIndex = assistantMessages.length - 1
    
    if (lastMessageIndex > lastSpokenIndexRef.current && lastMessageIndex >= 0) {
      const newMessage = assistantMessages[lastMessageIndex]
      
      // Clean up message content (remove markdown, emojis for better speech)
      const cleanText = newMessage.content
        .replace(/\*\*/g, '') // Remove bold markdown
        .replace(/#{1,6}\s/g, '') // Remove headers
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Remove links, keep text
        .replace(/✅|🚀|👋|🎧|🤔|❓/g, '') // Remove common emojis
        .trim()
      
      if (cleanText) {
        setIsSpeaking(true)
        textToSpeech.speak(
          cleanText,
          { rate: 1.0, pitch: 1.0, volume: 0.9 },
          undefined,
          () => {
            setIsSpeaking(false)
          },
          (error) => {
            console.error('Speech error:', error)
            setIsSpeaking(false)
          }
        )
      }
      
      lastSpokenIndexRef.current = lastMessageIndex
    }
  }, [messages, isSpeechEnabled])

  // Cleanup speech when component unmounts
  useEffect(() => {
    return () => {
      textToSpeech.stop()
      voiceRecognition.cleanup()
    }
  }, [])

  // Initialize voice recognition
  useEffect(() => {
    const isSupported = voiceRecognition.isRecognitionSupported()
    console.log('🎤 ConversationMode Voice Recognition Support:', isSupported)
    
    if (isSupported) {
      voiceRecognition.initialize({
        continuous: false,
        interimResults: true,
        language: 'en-US'
      })
      console.log('🎤 ConversationMode Voice Recognition Initialized')
    }
  }, [])

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

  const toggleVoiceInput = async () => {
    if (!voiceRecognition.isRecognitionSupported()) {
      setVoiceError('Voice input not supported in this browser')
      return
    }

    try {
      if (isListening) {
        // Stop listening
        voiceRecognition.stopListening()
        setIsListening(false)
        setInterimTranscript('')
        setVoiceError(null)
      } else {
        // Start listening
        setVoiceError(null)
        await voiceRecognition.startListening(
          (result) => {
            if (result.isFinal) {
              // Append final transcript to input
              setInput(prev => (prev + ' ' + result.transcript).trim())
              setInterimTranscript('')
            } else {
              // Show interim transcript
              setInterimTranscript(result.transcript)
            }
          },
          (error) => {
            setVoiceError(error)
            setIsListening(false)
            setInterimTranscript('')
          }
        )
        setIsListening(true)
      }
    } catch (error) {
      console.error('Voice recognition error:', error)
      setVoiceError('Failed to start voice recognition')
      setIsListening(false)
    }
  }

  const handleResetConversation = () => {
    socket.emit('reset_conversation')
    setIntent(null)
    textToSpeech.stop()
    lastSpokenIndexRef.current = -1
    // Switch to agent mode after reset
    if (onSwitchToAgent) {
      onSwitchToAgent()
    }
  }

  const toggleSpeech = () => {
    if (isSpeechEnabled) {
      // Turning off - stop any ongoing speech
      textToSpeech.stop()
      setIsSpeaking(false)
    }
    setIsSpeechEnabled(!isSpeechEnabled)
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
        {voiceError && (
          <div className="voice-error-message">{voiceError}</div>
        )}
        <div className="relative">
          <textarea
            className="chat-input-with-buttons"
            value={input + (interimTranscript ? ' ' + interimTranscript : '')}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isProcessing ? "Assistant is typing..." : isListening ? "🎤 Listening..." : "Type your message... (Ctrl+Enter to send)"}
            rows={3}
            disabled={!connected || isProcessing}
          />
          <div className="absolute right-2 bottom-2 flex gap-2">
            {voiceRecognition.isRecognitionSupported() && (
              <button
                className={`input-action-btn voice-btn ${isListening ? 'listening' : ''}`}
                onClick={toggleVoiceInput}
                disabled={!connected || isProcessing}
                title={isListening ? 'Stop listening' : 'Start voice input'}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  {isListening ? (
                    <rect x="6" y="6" width="12" height="12" fill="currentColor" />
                  ) : (
                    <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" fill="currentColor" />
                  )}
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1m7 9v3m-3 0h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
              </button>
            )}
            <button 
              className="input-action-btn send-btn"
              onClick={handleSendMessage}
              disabled={!input.trim() || !connected || isProcessing}
              title="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
