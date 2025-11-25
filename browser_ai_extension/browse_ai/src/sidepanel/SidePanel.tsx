import { useState, useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

import { ChatInput } from './components/ChatInput'
import { StepList } from './components/TaskProgress/StepList'
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
  const [concentrationMode, setConcentrationMode] = useState(false)
  const [taskResult, setTaskResult] = useState<string>("")

  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS)
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const socketRef = useRef<Socket | null>(null)

  // Scroll ref
  const scrollRef = useRef<HTMLDivElement>(null)

  // Voice State Hook (lifted from ChatInput roughly, but we need to know global listening state)
  // Actually, ChatInput manages listening state internally.
  // We need to know if we are in "Voice Mode" to trigger Concentration Mode.
  // We can infer this: If ChatInput triggers a start via voice, or if we toggle it.
  // For now, let's add a manual toggle or infer from interaction.
  // Requirement: "Implement concentration mode with voice... visualize the voice".

  // Let's track if voice is active via an event listener or shared state service if possible,
  // but since VoiceRecognition is a singleton service, we can add a listener to it or just pass callbacks.
  // Refactoring ChatInput to expose `isListening` or lifting the state up would be cleaner.
  // For this plan, let's lift `isListening` state to SidePanel so we can drive the UI.

  const [isListening, setIsListening] = useState(false)

  // Auto-scroll logs
  useEffect(() => {
    if (scrollRef.current && !concentrationMode) {
       scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, concentrationMode])

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
  useEffect(() => { saveTaskStatus(taskStatus) }, [taskStatus])
  useEffect(() => { if (cdpEndpoint) saveCdpEndpoint(cdpEndpoint) }, [cdpEndpoint])

  // Update Page Overlay based on status
  const updateOverlay = useCallback(async (status: string, isError: boolean = false) => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, {
          type: 'SHOW_OVERLAY_STATUS',
          message: status,
          isError
        }).catch(() => {})
      }
    } catch (e) { console.error(e) }
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
      if (event.event_type === 'agent_result' || (event.message.includes('Result:') && event.level === 'INFO')) {
         setTaskResult(event.message.replace('Result:', '').trim())
      }
    })

    newSocket.on('task_started', (data: { message: string }) => {
      setLogs([])
      setTaskResult("")
      updateOverlay('Starting Task...', false)
    })

    // Explicit task result event handling if backend sends it
    newSocket.on('task_result', (result: { task: string; success: boolean; history: string | null }) => {
       if (result.success && result.history) {
          // Try to extract final text or just use a success message
          setTaskResult("Task completed successfully.")
       }
    })

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
    setTaskResult("")

    // If we started via voice (implied if we are in concentration mode or isListening was true recently),
    // keep concentration mode on.
    // Otherwise, default to standard view unless toggled.
  }

  const handleStopTask = () => {
    socket?.emit('stop_task')
    updateOverlay('Stopping...', false)
  }

  const handlePauseTask = () => socket?.emit('pause_task')
  const handleResumeTask = () => socket?.emit('resume_task')

  // Auto-switch to Concentration Mode when listening starts
  useEffect(() => {
    if (isListening) {
      setConcentrationMode(true)
    }
  }, [isListening])

  return (
    <Layout>
      {/* Header */}
      <header className="flex-none px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm z-10">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-blue-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-white">
                <circle cx="12" cy="12" r="3" fill="currentColor" />
                <path d="M12 2v4m0 12v4m10-10h-4M6 12H2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 dark:text-white leading-none">Browser.AI</h1>
              <div className="flex items-center gap-1.5 mt-1">
                <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                  {connected ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1">
             {/* Concentration Mode Toggle */}
            <button
              onClick={() => setConcentrationMode(!concentrationMode)}
              className={`p-2 rounded-lg transition-colors ${
                concentrationMode
                  ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
              title="Toggle Focus Mode"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>

            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            >
              {theme === 'light' ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
              )}
            </button>
            <button
              onClick={openOptionsPage}
              className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            >
               <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700 relative flex flex-col"
      >
        {/* Active Task Banner / Sticky Header */}
        {(taskStatus.is_running || taskStatus.current_task) && (
          <TaskStatusHeader
            task={taskStatus.current_task || "Unknown Task"}
            status={
              taskStatus.is_paused ? 'paused' :
              taskStatus.is_running ? 'running' :
              logs.find(l => l.level === 'ERROR') ? 'failed' : 'completed'
            }
            result={taskResult}
            onClose={() => {
              setTaskResult("")
              // Optional: Clear task status here or just hide UI
            }}
          />
        )}

        {concentrationMode ? (
          /* Concentration Mode View */
          <div className="flex-1 flex flex-col items-center justify-center p-6 min-h-[300px]">
            <VoiceVisualizer isListening={isListening} isSpeaking={false} />

            {/* Minimal controls for concentration mode */}
            {taskStatus.is_running && (
              <div className="mt-8">
                 <button
                   onClick={handleStopTask}
                   className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-full font-medium shadow-lg shadow-red-500/30 transition-transform active:scale-95 flex items-center gap-2"
                 >
                   <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                     <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                   </svg>
                   Stop Task
                 </button>
              </div>
            )}
          </div>
        ) : (
          /* Standard View */
          <>
            {!taskStatus.is_running && logs.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center p-8 text-center opacity-0 animate-[fadeInUp_0.5s_ease-out_forwards]">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 flex items-center justify-center mb-6">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" className="text-blue-500 dark:text-blue-400">
                    <path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2z" stroke="currentColor" strokeWidth="2"/>
                    <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
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
      {/* Hide standard input in concentration mode if listening? No, user might want to type. */}
      {/* But Concentration Mode usually implies Hands-Free. Let's keep it visible but minimal. */}

      <div className={`flex-none p-4 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 ${concentrationMode ? 'hidden' : ''}`}>
        <ChatInput
          onSendMessage={handleStartTask}
          onStopTask={handleStopTask}
          onPauseTask={handlePauseTask}
          onResumeTask={handleResumeTask}
          isRunning={taskStatus.is_running}
          isPaused={taskStatus.is_paused}
          disabled={!connected}
          // We need to pass a callback to update local isListening state
          // However, ChatInput encapsulates it.
          // To properly implement the requirement "visualize the voice",
          // we should probably control listening state here or lift it.
          // For now, I'll modify ChatInput to accept an onListeningChange prop.
          // Since I can't easily modify ChatInput signature without checking it again...
          // I checked it in previous turns. It has local state.
          // Let's modify ChatInput.tsx next to support lifting state.
        />
      </div>

      {/* Voice Controls for Concentration Mode (if we hide standard input) */}
      {concentrationMode && (
         <div className="flex-none p-6 bg-slate-950 border-t border-slate-800 flex justify-center pb-8">
            <button
               onClick={() => {
                 // Toggle listening
                 // Note: Ideally we call into ChatInput or VoiceService
                 // Since logic is in ChatInput, we really should refactor ChatInput to be a controlled component or similar.
                 // For this immediate task, let's assume the user toggles back to standard view to type,
                 // OR we put the ChatInput *inside* the concentration view but styled differently?
                 // Let's just provide a "Close Focus Mode" button.
                 setConcentrationMode(false)
               }}
               className="text-slate-400 hover:text-white text-sm font-medium"
            >
              Exit Focus Mode
            </button>
         </div>
      )}
    </Layout>
  )
}

export default SidePanel
