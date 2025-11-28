import { useState, useEffect, useRef } from 'react'
import './ConversationMode.css'
import { textToSpeech } from '../../services/TextToSpeech'
import { voiceRecognition } from '../../services/VoiceRecognition'
import { VoiceVisualizer } from './Visuals/VoiceVisualizer'
import {
  voiceConversation,
  type ConversationState,
  type ConversationStateInfo,
} from '../../services/VoiceConversation'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  language?: string
}

export interface Intent {
  task_description: string
  is_ready: boolean
  confidence: number
}

// Supported languages for JARVIS conversation
export const SUPPORTED_LANGUAGES = {
  en: { name: 'English', speechCode: 'en-US' },
  ta: { name: 'தமிழ்', speechCode: 'ta-IN' },
  si: { name: 'සිංහල', speechCode: 'si-LK' },
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
  onSwitchToAgent,
}: ConversationModeProps) => {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeechEnabled, setIsSpeechEnabled] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  
  // Language state for JARVIS multi-language support
  const [currentLanguage, setCurrentLanguage] = useState<'en' | 'ta' | 'si'>('en')
  const [isListening, setIsListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [voiceError, setVoiceError] = useState<string | null>(null)

  // Audio visualization state
  const [audioLevel, setAudioLevel] = useState(0)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const animationFrameRef = useRef<number>()

  // New state for live voice mode
  const [isLiveVoiceMode, setIsLiveVoiceMode] = useState(false)
  const [conversationState, setConversationState] = useState<ConversationState>('idle')
  const [liveTranscript, setLiveTranscript] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastSpokenIndexRef = useRef<number>(-1)
  const isWaitingForResponseRef = useRef<boolean>(false)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Speak new assistant messages when speech is enabled
  useEffect(() => {
    if (!isSpeechEnabled || !textToSpeech.isSynthesisSupported()) return

    // Find new assistant messages that haven't been spoken yet
    const assistantMessages = messages.filter((m) => m.role === 'assistant')
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
          },
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
      voiceConversation.cleanup()
    }
  }, [])

  // Handle live voice mode responses
  useEffect(() => {
    if (!isLiveVoiceMode || !messages.length) return

    const lastMessage = messages[messages.length - 1]

    // If we received a bot response and we're waiting for it
    if (lastMessage.role === 'assistant' && isWaitingForResponseRef.current) {
      console.log('🎙️ Bot response received in live mode, speaking...')
      isWaitingForResponseRef.current = false
      setIsProcessing(false)

      // Let the voice conversation service handle the response
      voiceConversation.handleBotResponse(lastMessage.content)
    }
  }, [messages, isLiveVoiceMode])

  // Initialize voice recognition with current language
  useEffect(() => {
    const isSupported = voiceRecognition.isRecognitionSupported()
    console.log('🎤 ConversationMode Voice Recognition Support:', isSupported)

    if (isSupported) {
      const speechCode = SUPPORTED_LANGUAGES[currentLanguage]?.speechCode || 'en-US'
      voiceRecognition.initialize({
        continuous: false,
        interimResults: true,
        language: speechCode,
      })
      console.log(`🎤 ConversationMode Voice Recognition Initialized with language: ${speechCode}`)
    }
  }, [currentLanguage])

  // Update voice conversation language when language changes
  useEffect(() => {
    if (isLiveVoiceMode) {
      const speechCode = SUPPORTED_LANGUAGES[currentLanguage]?.speechCode || 'en-US'
      voiceConversation.updateConfig({ language: speechCode })
    }
  }, [currentLanguage, isLiveVoiceMode])

  // Monitor messages to reset processing state
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.role === 'assistant') {
        setIsProcessing(false)
      }
    }
  }, [messages])

  // Request JARVIS greeting when connected - with language support
  useEffect(() => {
    if (connected && messages.length === 0 && socket) {
      // Request greeting from server with current language
      socket.emit('reset_conversation', { language: currentLanguage })
    }
  }, [connected, messages.length, socket, currentLanguage])

  const handleSendMessage = () => {
    if (!input.trim() || !connected || isProcessing) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
      language: currentLanguage,
    }

    setMessages([...messages, userMessage])
    setIsProcessing(true)

    // Check if last message was a help request (contains "🤔 **The agent appears to be stuck**")
    const lastMessage = messages[messages.length - 1]
    const isHelpRequest =
      lastMessage && lastMessage.content.includes('🤔 **The agent appears to be stuck**')

    if (isHelpRequest) {
      // Send as help response
      socket.emit('user_help_response', { response: input.trim() })
    } else {
      // Send as regular chat message with language
      socket.emit('chat_message', { message: input.trim(), language: currentLanguage })
    }

    setInput('')
  }

  // Handle language change
  const handleLanguageChange = (lang: 'en' | 'ta' | 'si') => {
    setCurrentLanguage(lang)
    if (socket && connected) {
      socket.emit('set_language', { language: lang })
      // Reset conversation with new language
      socket.emit('reset_conversation', { language: lang })
      setMessages([])
      setIntent(null)
    }
  }

  const handleStartAutomation = () => {
    if (!intent) return

    // Start the automation task
    socket.emit('start_clarified_task', {
      task: intent.task_description,
      cdp_endpoint: cdpEndpoint,
      is_extension: true,
    })

    // Clear intent after starting
    setIntent(null)

    // Add confirmation message
    setMessages([
      ...messages,
      {
        role: 'assistant',
        content: '🚀 Perfect! Starting the automation now...',
        timestamp: new Date().toISOString(),
      },
    ])
  }

  const toggleVoiceInput = async () => {
    // Don't allow manual voice input when in live mode
    if (isLiveVoiceMode) {
      setVoiceError('Please exit Live Voice Mode to use manual voice input')
      return
    }

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
              setInput((prev) => (prev + ' ' + result.transcript).trim())
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
          },
        )
        setIsListening(true)
      }
    } catch (error) {
      console.error('Voice recognition error:', error)
      setVoiceError('Failed to start voice recognition')
      setIsListening(false)
    }
  }

  const toggleLiveVoiceMode = () => {
    if (!voiceConversation.isSupported()) {
      setVoiceError('Live voice mode requires both microphone and speaker support')
      return
    }

    if (isLiveVoiceMode) {
      // Stop live voice mode
      console.log('🎙️ Stopping live voice mode')
      voiceConversation.stop()
      setIsLiveVoiceMode(false)
      setConversationState('idle')
      setLiveTranscript('')
      setVoiceError(null)
      isWaitingForResponseRef.current = false
    } else {
      // Start live voice mode
      console.log('🎙️ Starting live voice mode')
      setVoiceError(null)
      setIsLiveVoiceMode(true)

      // Stop any manual voice input
      if (isListening) {
        voiceRecognition.stopListening()
        setIsListening(false)
        setInterimTranscript('')
      }

      // Configure voice conversation with current language
      const speechCode = SUPPORTED_LANGUAGES[currentLanguage]?.speechCode || 'en-US'
      voiceConversation.updateConfig({ language: speechCode })

      // Start the voice conversation
      voiceConversation.start(
        // State change callback
        (stateInfo: ConversationStateInfo) => {
          console.log('🎙️ Conversation state:', stateInfo.state)
          setConversationState(stateInfo.state)

          if (stateInfo.transcript) {
            setLiveTranscript(stateInfo.transcript)
          }
        },
        // Message ready callback - auto send with language
        (message: string) => {
          console.log('🎙️ Auto-sending message:', message)

          // Add user message to chat
          const userMessage: Message = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
            language: currentLanguage,
          }

          setMessages([...messages, userMessage])
          setIsProcessing(true)
          isWaitingForResponseRef.current = true
          setLiveTranscript('')

          // Send to backend with language
          socket.emit('chat_message', { message, language: currentLanguage })
        },
        // Error callback
        (error: string) => {
          console.error('🎙️ Voice conversation error:', error)
          setVoiceError(error)
        },
      )
    }
  }

  const handleResetConversation = () => {
    socket.emit('reset_conversation', { language: currentLanguage })
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

  // Combined voice button handler
  const handleVoiceButtonClick = () => {
    if (isLiveVoiceMode) {
      // Exit live mode
      toggleLiveVoiceMode()
    } else if (isListening) {
      // Stop manual voice input
      toggleVoiceInput()
    } else {
      // Show options or toggle between modes
      if (voiceConversation.isSupported()) {
        // Long press or double click could toggle live mode, single click for manual
        toggleLiveVoiceMode()
      } else {
        toggleVoiceInput()
      }
    }
  }

  const getVoiceButtonTitle = () => {
    if (isLiveVoiceMode) return 'Exit Live Voice Mode'
    if (isListening) return 'Stop listening'
    if (voiceConversation.isSupported()) return 'Start Live Voice Mode'
    return 'Start voice input'
  }

  const getVoiceButtonState = () => {
    if (isLiveVoiceMode) return 'live'
    if (isListening) return 'listening'
    return 'idle'
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

  // Audio analysis for visualization
  useEffect(() => {
    if ((isListening || isLiveVoiceMode) && !audioContextRef.current) {
      const initAudio = async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
          const analyser = audioContext.createAnalyser()
          analyser.fftSize = 256
          analyser.smoothingTimeConstant = 0.8

          const source = audioContext.createMediaStreamSource(stream)
          source.connect(analyser)

          audioContextRef.current = audioContext
          analyserRef.current = analyser
          sourceRef.current = source

          const updateLevel = () => {
            if (!analyserRef.current) return

            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
            analyserRef.current.getByteFrequencyData(dataArray)

            // Calculate average level
            let sum = 0
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i]
            }
            const average = sum / dataArray.length

            // Normalize to 0-1 with some boost
            const normalized = Math.min(1, (average / 128) * 1.5)
            setAudioLevel(normalized)

            animationFrameRef.current = requestAnimationFrame(updateLevel)
          }

          updateLevel()
        } catch (err) {
          console.error('Error initializing audio visualization:', err)
        }
      }

      initAudio()
    } else if (!isListening && !isLiveVoiceMode && audioContextRef.current) {
      // Cleanup
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (sourceRef.current) {
        sourceRef.current.disconnect()
      }
      if (analyserRef.current) {
        analyserRef.current.disconnect()
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }

      audioContextRef.current = null
      analyserRef.current = null
      sourceRef.current = null
      setAudioLevel(0)
    }

    return () => {
      // Cleanup on unmount or dependency change
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      // We don't close the context here immediately to avoid rapid open/close cycles
      // but we should if the component unmounts.
      // For now, we rely on the else block above for logic cleanup.
    }
  }, [isListening, isLiveVoiceMode])

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  return (
    <div className="conversation-mode">
      {/* Language Selector */}
      <div className="language-selector">
        <span className="language-label">🌐</span>
        {Object.entries(SUPPORTED_LANGUAGES).map(([code, { name }]) => (
          <button
            key={code}
            className={`language-btn ${currentLanguage === code ? 'active' : ''}`}
            onClick={() => handleLanguageChange(code as 'en' | 'ta' | 'si')}
            title={name}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Live Voice Mode Status Bar */}
      {isLiveVoiceMode && (
        <div className={`live-voice-status ${conversationState}`}>
          {/* <div className="visualizer-container" style={{ height: '180px', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: '10px' }}>
             <VoiceVisualizer
               isListening={conversationState === 'listening'}
               isSpeaking={conversationState === 'speaking'}
               audioLevel={audioLevel}
             />
          </div> */}
          <div className="status-indicator">
            {conversationState === 'listening' && (
              <>
                <div className="pulse-indicator listening"></div>
                <span>🎤 Listening...</span>
              </>
            )}
            {conversationState === 'processing' && (
              <>
                <div className="pulse-indicator processing"></div>
                <span>🤔 Processing...</span>
              </>
            )}
            {conversationState === 'speaking' && (
              <>
                <div className="pulse-indicator speaking"></div>
                <span>🔊 Speaking...</span>
              </>
            )}
            {conversationState === 'idle' && (
              <>
                <div className="pulse-indicator idle"></div>
                <span>⏸️ Idle</span>
              </>
            )}
          </div>
          {liveTranscript && <div className="live-transcript">{liveTranscript}</div>}
        </div>
      )}
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
        {voiceError && <div className="voice-error-message">{voiceError}</div>}
        {isLiveVoiceMode ? (
          <div className="live-voice-mode-input">
            <div className="live-mode-message">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                <circle cx="12" cy="12" r="3" fill="currentColor" />
              </svg>
              <div>
                <div className="live-mode-title">Live Voice Mode Active</div>
                <div className="live-mode-hint">
                  Just start speaking - no need to click anything!
                </div>
              </div>
            </div>
            <button className="exit-live-mode-btn" onClick={toggleLiveVoiceMode}>
              Exit Live Mode
            </button>
          </div>
        ) : (
          <div className="input-wrapper">
            <div className="input-field">
              <textarea
                className="chat-input"
                value={input + (interimTranscript ? ' ' + interimTranscript : '')}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  isProcessing
                    ? 'Assistant is typing...'
                    : isListening
                      ? '🎤 Listening...'
                      : 'Type your message... (Ctrl+Enter to send)'
                }
                rows={3}
                disabled={!connected || isProcessing}
              />
              <div className="input-actions">
                <button
                  className={`action-btn voice-btn ${getVoiceButtonState()}`}
                  onClick={handleVoiceButtonClick}
                  disabled={
                    !connected ||
                    isProcessing ||
                    (!voiceRecognition.isRecognitionSupported() && !voiceConversation.isSupported())
                  }
                  title={getVoiceButtonTitle()}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    {isLiveVoiceMode ? (
                      // Live mode icon - circle with dot
                      <>
                        <circle
                          cx="12"
                          cy="12"
                          r="8"
                          stroke="currentColor"
                          strokeWidth="2"
                          fill="currentColor"
                        />
                        <circle cx="12" cy="12" r="3" fill="white" />
                      </>
                    ) : isListening ? (
                      // Listening mode - stop square
                      <rect x="8" y="8" width="8" height="8" fill="currentColor" rx="1" />
                    ) : (
                      // Default microphone icon
                      <path
                        d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14ZM17.91 11C17.91 14.39 15.16 17.14 11.77 17.14C8.38 17.14 5.63 14.39 5.63 11H4C4 14.93 7.04 18.16 10.86 18.71V22H13.14V18.71C16.96 18.16 20 14.93 20 11H17.91Z"
                        fill="currentColor"
                      />
                    )}
                  </svg>
                  {isLiveVoiceMode && <span className="voice-btn-text">Live</span>}
                </button>
                <button
                  className="action-btn send-btn"
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
        )}
      </div>
    </div>
  )
}
