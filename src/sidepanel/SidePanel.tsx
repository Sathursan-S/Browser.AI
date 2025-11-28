import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { io, Socket } from 'socket.io-client'

import { ChatMessages, type ChatMessage } from './components/ChatMessages'
import logo from '../assets/logo.png'
import { voiceRecognition } from '../services/VoiceRecognition'
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
} from '../utils/state'

export const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [showUtilityMenu, setShowUtilityMenu] = useState(false)
  const [renderKey, setRenderKey] = useState(0)
  const [activeSection, setActiveSection] = useState<'chat' | 'settings' | 'history'>('chat')
  const [composerValue, setComposerValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [voiceSupported, setVoiceSupported] = useState(false)
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [activeTaskTitle, setActiveTaskTitle] = useState('')
  const [showTaskProgress, setShowTaskProgress] = useState(false)
  const chatHistory = useMemo(
    () => messages.filter((message) => message.type !== 'system'),
    [messages],
  )
  const taskSteps = useMemo(() => {
    const baseSteps = [
      'Starting your automation task',
      'Processing step 1',
      'Processing step 2',
      'Processing step 3',
      'Processing step 4',
    ]

    let currentIndex = -1

    messages.forEach((message) => {
      baseSteps.forEach((label, index) => {
        if (message.content.toLowerCase().includes(label.toLowerCase())) {
          currentIndex = Math.max(currentIndex, index)
        }
      })

      if (
        /task\s+["“].*["”]\s+completed/i.test(message.content) ||
        message.content.includes('✅') ||
        message.content.toLowerCase().includes('completed successfully')
      ) {
        currentIndex = baseSteps.length
      }
    })

    return baseSteps.map((label, index) => {
      let status: 'pending' | 'active' | 'complete' = 'pending'
      if (index < currentIndex) {
        status = 'complete'
      } else if (index === currentIndex) {
        status = 'active'
      }
      return { id: `${label}-${index}`, label, status }
    })
  }, [messages])

  const [taskStatus, setTaskStatus] = useState<ProtocolTaskStatus>({
    is_running: false,
    current_task: null,
    has_agent: false,
    is_paused: false,
  })
  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS)
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    if (!showUtilityMenu) return
    const handleClickAway = () => setShowUtilityMenu(false)
    window.addEventListener('click', handleClickAway)
    return () => window.removeEventListener('click', handleClickAway)
  }, [showUtilityMenu])

  useEffect(() => {
    const supported = voiceRecognition.isRecognitionSupported()
    setVoiceSupported(supported)

    if (supported) {
      voiceRecognition.initialize({
        continuous: false,
        interimResults: true,
        language: 'en-US',
      })
    }

    return () => {
      if (supported) {
        voiceRecognition.cleanup()
      }
    }
  }, [])

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
    if (
      content.includes('{"done":') ||
      content.includes('{"success":') ||
      content.includes('{"error":')
    ) {
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
      const filtered = prev.filter((msg) => msg.id !== 'loading')
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
  }, [
    settings.serverUrl,
    settings.autoReconnect,
    addMessage,
    replaceLoadingMessage,
    showNotificationPopup,
    addSystemMessage,
  ])

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
    setActiveTaskTitle(task)
    setShowTaskProgress(true)
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

  const handleNewChat = () => {
    clearMessages()
    setComposerValue('')
    setActiveSection('chat')
    addSystemMessage('Started a new chat', 'INFO')
    setShowTaskProgress(false)
    setActiveTaskTitle('')
  }

  const handleRefreshChat = () => {
    setRenderKey((prev) => prev + 1)
    setComposerValue('')
    setActiveSection('chat')
    setIsTyping(false)
    socket?.emit('get_status')
    addSystemMessage('Chat refreshed', 'INFO')
    setShowTaskProgress(false)
    setActiveTaskTitle('')
  }

  const handleMenuSelect = (section: 'settings' | 'history') => {
    setActiveSection(section)
    setShowUtilityMenu(false)
  }

  const handleComposerSend = () => {
    if (!composerValue.trim()) return
    handleStartTask(composerValue.trim())
    setComposerValue('')
    setActiveSection('chat')
  }

  const toggleRecording = () => {
    if (!voiceSupported) {
      setVoiceError('Voice input not supported in this browser')
      return
    }

    if (isRecording) {
      voiceRecognition.stopListening()
      setIsRecording(false)
      setInterimTranscript('')
      return
    }

    setVoiceError(null)
    setIsRecording(true)
    voiceRecognition.startListening(
      (result) => {
        if (result.isFinal) {
          setComposerValue((prev) => (prev + ' ' + result.transcript).trim())
          setInterimTranscript('')
        } else {
          setInterimTranscript(result.transcript)
        }
      },
      (error) => {
        setVoiceError(error)
        setIsRecording(false)
        setInterimTranscript('')
      },
      () => {
        setIsRecording(false)
        setInterimTranscript('')
      },
    )
  }

  /**
   * Extracts the 'done' text from the last entry in the all_model_outputs list.
   * @param agentHistoryString The raw string output from AgentHistoryList.
   * @returns The extracted text string, or null if not found.
   */
  function getLastDoneText(agentHistoryString: string): string | null {
    // 1. Isolate the string content of the 'all_model_outputs' array
    const match = agentHistoryString.match(/all_model_outputs=\[(.*)\]\)/)
    if (!match || !match[1]) {
      console.error("Could not find 'all_model_outputs' in the string.")
      return null
    }

    // 2. Convert the Python-like string into a valid JSON string
    const jsonString = `[${match[1]}]`
      .replace(/'/g, '"') // Replace single quotes with double quotes
      .replace(/None/g, 'null') // Replace Python's None with JSON's null
      .replace(/True/g, 'true') // Replace Python's True with JSON's true
      .replace(/False/g, 'false') // Replace Python's False with JSON's false

    try {
      // 3. Parse the cleaned string into a JavaScript array
      const allModelOutputs = JSON.parse(jsonString)

      // 4. Get the last object from the array
      const lastOutput = allModelOutputs[allModelOutputs.length - 1]

      // 5. Check for the 'done.text' property and return it
      if (lastOutput && lastOutput.done && typeof lastOutput.done.text === 'string') {
        return lastOutput.done.text
      }
    } catch (error) {
      console.error('Failed to parse JSON string:', error)
      return null
    }

    return null // Return null if the structure isn't as expected
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
    <div
      key={renderKey}
      className="h-screen bg-gradient-to-b from-[#d5e5ff] to-[#e6ecff] text-[#1e2141] font-['Inter',_system-ui]"
    >
      <div className="flex flex-col h-full gap-4 px-4 py-4">
        <header className="relative rounded-[32px] bg-[#a39be1] text-white px-5 py-3 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={logo} alt="Browze.AI logo" className="h-9 w-9 rounded-2xl object-contain bg-white/20 p-1" />
              <div className="flex flex-col leading-tight">
                <span className="text-lg font-semibold">Browze.AI</span>
                <span className="text-xs opacity-80 flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-300' : 'bg-red-300'}`} />
                  {connected ? 'Online' : 'Offline'}
                </span>
              </div>
          </div>
          <div className="flex items-center gap-2">
            <button
                className="h-9 w-9 rounded-full bg-white/20 text-white text-lg font-semibold shadow-inner hover:bg-white/30 transition-colors"
                title="New chat"
                onClick={handleNewChat}
              >
                +
              </button>
              <button
                className="h-9 w-9 rounded-full bg-white/20 text-white text-base shadow-inner hover:bg-white/30 transition-colors"
                title="Refresh chat"
                onClick={handleRefreshChat}
              >
                ↻
            </button>
              <button
                className="h-9 w-9 rounded-full bg-white/20 text-white text-base shadow-inner hover:bg-white/30 transition-colors"
                title="More"
                onClick={(event) => {
                  event.stopPropagation()
                  setShowUtilityMenu((prev) => !prev)
                }}
              >
                ⋮
              </button>
            </div>
          </div>
          {showUtilityMenu && (
            <div
              className="absolute right-4 top-[calc(100%+0.75rem)] w-36 rounded-2xl bg-white text-[#44497a] shadow-2xl border border-[#e0e2ff] py-2"
              onClick={(event) => event.stopPropagation()}
            >
            <button
                className="w-full text-left px-4 py-2 hover:bg-[#eef0ff]"
                onClick={() => handleMenuSelect('settings')}
              >
                Settings
            </button>
            <button
                className="w-full text-left px-4 py-2 hover:bg-[#eef0ff]"
                onClick={() => handleMenuSelect('history')}
              >
                History
            </button>
          </div>
          )}
        </header>

        {showTaskProgress && (
          <section className="rounded-[28px] bg-white shadow-[0_20px_60px_rgba(111,121,255,0.15)] border border-[#dfe3ff] px-5 py-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-[#7c82a8]">Current task</p>
                <p className="text-base font-semibold text-[#363c6f]">
                  {activeTaskTitle || 'Running task'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  title={taskStatus.is_paused ? 'Resume task' : 'Pause task'}
                  onClick={taskStatus.is_paused ? handleResumeTask : handlePauseTask}
                  disabled={!taskStatus.is_running}
                  className={`h-9 w-9 rounded-full border border-[#d1d6ff] flex items-center justify-center text-[#4b4f80] shadow-inner ${
                    taskStatus.is_running ? 'bg-white hover:bg-[#f4f5ff]' : 'bg-[#f2f3ff]'
                  }`}
                >
                  {taskStatus.is_paused ? (
                    <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M7 4l8 6-8 6z" fill="currentColor" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <rect x="5" y="4" width="3" height="12" rx="1" fill="currentColor" />
                      <rect x="12" y="4" width="3" height="12" rx="1" fill="currentColor" />
                    </svg>
                  )}
                </button>
                <button
                  title="Stop task"
                  onClick={handleStopTask}
                  disabled={!taskStatus.is_running}
                  className={`h-9 w-9 rounded-full border border-[#d1d6ff] flex items-center justify-center text-[#4b4f80] shadow-inner ${
                    taskStatus.is_running ? 'bg-white hover:bg-[#f4f5ff]' : 'bg-[#f2f3ff]'
                  }`}
                >
                  <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <rect x="6" y="6" width="8" height="8" rx="1.5" fill="currentColor" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="rounded-2xl border border-[#dfe4ff] bg-[#f5f6ff] px-4 py-3 space-y-2">
              {taskSteps.map((step) => (
                <div key={step.id} className="flex items-center gap-3 text-sm">
                  <span
                    className={`h-4 w-4 rounded-full flex items-center justify-center border text-[10px] ${
                      step.status === 'complete'
                        ? 'bg-[#4c63ff] border-[#4c63ff] text-white'
                        : step.status === 'active'
                        ? 'border-[#4c63ff] text-[#4c63ff]'
                        : 'border-[#c5c9ec] text-[#c5c9ec]'
                    }`}
                  >
                    {step.status === 'complete' ? '✓' : ''}
                  </span>
                  <span
                    className={`${
                      step.status === 'complete'
                        ? 'text-[#4b5178]'
                        : step.status === 'active'
                        ? 'text-[#2f3570] font-semibold'
                        : 'text-[#9aa0c5]'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="flex-1 rounded-[32px] bg-white shadow-[0_25px_70px_rgba(93,102,255,0.18)] border border-[#dee1ff] px-4 py-5">
          {activeSection === 'chat' && (
            <div className="flex flex-col h-full">
              <div className="flex-1 min-h-0">
                <ChatMessages messages={messages} isTyping={isTyping} />
              </div>
            </div>
          )}

          {activeSection === 'history' && (
            <div className="h-full flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-[#454b7f]">Previous chats</h2>
                <button
                  className="text-xs text-[#6a72a4] underline hover:text-[#4a4f7c]"
                  onClick={() => setActiveSection('chat')}
                >
                  Back to chat
                </button>
              </div>
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-[#7a80a8] mt-10">No conversations yet.</div>
                ) : (
                  chatHistory
                    .slice()
                    .reverse()
                    .map((entry) => (
                      <div
                        key={entry.id}
                        className="rounded-2xl border border-[#eceeff] bg-[#f6f7ff] px-4 py-3 shadow-sm"
                      >
                        <div className="flex items-center justify-between text-xs text-[#7b81a8] mb-1">
                          <span className="font-medium">{entry.type === 'user' ? 'You' : 'Assistant'}</span>
                          <span>{entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <p className="text-sm text-[#44497a] line-clamp-3">{entry.content}</p>
                      </div>
                    ))
                )}
              </div>
            </div>
          )}

          {activeSection === 'settings' && (
            <div className="h-full flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[#454b7f]">Quick settings</h2>
                <button
                  className="text-xs text-[#6a72a4] underline hover:text-[#4a4f7c]"
                  onClick={() => setActiveSection('chat')}
                >
                  Back to chat
                </button>
              </div>
              <div className="rounded-2xl border border-[#eceeff] bg-[#f8f9ff] px-4 py-3 shadow-sm">
                <p className="text-xs uppercase tracking-wide text-[#8a90ba] mb-1">Server URL</p>
                <p className="text-sm text-[#404572] font-medium">{settings.serverUrl || 'Not configured'}</p>
              </div>
              <div className="rounded-2xl border border-[#eceeff] bg-[#f8f9ff] px-4 py-3 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-sm text-[#404572]">
                  <span>Auto reconnect</span>
                  <span className="font-semibold">{settings.autoReconnect ? 'On' : 'Off'}</span>
                </div>
                <div className="flex items-center justify-between text-sm text-[#404572]">
                  <span>Notifications</span>
                  <span className="font-semibold">{settings.showNotifications ? 'Enabled' : 'Muted'}</span>
                </div>
                <div className="flex items-center justify-between text-sm text-[#404572]">
                  <span>Max log entries</span>
                  <span className="font-semibold">{settings.maxLogs}</span>
                </div>
              </div>
              <button
                onClick={openOptionsPage}
                className="mt-auto rounded-2xl bg-[#a39be1] text-white py-3 font-medium shadow-lg hover:bg-[#928dd4] transition-colors"
              >
                Open full settings
              </button>
            </div>
          )}
        </section>

        {activeSection === 'chat' && (
          <footer>
            <div className="rounded-[32px] bg-[#a6aeff] flex items-center gap-3 px-4 py-3 shadow-[0_15px_35px_rgba(83,91,255,0.35)] border border-white/40">
              <input
                value={interimTranscript || composerValue}
                onChange={(event) => {
                  setComposerValue(event.target.value)
                  setInterimTranscript('')
                }}
                placeholder={isRecording ? 'Listening...' : 'Type your message here...'}
                className="flex-1 bg-transparent text-white placeholder-white/70 text-sm outline-none"
              />
              <button
                className={`h-10 w-10 rounded-2xl bg-white/20 text-white flex items-center justify-center shadow-inner transition-colors ${
                  isRecording ? 'bg-rose-500/80' : 'hover:bg-white/30'
                }`}
                title="Voice input"
                onClick={toggleRecording}
              >
                🎙️
              </button>
              <button
                className="h-10 w-10 rounded-2xl bg-[#1d2db3] text-white flex items-center justify-center shadow-lg hover:bg-[#1a27a0] transition-colors"
                title="Send"
                onClick={handleComposerSend}
                disabled={!composerValue.trim()}
              >
                ▶
              </button>
            </div>
            {voiceError && <p className="text-xs text-rose-600 mt-2">{voiceError}</p>}
            {!voiceSupported && (
              <p className="text-xs text-white/70 mt-1">Voice input is unavailable in this browser.</p>
            )}
          </footer>
        )}
      </div>
    </div>
  )
}

export default SidePanel
