import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { io, Socket } from 'socket.io-client'

// import './SidePanel.css'
import { ChatInput } from './components/ChatInput'
import { ConversationMode } from './components/ConversationMode'
import { ExecutionLog, LogEvent } from './components/ExecutionLog'
import { ControlButtons, ControlButtonsProps } from './components/ControlButtons'
import { TaskStatus, TaskStatusProps } from './components/TaskStatus'
import { ChatMessages, ChatMessage } from './components/ChatMessages'
import {
  TaskStatus as ProtocolTaskStatus,
  StartTaskPayload,
  ExtensionSettings,
  DEFAULT_SETTINGS,
  WEBSOCKET_NAMESPACE,
  MAX_RECONNECTION_ATTEMPTS,
  RECONNECTION_DELAY_MS,
} from '../types/protocol'
import { loadSettings, onSettingsChanged, formatTimestamp, openOptionsPage } from '../utils/helpers'
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
  ConversationMessage,
  ConversationIntent,
} from '../utils/state'

export const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)

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
  const [taskResult, setTaskResult] = useState<string | null>(null)
  const [conversationMode, setConversationMode] = useState(true) // Enable conversation mode by default
  const [conversationMessages, setConversationMessages] = useState<ConversationMessage[]>([])
  const [conversationIntent, setConversationIntent] = useState<ConversationIntent | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
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
    loadConversationMessages().then((messages) => {
      if (isMounted) {
        setConversationMessages(messages)
      }
    })

    loadConversationIntent().then((intent) => {
      if (isMounted) {
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

  // Shared helper for bounded log append
  const appendBoundedLog = useCallback(
    (prev: LogEvent[], event: LogEvent) => {
      const updated = [...prev, event]
      return updated.length > settings.maxLogs ? updated.slice(-settings.maxLogs) : updated
    },
    [settings.maxLogs],
  )

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
    addSystemLog('Using local CDP endpoint: http://localhost:9222', 'INFO')
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
        setTaskResult(agentHistory)
      } catch (error) {
        console.error('Failed to parse AgentHistoryList:', error)
        addSystemLog('Error parsing task result metadata', 'ERROR')
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
    <div className="flex flex-col h-screen bg-gradient-to-b from-[#020617] to-[#0a0f2c] text-white relative overflow-hidden before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_center,_rgba(33,150,243,0.15)_0%,_rgba(33,150,243,0.05)_40%,_transparent_70%)] before:pointer-events-none before:-z-10">
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
              <h1 className="text-sm font-semibold text-white">Browser.AI</h1>
            </div>
          </div>
          <div className="header-actions">
            <button 
              className={`mode-toggle ${conversationMode ? 'active' : ''}`}
              onClick={() => setConversationMode(!conversationMode)}
              title={conversationMode ? "Switch to Direct Mode" : "Switch to Conversation Mode"}
              style={{ paddingLeft: '6px', paddingRight: '6px' }}
            >
              {conversationMode ? '💬' : '⚡'}
            </button>
            <button className="settings-button" onClick={openOptionsPage} title="Settings">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M10 6.5C8.067 6.5 6.5 8.067 6.5 10C6.5 11.933 8.067 13.5 10 13.5C11.933 13.5 13.5 11.933 13.5 10C13.5 8.067 11.933 6.5 10 6.5Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path
                  d="M17.5 10C17.5 10.233 17.49 10.464 17.471 10.692L18.935 11.809C19.082 11.925 19.135 12.129 19.058 12.304L17.508 15.196C17.431 15.371 17.242 15.453 17.056 15.402L15.341 14.839C14.995 15.111 14.616 15.344 14.21 15.531L13.964 17.312C13.939 17.503 13.773 17.647 13.579 17.647H10.479C10.285 17.647 10.119 17.503 10.094 17.312L9.848 15.531C9.442 15.344 9.063 15.111 8.717 14.839L7.002 15.402C6.816 15.453 6.627 15.371 6.55 15.196L5 12.304C4.923 12.129 4.976 11.925 5.123 11.809L6.587 10.692C6.568 10.464 6.558 10.233 6.558 10C6.558 9.767 6.568 9.536 6.587 9.308L5.123 8.191C4.976 8.075 4.923 7.871 5 7.696L6.55 4.804C6.627 4.629 6.816 4.547 7.002 4.598L8.717 5.161C9.063 4.889 9.442 4.656 9.848 4.469L10.094 2.688C10.119 2.497 10.285 2.353 10.479 2.353H13.579C13.773 2.353 13.939 2.497 13.964 2.688L14.21 4.469C14.616 4.656 14.995 4.889 15.341 5.161L17.056 4.598C17.242 4.547 17.431 4.629 17.508 4.804L19.058 7.696C19.135 7.871 19.082 8.075 18.935 8.191L17.471 9.308C17.49 9.536 17.5 9.767 17.5 10Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-white/5 border border-white/10 rounded-full">
              <span className={`w-1.5 h-1.5 rounded-full transition-all ${connected 
                ? 'bg-green-400 shadow-lg shadow-green-400/30 animate-pulse' 
                : 'bg-red-400'
              }`}></span>
              <span className="text-xs text-white">{connected ? 'Online' : 'Offline'}</span>
            </div>
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

      {/* Main Content */}
      <div className="sidepanel-content">
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
          />
        ) : (
          /* Direct Mode - Traditional logs and controls */
          <>
            {/* Task Status Banner */}
            <TaskStatus {...taskStatusProps} />

            {/* Control Buttons */}
            <ControlButtons {...controlButtonsProps} />

            {/* Execution Logs */}
            <ExecutionLog logs={logs} onClear={clearLogs} devMode={settings.devMode} />

            {/* Task Result */}
            {taskResult && (
              <div className="task-result">
                <h3>Task Result</h3>
                <p>{taskResult}</p>
              </div>
            )}
            
            {/* Chat Input at Bottom for Direct Mode */}
            <div className="sidepanel-footer">
              <ChatInput
                onSendMessage={handleStartTask}
                disabled={taskStatus.is_running}
                placeholder="What would you like me to automate? (e.g., 'Search for Python tutorials')"
              />
            </div>
          </>
        )}
      </div>
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
    </div>
  )
}

export default SidePanel
