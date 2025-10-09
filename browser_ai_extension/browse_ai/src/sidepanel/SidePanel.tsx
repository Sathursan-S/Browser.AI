import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { io, Socket } from 'socket.io-client'

// import './SidePanel.css'
import { ChatInput } from './components/ChatInput'
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

  // Get CDP endpoint from background script
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





  // Listen for task result
  useEffect(() => {
    if (!socket) return

    const handleTaskResult = (result: {
      task: string
      success: boolean
      history: string | null
    }) => {
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
