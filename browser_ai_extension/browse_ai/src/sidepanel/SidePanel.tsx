import { useState, useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

import { ChatInput } from './components/ChatInput'
import { ConversationMode } from './components/ConversationMode'
import { StepList } from './components/TaskProgress/StepList'
import LiveKitJarvisMode from './components/LiveKitJarvisMode'
import { TaskStatusHeader } from './components/TaskProgress/TaskStatusHeader'
import { VoiceVisualizer } from './components/Visuals/VoiceVisualizer'
import { LogEvent } from './components/ExecutionLog'
import { Layout } from './components/Layout'
import { useTheme } from '../utils/theme'
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
  loadConversationMessages,
  saveConversationMessages,
  loadConversationIntent,
  saveConversationIntent,
  loadTaskHistory,
  saveTaskHistory,
  loadChatHistory,
  saveChatHistory,
  TaskHistoryEntry,
  ChatHistoryEntry,
} from '../utils/state'

export const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [logs, setLogs] = useState<LogEvent[]>([])

  // Theme context
  const { theme, toggleTheme } = useTheme()

  // Task State
  const [taskStatus, setTaskStatus] = useState<ProtocolTaskStatus>({
    is_running: false,
    current_task: null,
    has_agent: false,
    is_paused: false,
  })

  // UI State
  const [taskResult, setTaskResult] = useState<string>('')
  const [taskHeaderDismissed, setTaskHeaderDismissed] = useState(true)

  // History State
  const [taskHistory, setTaskHistory] = useState<TaskHistoryEntry[]>([])
  const [chatHistory, setChatHistory] = useState<ChatHistoryEntry[]>([])

  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS)
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const socketRef = useRef<Socket | null>(null)

  // Scroll ref
  const scrollRef = useRef<HTMLDivElement>(null)

  // Mode State for switching between Agent and Conversation modes
  const [mode, setMode] = useState<'agent' | 'conversation' | 'livekit-jarvis'>('agent')

  // Conversation State
  const [messages, setMessages] = useState<
    Array<{ role: 'user' | 'assistant'; content: string; timestamp?: string }>
  >([])
  const [intent, setIntent] = useState<{
    task_description: string
    is_ready: boolean
    confidence: number
  } | null>(null)

  // Auto-scroll logs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  // Initial Load
  useEffect(() => {
    let isMounted = true

    loadSettings().then((loadedSettings) => {
      if (isMounted) setSettings(loadedSettings)
    })

    const handleSettingsChange = (newSettings: ExtensionSettings) => {
      if (isMounted) setSettings(newSettings)
    }
    const unsubscribeSettings = onSettingsChanged(handleSettingsChange)

    loadTaskStatus().then((status) => {
      if (isMounted && status) setTaskStatus(status)
    })

    loadCdpEndpoint().then((endpoint) => {
      if (isMounted && endpoint) setCdpEndpoint(endpoint)
    })

    loadTaskHistory().then((history) => {
      if (isMounted && history) setTaskHistory(history)
    })

    loadChatHistory().then((history) => {
      if (isMounted && history) setChatHistory(history)
    })

    const handleTaskStatusChange = (newStatus: ProtocolTaskStatus) => {
      if (isMounted) setTaskStatus(newStatus)
    }
    const unsubscribeTaskStatus = onTaskStatusChanged(handleTaskStatusChange)

    return () => {
      isMounted = false
      unsubscribeSettings()
      unsubscribeTaskStatus()
    }
  }, [])

  // Persistence
  useEffect(() => {
    saveTaskStatus(taskStatus)
  }, [taskStatus])
  useEffect(() => {
    if (cdpEndpoint) saveCdpEndpoint(cdpEndpoint)
  }, [cdpEndpoint])
  useEffect(() => {
    saveTaskHistory(taskHistory)
  }, [taskHistory])
  useEffect(() => {
    saveChatHistory(chatHistory)
  }, [chatHistory])

  // Update Page Overlay based on status
  const updateOverlay = useCallback(async (status: string, isError: boolean = false) => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (tab?.id) {
        chrome.tabs
          .sendMessage(tab.id, {
            type: 'SHOW_OVERLAY_STATUS',
            message: status,
            isError,
          })
          .catch(() => {})
      }
    } catch (e) {
      console.error(e)
    }
  }, [])

  const hideOverlay = useCallback(async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { type: 'HIDE_OVERLAY' }).catch(() => {})
      }
    } catch (e) {}
  }, [])

  // Socket Connection
  useEffect(() => {
    if (socketRef.current) socketRef.current.close()

    const newSocket = io(`${settings.serverUrl}${WEBSOCKET_NAMESPACE}`, {
      transports: ['websocket'],
      reconnection: settings.autoReconnect,
      reconnectionAttempts: MAX_RECONNECTION_ATTEMPTS,
      reconnectionDelay: RECONNECTION_DELAY_MS,
    })

    newSocket.on('connect', () => {
      setConnected(true)
      newSocket.emit('extension_connect')
      newSocket.emit('get_status')

      // Initial greeting for conversation mode
      if (mode === 'conversation' && messages.length === 0) {
        setMessages([
          {
            role: 'assistant',
            content:
              "👋 Hi! I'm your Browser.AI assistant. What would you like me to help you automate today? I can help with shopping, downloads, research, form filling, and more!",
            timestamp: new Date().toISOString(),
          },
        ])
      }
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
    })

    newSocket.on('status', (status: ProtocolTaskStatus) => {
      setTaskStatus(status)
      if (!status.is_running) {
        if (status.current_task?.includes('failed')) {
          updateOverlay('Task Failed', true)
        } else if (status.current_task?.includes('completed')) {
          updateOverlay('Task Completed', false)
          setTimeout(hideOverlay, 3000)
        }
      } else {
        updateOverlay('Browser.AI Running...', false)
      }
    })

    newSocket.on('log_event', (event: LogEvent) => {
      setLogs((prev) => [...prev, event])

      // Update overlay with high-level steps
      if (event.event_type === 'agent_step') {
        const title = event.message.replace(/Step \d+:/i, '').trim()
        updateOverlay(title || 'Processing step...', false)
      }

      // Capture result from logs if available (heuristic)
      if (
        event.event_type === 'agent_result' ||
        (event.message.includes('Result:') && event.level === 'INFO')
      ) {
        setTaskResult(event.message.replace('Result:', '').trim())
      }
    })

    newSocket.on('task_started', (data: { message: string }) => {
      // Save current task to history before starting new one
      if (taskStatus.current_task || taskResult || logs.length > 0) {
        setTaskHistory((prev) => [
          ...prev,
          {
            task: taskStatus.current_task || 'Unknown Task',
            result: taskResult,
            logs: [...logs],
            timestamp: new Date().toISOString(),
            mode: mode,
          },
        ])
      }

      // Save current conversation if in conversation mode
      if (mode === 'conversation' && messages.length > 1) {
        // More than just greeting
        setChatHistory((prev) => [
          ...prev,
          {
            messages: [...messages],
            timestamp: new Date().toISOString(),
          },
        ])
      }

      setLogs([])
      setTaskResult('')
      setTaskHeaderDismissed(false)
      updateOverlay('Starting Task...', false)
    })

    newSocket.on(
      'task_result',
      (result: { task: string; success: boolean; history: string | null }) => {
        if (result.success && result.history) {
          // Try to extract final text or just use a success message
          setTaskResult('Task completed successfully.')
        }
      },
    )

    // Conversation mode events
    newSocket.on('chat_response', (data: { role: string; content: string; intent?: any }) => {
      const message = {
        role: data.role as 'user' | 'assistant',
        content: data.content,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, message])

      if (data.intent && data.intent.is_ready) {
        setIntent(data.intent)
      }
    })

    newSocket.on('conversation_reset', (data: { role: string; content: string }) => {
      setMessages([
        {
          role: data.role as 'assistant',
          content: data.content,
          timestamp: new Date().toISOString(),
        },
      ])
      setIntent(null)
    })

    newSocket.on(
      'agent_needs_help',
      (data: {
        reason: string
        summary: string
        attempted_actions: string[]
        duration: number
        suggestion: string
      }) => {
        const helpMessage = {
          role: 'assistant' as const,
          content: data.summary,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, helpMessage])
      },
    )

    setSocket(newSocket)
    socketRef.current = newSocket

    return () => {
      newSocket.close()
    }
  }, [settings.serverUrl, updateOverlay, hideOverlay])

  const getCdpEndpoint = async () => {
    const endpoint = 'http://localhost:9222'
    setCdpEndpoint(endpoint)
    return endpoint
  }

  const handleStartTask = async (task: string) => {
    if (!task.trim() || !socket) return

    let endpoint = cdpEndpoint
    if (!endpoint) {
      endpoint = (await getCdpEndpoint()) || ''
    }

    const payload: StartTaskPayload = {
      task: task,
      cdp_endpoint: endpoint,
      is_extension: true,
    }

    socket.emit('start_task', payload)

    setLogs([])
    setTaskResult('')

    // Voice input is handled within conversation mode now.
  }

  const handleStartClarifiedTask = async (task: string, cdpEndpoint: string) => {
    if (!task.trim() || !socket) return

    const payload: StartTaskPayload = {
      task: task,
      cdp_endpoint: cdpEndpoint,
      is_extension: true,
    }

    socket.emit('start_clarified_task', payload)

    setLogs([])
    setTaskResult('')
  }

  const handleStopTask = () => {
    socket?.emit('stop_task')
    updateOverlay('Stopping...', false)
  }

  const handlePauseTask = () => socket?.emit('pause_task')
  const handleResumeTask = () => socket?.emit('resume_task')

  return (
    <Layout>
      {/* Header */}
      <header className="flex-none px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm z-10">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-blue-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-white">
                <circle cx="12" cy="12" r="3" fill="currentColor" />
                <path
                  d="M12 2v4m0 12v4m10-10h-4M6 12H2"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 dark:text-white leading-none">
                Browser.AI
              </h1>
              <div className="flex items-center gap-1.5 mt-1">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}
                />
                <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                  {connected ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1">
            {/* Mode Toggle */}
            <button
              onClick={() => {
                setMode(mode === 'agent' ? 'conversation' : 'agent')
                if (mode === 'conversation') {
                  // Switching to agent mode, reset conversation state
                  setMessages([])
                  setIntent(null)
                }
              }}
              className={`p-2 rounded-lg transition-colors ${
                mode === 'conversation'
                  ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'
                  : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
              title={`Switch to ${mode === 'agent' ? 'Conversation' : 'Agent'} Mode`}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                {mode === 'conversation' ? (
                  <>
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    <line x1="9" y1="9" x2="15" y2="9" />
                    <line x1="9" y1="12" x2="12" y2="12" />
                  </>
                ) : (
                  <circle cx="12" cy="12" r="3" />
                )}
              </svg>
            </button>

            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            >
              {theme === 'light' ? (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              ) : (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="5" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
              )}
            </button>
            <button
              onClick={openOptionsPage}
              className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {mode === 'livekit-jarvis' ? (
        <LiveKitJarvisMode />
      ) : (
      {/* Main Content Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700 relative flex flex-col"
        onClick={() => {
          setTaskHeaderDismissed(!taskStatus.is_running)
          if (mode === 'conversation') {
            setMessages([])
            setIntent(null)
          }
        }}
      >
        {/* Active Task Banner / Sticky Header */}
        {(taskStatus.is_running || taskStatus.current_task) && !taskHeaderDismissed && (
          <TaskStatusHeader
            key={taskStatus.current_task || 'no-task'}
            task={taskStatus.current_task || 'Unknown Task'}
            status={
              taskStatus.is_paused
                ? 'paused'
                : taskStatus.is_running
                  ? 'running'
                  : logs.find((l) => l.level === 'ERROR')
                    ? 'failed'
                    : 'completed'
            }
            result={taskResult}
            onClose={() => {
              setTaskHeaderDismissed(true)
              setTaskResult('')
              // Clear conversation messages when dismissing in conversation mode
              if (mode === 'conversation') {
                setMessages([])
                setIntent(null)
              }
            }}
          />
        )}

        {mode === 'conversation' ? (
          /* Conversation Mode */
          <ConversationMode
            socket={socket}
            connected={connected}
            onStartTask={handleStartClarifiedTask}
            cdpEndpoint={cdpEndpoint}
            messages={messages}
            setMessages={setMessages}
            intent={intent}
            setIntent={setIntent}
            onSwitchToAgent={() => setMode('agent')}
          />
        ) : (
          /* Standard Agent View */
          <>
            {!taskStatus.is_running && logs.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center p-8 text-center opacity-0 animate-[fadeInUp_0.5s_ease-out_forwards]">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 flex items-center justify-center mb-6">
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    className="text-blue-500 dark:text-blue-400"
                  >
                    <path
                      d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2z"
                      stroke="currentColor"
                      strokeWidth="2"
                    />
                    <path
                      d="M12 16v-4M12 8h.01"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  Ready to automate?
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 max-w-[240px]">
                  Type a task below or use voice to tell me what to do on this page.
                </p>
              </div>
            )}

            {(taskStatus.is_running || logs.length > 0) && (
              <StepList logs={logs} isRunning={taskStatus.is_running} />
            )}
          </>
        )}
      </div>

      {/* Footer / Input */}
      {/* Hide standard input in conversation mode */}
      {mode === 'agent' && (
        <div className="flex-none p-4 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800">
          <ChatInput
            onSendMessage={handleStartTask}
            onStopTask={handleStopTask}
            onPauseTask={handlePauseTask}
            onResumeTask={handleResumeTask}
            isRunning={taskStatus.is_running}
            isPaused={taskStatus.is_paused}
            disabled={!connected}
            onToggleLiveKitJarvisMode={() => setMode('livekit-jarvis')}
            // Voice input is now handled within conversation mode components.
          />
        </div>
      )}
    </Layout>
  )
}

export default SidePanel
