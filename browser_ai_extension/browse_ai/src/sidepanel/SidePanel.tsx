import { useState, useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

import { ChatInput } from './components/ChatInput'
import { ChatMessages, ChatMessage } from './components/ChatMessages'
import { ConversationMode, Message, Intent } from './components/ConversationMode'
import {
  TaskStatus as ProtocolTaskStatus,
  StartTaskPayload,
  ExtensionSettings,
  DEFAULT_SETTINGS,
  WEBSOCKET_NAMESPACE,
  MAX_RECONNECTION_ATTEMPTS,
  RECONNECTION_DELAY_MS,
} from '../types/protocol'
import { loadSettings, onSettingsChanged, openOptionsPage } from '../utils/helpers'
import {
  loadTaskStatus,
  saveTaskStatus,
  loadCdpEndpoint,
  saveCdpEndpoint,
  onTaskStatusChanged,
  loadConversationMessages,
  saveConversationMessages,
  loadConversationIntent,
  saveConversationIntent,
} from '../utils/state'

export const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)

  // Mode states
  const [conversationMode, setConversationMode] = useState(true) // Toggle between chat and agent mode
  const [conversationMessages, setConversationMessages] = useState<Message[]>([])
  const [conversationIntent, setConversationIntent] = useState<Intent | null>(null)

  // Debug logging for mode changes
  useEffect(() => {
    console.log('🚀 useEffect: Mode changed to:', conversationMode ? 'Chat Mode' : 'Agent Mode')
  }, [conversationMode])

  // Force re-render test
  const [renderKey, setRenderKey] = useState(0)

  // Add scrollbar styles (hidden)
  useEffect(() => {
    const styleElement = document.createElement('style')
    styleElement.textContent = `
      .chat-scroll::-webkit-scrollbar {
        display: none;
      }

      .chat-scroll {
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

  const [taskStatus, setTaskStatus] = useState<ProtocolTaskStatus>({
    is_running: false,
    current_task: null,
    has_agent: false,
    is_paused: false,
  })
  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS)
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const socketRef = useRef<Socket | null>(null)

  // Load settings and persisted task status on mount
  useEffect(() => {
    let isMounted = true

    loadSettings().then((loadedSettings) => {
      if (isMounted) {
        setSettings(loadedSettings)
      }
    })

    const handleSettingsChange = (newSettings: ExtensionSettings) => {
      if (isMounted) {
        setSettings(newSettings)
      }
    }
    const unsubscribeSettings = onSettingsChanged(handleSettingsChange)

    // Load persisted task status from chrome storage using state manager
    loadTaskStatus().then((status) => {
      if (isMounted && status) {
        setTaskStatus(status)
      }
    })

    // Load persisted CDP endpoint
    loadCdpEndpoint().then((endpoint) => {
      if (isMounted && endpoint) {
        setCdpEndpoint(endpoint)
      }
    })

    // Load persisted conversation state
    loadConversationMessages().then((msgs) => {
      if (isMounted && msgs) {
        setConversationMessages(msgs)
      }
    })

    loadConversationIntent().then((intent) => {
      if (isMounted && intent) {
        setConversationIntent(intent)
      }
    })

    // Listen for task status changes from other extension pages
    const handleTaskStatusChange = (newStatus: ProtocolTaskStatus) => {
      if (isMounted) {
        setTaskStatus(newStatus)
      }
    }
    const unsubscribeTaskStatus = onTaskStatusChanged(handleTaskStatusChange)

    return () => {
      isMounted = false
      unsubscribeSettings()
      unsubscribeTaskStatus()
    }
  }, [])

  // Persist task status to chrome storage whenever it changes
  useEffect(() => {
    saveTaskStatus(taskStatus)
  }, [taskStatus])

  // Persist CDP endpoint when it changes
  useEffect(() => {
    if (cdpEndpoint) {
      saveCdpEndpoint(cdpEndpoint)
    }
  }, [cdpEndpoint])

  // Persist conversation messages when they change
  useEffect(() => {
    if (conversationMessages.length > 0) {
      saveConversationMessages(conversationMessages)
    }
  }, [conversationMessages])

  // Persist conversation intent when it changes
  useEffect(() => {
    saveConversationIntent(conversationIntent)
  }, [conversationIntent])

  // Helper function to check if message is JSON-like technical output
  const isJsonTechnicalMessage = useCallback((content: string): boolean => {
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
  }, [])

  // Add message to chat
  const addMessage = useCallback(
    (content: string, type: 'user' | 'assistant' | 'system' = 'system') => {
      // Skip JSON technical messages
      if (type !== 'user' && isJsonTechnicalMessage(content)) {
        return
      }

      const message: ChatMessage = {
        id: Date.now().toString(),
        content,
        type,
        timestamp: new Date(),
      }
      setMessages((prev) => {
        const updated = [...prev, message]
        return updated.length > settings.maxLogs ? updated.slice(-settings.maxLogs) : updated
      })
    },
    [settings.maxLogs, isJsonTechnicalMessage],
  )

  // Add loading message
  const addLoadingMessage = useCallback(() => {
    const message: ChatMessage = {
      id: 'loading',
      content: '',
      type: 'assistant',
      timestamp: new Date(),
      isLoading: true,
    }
    setMessages((prev) => [...prev, message])
    setIsTyping(true)
  }, [])

  // Remove loading message and add actual response
  const replaceLoadingMessage = useCallback((content: string) => {
    setIsTyping(false)
    setMessages((prev) => {
      const filtered = prev.filter(msg => msg.id !== 'loading')
      const message: ChatMessage = {
        id: Date.now().toString(),
        content,
        type: 'assistant',
        timestamp: new Date(),
      }
      return [...filtered, message]
    })
  }, [])

  // Show notification popup
  const showNotificationPopup = useCallback(
    async (
      notificationType: 'user_interaction' | 'task_complete' | 'error',
      message: string,
      details?: string,
    ) => {
      if (!settings.showNotifications) return

      try {
        await chrome.runtime.sendMessage({
          type: 'SHOW_NOTIFICATION',
          notificationType,
          message,
          details,
        })
      } catch (error) {
        console.error('Failed to show notification:', error)
      }
    },
    [settings.showNotifications],
  )

  // Add system message
  const addSystemMessage = useCallback(
    (message: string, level: string = 'INFO') => {
      const type = level === 'ERROR' ? 'system' : 'system'
      addMessage(message, type)
    },
    [addMessage],
  )

  // Initialize socket connection - reconnect when settings change
  useEffect(() => {
    // Clean up existing socket
    if (socketRef.current) {
      socketRef.current.close()
    }

    const newSocket = io(`${settings.serverUrl}${WEBSOCKET_NAMESPACE}`, {
      transports: ['websocket'],
      reconnection: settings.autoReconnect,
      reconnectionAttempts: MAX_RECONNECTION_ATTEMPTS,
      reconnectionDelay: RECONNECTION_DELAY_MS,
    })

    newSocket.on('connect', () => {
      setConnected(true)
      console.log('Connected to Browser.AI server')
      newSocket.emit('extension_connect')
      // Request current status from server on connect to ensure UI is synchronized
      newSocket.emit('get_status')
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
      console.log('Disconnected from Browser.AI server')
    })

    newSocket.on('status', (status: ProtocolTaskStatus) => {
      setTaskStatus(status)
      console.log('Received status update:', status)

      // Notify user about task completion or failure
      if (!status.is_running && typeof status.current_task === 'string') {
        if (status.current_task.includes('completed')) {
          showNotificationPopup(
            'task_complete',
            'Task completed successfully!',
            status.current_task,
          )
        } else if (status.current_task.includes('failed')) {
          showNotificationPopup('error', 'Task failed', status.current_task)
        }
      }
    })

    newSocket.on('log_event', (event: any) => {
      // Convert log events to chat messages
      addMessage(event.message, 'assistant')

      // Show notification popup for user interaction events
      if (
        event.message.includes('🙋‍♂️') ||
        event.message.toLowerCase().includes('requesting user help') ||
        event.message.toLowerCase().includes('user intervention')
      ) {
        showNotificationPopup('user_interaction', event.message, event.logger_name)
      }

      // Show notification for task completion
      if (event.message.includes('✅') || event.message.toLowerCase().includes('task completed')) {
        showNotificationPopup('task_complete', 'Task completed successfully!', event.message)
        replaceLoadingMessage(event.message)
      }

      // Show notification for errors
      if (event.level === 'ERROR' && event.message.includes('❌')) {
        showNotificationPopup('error', 'An error occurred', event.message)
        replaceLoadingMessage(event.message)
      }
    })

    newSocket.on('task_started', (data: { message: string }) => {
      console.log('Task started:', data.message)
      addSystemMessage(data.message, 'INFO')
      newSocket.emit('get_status')
    })

    newSocket.on(
      'task_action_result',
      (result: { success: boolean; message?: string; error?: string }) => {
        console.log('Task action result:', result)

        if (result.success) {
          // Request updated status from server instead of updating locally
          newSocket.emit('get_status')
          if (result.message) {
            replaceLoadingMessage(result.message)
          }
        } else if (result.error) {
          replaceLoadingMessage(result.error)
          // Also request status on error to ensure UI is in sync
          newSocket.emit('get_status')
        }
      },
    )

    // Listen for task result
    newSocket.on(
      'task_result',
      (result: { task: string; success: boolean; history: string | null }) => {
        console.log('Task result received:', result)
        if (result.task !== null) {
          const message = `Task "${result.task}" ${result.success ? 'completed successfully' : 'failed'}`
          replaceLoadingMessage(message)
        }
        // Remove task history from chat - keeping only the completion message
      },
    )

    newSocket.on('error', (data: { message: string }) => {
      console.error('Server error:', data.message)
      addSystemMessage(data.message, 'ERROR')
    })

    setSocket(newSocket)
    socketRef.current = newSocket

    return () => {
      newSocket.close()
    }
  }, [settings.serverUrl, settings.autoReconnect, addMessage, replaceLoadingMessage, showNotificationPopup, addSystemMessage])

  // ❌ NOT NEEDED FOR LOCAL PLAYWRIGHT SETUP
  // This function was for extension-proxy mode where CDP endpoint is fetched dynamically
  // For local setup, we use direct CDP at http://localhost:9222
  /*
  const getCdpEndpoint = async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (!tab.id) {
        throw new Error('No active tab found')
      }

      // Use extension proxy mode instead of direct WebSocket
      const response = await chrome.runtime.sendMessage({
        type: 'GET_CDP_ENDPOINT',
        tabId: tab.id,
      })

      if (response.success && response.mode === 'extension-proxy') {
        setCdpEndpoint(String(response.endpoint))
        return String(response.endpoint)
      } else {
        throw new Error(response.error || 'Failed to get CDP endpoint')
      }
    } catch (error) {
      console.error('Failed to get CDP endpoint:', error)
      addSystemMessage(`Failed to get CDP endpoint: ${error}`, 'ERROR')
      return null
    }
  }
  */

  // ✅ SIMPLIFIED FOR LOCAL PLAYWRIGHT SETUP
  // Just use the known CDP endpoint for local development
  const getCdpEndpoint = async () => {
    const endpoint = 'http://localhost:9222'
    setCdpEndpoint(endpoint)
    addSystemMessage('Using local CDP endpoint: http://localhost:9222', 'INFO')
    return endpoint
  }

  const handleStartTask = async (task: string) => {
    if (!task.trim()) {
      addSystemMessage('Please enter a task description', 'WARNING')
      return
    }

    if (!connected || !socket) {
      addSystemMessage('Not connected to server', 'ERROR')
      return
    }

    let endpoint = cdpEndpoint
    if (!endpoint) {
      addSystemMessage('Getting CDP endpoint from current tab...', 'INFO')
      endpoint = (await getCdpEndpoint()) || ''
      if (!endpoint) {
        return
      }
    }

    // Add user message and loading state
    addMessage(task, 'user')
    addLoadingMessage()

    const payload: StartTaskPayload = {
      task: task,
      cdp_endpoint: endpoint,
      is_extension: true, // Indicate this is running in extension mode
    }

    socket.emit('start_task', payload)

    // Don't update state optimistically - wait for server status update via 'status' event
    addSystemMessage(`Starting task: ${task}`, 'INFO')
  }

  const handleStopTask = () => {
    if (!connected || !socket) return
    socket.emit('stop_task')
    setIsTyping(false)
    // Don't update state optimistically - wait for server status update
    addSystemMessage('Stopping task...', 'INFO')
  }

  const handlePauseTask = () => {
    if (!connected || !socket) return
    socket.emit('pause_task')
    setIsTyping(false)
    // Don't update state optimistically - wait for server status update
    addSystemMessage('Pausing task...', 'INFO')
  }

  const handleResumeTask = () => {
    if (!connected || !socket) return
    socket.emit('resume_task')
    addLoadingMessage()
    // Don't update state optimistically - wait for server status update
    addSystemMessage('Resuming task...', 'INFO')
  }

  const clearMessages = () => {
    setMessages([])
    setIsTyping(false)
  }





  /**
 * Extracts the 'done' text from the last entry in the all_model_outputs list.
 * @param agentHistoryString The raw string output from AgentHistoryList.
 * @returns The extracted text string, or null if not found.
 */
function getLastDoneText(agentHistoryString: string): string | null {
  // 1. Isolate the string content of the 'all_model_outputs' array
  const match = agentHistoryString.match(/all_model_outputs=\[(.*)\]\)/);
  if (!match || !match[1]) {
    console.error("Could not find 'all_model_outputs' in the string.");
    return null;
  }

  // 2. Convert the Python-like string into a valid JSON string
  const jsonString = `[${match[1]}]`
    .replace(/'/g, '"') // Replace single quotes with double quotes
    .replace(/None/g, "null") // Replace Python's None with JSON's null
    .replace(/True/g, "true") // Replace Python's True with JSON's true
    .replace(/False/g, "false"); // Replace Python's False with JSON's false

  try {
    // 3. Parse the cleaned string into a JavaScript array
    const allModelOutputs = JSON.parse(jsonString);

    // 4. Get the last object from the array
    const lastOutput = allModelOutputs[allModelOutputs.length - 1];

    // 5. Check for the 'done.text' property and return it
    if (lastOutput && lastOutput.done && typeof lastOutput.done.text === 'string') {
      return lastOutput.done.text;
    }
  } catch (error) {
    console.error("Failed to parse JSON string:", error);
    return null;
  }

  return null; // Return null if the structure isn't as expected
}


  // Listen for task result
  useEffect(() => {
    if (!socket) return

    const handleTaskResult = (result: {
      task: string
      success: boolean
      history: string | null
    }) => {
      if (!result.history && result.task !== null) return

      try {
        const agentHistory = getLastDoneText(result.history ? result.history : '')
        // console.log('Parsed AgentHistoryList:', agentHistory)

        // const extractedContents = agentHistory.all_results.map(
        //   (action: { extracted_content: string }) => action.extracted_content,
        // )
        // console.log('Extracted Contents:', extractedContents)r

        const resultMessage = `Task "${result.task}" ${
          result.success ? 'completed successfully' : 'failed'
        }: ${agentHistory}`
        if (agentHistory) {
          replaceLoadingMessage(agentHistory)
        }
      } catch (error) {
        console.error('Failed to parse AgentHistoryList:', error)
        addSystemMessage('Error parsing task result metadata', 'ERROR')
      }
      if (result.task === null) return
      console.log('Task result received:', result)
      const resultMessage = `✅ Task "${result.task}" ${result.success ? 'completed successfully' : 'failed'}`
      replaceLoadingMessage(resultMessage)
      // Remove task history from chat - keeping only the completion message
    }

    socket.on('task_result', handleTaskResult)

    return () => {
      socket.off('task_result', handleTaskResult)
    }
  }, [socket])

  return (
    <div key={renderKey} className="flex flex-col h-screen bg-gradient-to-b from-[#020617] to-[#0a0f2c] text-white relative overflow-hidden before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_center,_rgba(33,150,243,0.15)_0%,_rgba(33,150,243,0.05)_40%,_transparent_70%)] before:pointer-events-none before:-z-10">
      {/* Curved neon top highlight line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#2196f3] to-transparent shadow-[0_0_10px_#2196f3] -z-10" />
      <div className="absolute top-[2px] left-[10%] right-[10%] h-[1px] bg-gradient-to-r from-transparent via-[#2196f3]/60 to-transparent blur-sm -z-10" />

      {/* Soft radial blue glow in center */}
      <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-[radial-gradient(ellipse,_rgba(33,150,243,0.1)_0%,_rgba(33,150,243,0.03)_50%,_transparent_100%)] blur-2xl opacity-80 pointer-events-none -z-10" />

      {/* Header - Minimized */}
      <header className="relative z-10 px-3 py-2 border-b border-white/10 bg-white/5 backdrop-blur-sm">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="drop-shadow-lg">
              <circle cx="12" cy="12" r="3" fill="#667eea" />
              <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1" stroke="#667eea" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div>
              <h1 className="text-sm font-semibold text-white">Browze.AI</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-white/5 border border-white/10 rounded-full">
              <span className={`w-1.5 h-1.5 rounded-full transition-all ${connected
                ? 'bg-green-400 shadow-lg shadow-green-400/30 animate-pulse'
                : 'bg-red-400'
              }`}></span>
              <span className="text-xs text-white">{connected ? 'Online' : 'Offline'}</span>
            </div>
            <button
              className={`flex items-center justify-center w-8 h-8 border rounded-lg text-white transition-all duration-300 hover:scale-105 ${
                conversationMode
                  ? 'bg-gradient-to-r from-[#2196f3] to-[#1976d2] border-blue-400/30 shadow-lg shadow-blue-500/30'
                  : 'bg-gradient-to-r from-[#9c27b0] to-[#7b1fa2] border-purple-400/30 shadow-lg shadow-purple-500/30'
              }`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔄 Toggle clicked! Current mode:', conversationMode ? 'Chat' : 'Agent');
                console.log('🔄 Switching to:', !conversationMode ? 'Chat' : 'Agent');
                setConversationMode(prev => {
                  console.log('🔄 State changing from:', prev, 'to:', !prev);
                  return !prev;
                });
                setRenderKey(prev => prev + 1);
              }}
              title={conversationMode ? "Switch to Agent Mode" : "Switch to Chat Mode"}
            >
              {conversationMode ? (
                // Chat Mode Icon - Message bubble
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  <circle cx="9" cy="10" r="1" fill="currentColor"/>
                  <circle cx="15" cy="10" r="1" fill="currentColor"/>
                </svg>
              ) : (
                // Agent Mode Icon - Robot/AI
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <circle cx="12" cy="5" r="2"/>
                  <path d="M12 7v4"/>
                  <line x1="8" y1="16" x2="8" y2="16"/>
                  <line x1="16" y1="16" x2="16" y2="16"/>
                </svg>
              )}
            </button>
            {conversationMode && (
              <button
                className="flex items-center justify-center w-7 h-7 bg-white/5 border border-white/10 rounded-md text-white hover:bg-white/10 transition-colors"
                onClick={() => {
                  if (socket) {
                    socket.emit('reset_conversation');
                  }
                  setConversationIntent(null);
                  setConversationMessages([]);
                }}
                title="Reset Conversation"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                  <path d="M21 3v5h-5"/>
                  <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                  <path d="M3 21v-5h5"/>
                </svg>
              </button>
            )}
            <button
              className="flex items-center justify-center w-7 h-7 bg-white/5 border border-white/10 rounded-md text-white hover:bg-white/10 transition-colors"
              onClick={clearMessages}
              title="Clear Chat"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
              </svg>
            </button>
            <button
              className="flex items-center justify-center w-7 h-7 bg-white/5 border border-white/10 rounded-md text-white hover:bg-white/10 transition-colors"
              onClick={openOptionsPage}
              title="Settings"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="m12 1 2.09 3.26L18 4l-2.35 2.56L15 11l-2.88-.76L9 12l.28-3.4L5.66 7 8 4l-0.09-3z"/>
              </svg>
            </button>
          </div>
        </div>
      </header>

      {conversationMode ? (
        /* Conversation Mode - Chat with AI to clarify intent */
        <ConversationMode
          socket={socket}
          connected={connected}
          onStartTask={handleStartTask}
          cdpEndpoint={cdpEndpoint}
          messages={conversationMessages}
          setMessages={setConversationMessages}
          intent={conversationIntent}
          setIntent={setConversationIntent}
          onSwitchToAgent={() => setConversationMode(false)}
        />
      ) : (
        /* Agent Mode - Direct task execution */
        <>
          {/* Chat Messages Area */}
          <div className="flex-1 flex flex-col relative z-10 min-h-0">
            <div className="flex-1 min-h-0">
              <ChatMessages messages={messages} isTyping={isTyping} />
            </div>
          </div>

          {/* Chat Input at Bottom */}
          <div className="relative z-10 p-3">
            <ChatInput
              onSendMessage={handleStartTask}
              onStopTask={handleStopTask}
              onPauseTask={handlePauseTask}
              onResumeTask={handleResumeTask}
              isRunning={taskStatus.is_running}
              isPaused={taskStatus.is_paused}
              disabled={false}
              placeholder="What would you like me to automate? (e.g., 'Search for Python tutorials')"
            />
          </div>
        </>
      )}
    </div>
  )
}

export default SidePanel

