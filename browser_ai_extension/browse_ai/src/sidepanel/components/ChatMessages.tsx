import React from 'react'

export interface ChatMessage {
  id: string
  content: string
  type: 'user' | 'assistant' | 'system'
  timestamp: Date
  isLoading?: boolean
}

interface ChatMessagesProps {
  messages: ChatMessage[]
  isTyping?: boolean
}

const LoadingDots = () => {
  return (
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  )
}

const TypingIndicator = ({ texts }: { texts: string[] }) => {
  const [currentTextIndex, setCurrentTextIndex] = React.useState(0)

  React.useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTextIndex((prev) => (prev + 1) % texts.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [texts])

  return (
    <div className="flex items-center space-x-3 text-white/70">
      <LoadingDots />
      <span className="text-sm animate-pulse">{texts[currentTextIndex]}</span>
    </div>
  )
}

// Helper function to check if message is JSON-like technical output
const isJsonTechnicalMessage = (content: string): boolean => {
  // Filter out JSON action results
  if (content.includes('🛠️') && content.includes('Action') && content.includes('{"')) {
    return true
  }
  
  // Filter out pure JSON responses
  if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
    try {
      JSON.parse(content.trim())
      return true
    } catch {
      return false
    }
  }
  
  // Filter out technical log messages with JSON
  if (content.includes('{"done":') || content.includes('{"success":') || content.includes('{"error":')) {
    return true
  }
  
  // Filter out "Starting task" messages
  if (content.includes('Starting task:')) {
    return true
  }
  
  return false
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, isTyping = false }) => {
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const scrollContainerRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (scrollContainer) {
      // Scroll to bottom using scrollTop for better control
      scrollContainer.scrollTop = scrollContainer.scrollHeight
    }
  }, [messages, isTyping])

  const loadingTexts = [
    'Thinking...',
    'Analyzing page...',
    'Working on your request...',
    'Processing...',
    'Almost done...'
  ]

  // Filter out JSON technical messages
  const filteredMessages = messages.filter(message => !isJsonTechnicalMessage(message.content))

  return (
    <div 
      ref={scrollContainerRef}
      className="chat-scroll h-full overflow-y-auto overflow-x-hidden p-4 space-y-4"
      style={{
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(255, 255, 255, 0.3) rgba(255, 255, 255, 0.1)',
      }}
    >
        {filteredMessages.length === 0 && !isTyping && (
          <div className="text-center text-white/50 py-8">
            <div className="mb-4">
              <svg className="w-12 h-12 mx-auto text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-sm">Start a conversation by typing a task below</p>
          </div>
        )}
        
        {filteredMessages.map((message, index) => (
        <div
          key={message.id}
          className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fadeInUp`}
          style={{
            animationDelay: `${index * 0.1}s`,
            animationFillMode: 'both'
          }}
        >
          <div
            className={`max-w-[85%] min-w-0 px-4 py-3 rounded-2xl transition-all duration-300 hover:shadow-lg ${
              message.type === 'user'
                ? 'bg-blue-600 text-white shadow-blue-600/20'
                : message.type === 'system'
                ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30 shadow-orange-500/10'
                : 'bg-white/10 text-white border border-white/20 shadow-white/10'
            }`}
          >
            {message.isLoading ? (
              <TypingIndicator texts={loadingTexts} />
            ) : (
              <div className="overflow-x-auto max-h-48">
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words min-w-0 pr-2">
                  {message.content}
                </p>
              </div>
            )}
            <p className="text-xs opacity-60 mt-2 flex-shrink-0">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
        </div>
      ))}

      {isTyping && (
        <div className="flex justify-start animate-fadeInUp">
          <div className="bg-white/10 text-white border border-white/20 px-4 py-3 rounded-2xl shadow-lg">
            <TypingIndicator texts={loadingTexts} />
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

export default ChatMessages