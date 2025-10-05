import { useState, useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

import './SidePanel.css'
import { ChatInput } from './components/ChatInput'
import { ExecutionLog, LogEvent } from './components/ExecutionLog'
import { ControlButtons } from './components/ControlButtons'
import { TaskStatus } from './components/TaskStatus'
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

export const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [logs, setLogs] = useState<LogEvent[]>([])
  const [taskStatus, setTaskStatus] = useState<ProtocolTaskStatus>({
    is_running: false,
    current_task: null,
    has_agent: false,
    is_paused: false,
  })
  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS)
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const logsEndRef = useRef<HTMLDivElement>(null)
  const socketRef = useRef<Socket | null>(null)

  // Load settings on mount
  useEffect(() => {
    loadSettings().then(setSettings)
    onSettingsChanged(setSettings)
  }, [])

  // Add log to list with bounded size
  const addLog = (event: LogEvent) => {
    setLogs((prev) => {
      const updated = [...prev, event]
      return updated.length > settings.maxLogs ? updated.slice(-settings.maxLogs) : updated
    })
  }

  // Show notification popup
  const showNotificationPopup = async (
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
  }

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

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
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
      console.log('Disconnected from Browser.AI server')
    })

    newSocket.on('status', (status: ProtocolTaskStatus) => {
      setTaskStatus(status)
      console.log('Received status update:', status)
    })

    newSocket.on('log_event', (event: LogEvent) => {
      addLog(event)

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
      }

      // Show notification for errors
      if (event.level === 'ERROR' && event.message.includes('❌')) {
        showNotificationPopup('error', 'An error occurred', event.message)
      }
    })

    newSocket.on('task_started', (data: { message: string }) => {
      console.log('Task started:', data.message)
      addSystemLog(data.message, 'INFO')
      newSocket.emit('get_status')
    })

    newSocket.on(
      'task_action_result',
      (result: { success: boolean; message?: string; error?: string }) => {
        console.log('Task action result:', result)

        if (result.success) {
          newSocket.emit('get_status')
          if (result.message) {
            addSystemLog(result.message, 'INFO')
          }
        } else if (result.error) {
          addSystemLog(result.error, 'ERROR')
        }
      },
    )

    newSocket.on('error', (data: { message: string }) => {
      console.error('Server error:', data.message)
      addSystemLog(data.message, 'ERROR')
    })

    setSocket(newSocket)
    socketRef.current = newSocket

    return () => {
      newSocket.close()
    }
  }, [settings.serverUrl, settings.autoReconnect])

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

      if (response.success) {
        setCdpEndpoint(response.endpoint)
        return response.endpoint
      } else {
        throw new Error(response.error || 'Failed to get CDP endpoint')
      }
    } catch (error) {
      console.error('Failed to get CDP endpoint:', error)
      addSystemLog(`Failed to get CDP endpoint: ${error}`, 'ERROR')
      return null
    }
  }

  const addSystemLog = (message: string, level: string = 'INFO') => {
    const event: LogEvent = {
      timestamp: new Date().toISOString(),
      level,
      logger_name: 'extension',
      message,
      event_type: 'LOG',
    }
    setLogs((prev) => {
      const updated = [...prev, event]
      return updated.length > settings.maxLogs ? updated.slice(-settings.maxLogs) : updated
    })
  }

  const handleStartTask = async (task: string) => {
    if (!task.trim()) {
      addSystemLog('Please enter a task description', 'WARNING')
      return
    }

    if (!connected || !socket) {
      addSystemLog('Not connected to server', 'ERROR')
      return
    }

    let endpoint = cdpEndpoint
    if (!endpoint) {
      addSystemLog('Getting CDP endpoint from current tab...', 'INFO')
      endpoint = (await getCdpEndpoint()) || ''
      if (!endpoint) {
        return
      }
    }

    const payload: StartTaskPayload = {
      task: task,
      cdp_endpoint: endpoint,
      is_extension: true, // Indicate this is running in extension mode
    }

    socket.emit('start_task', payload)

    setTaskStatus((prev) => ({
      ...prev,
      is_running: true,
      is_paused: false,
      current_task: task,
    }))

    addSystemLog(`Starting task: ${task}`, 'INFO')
  }

  const handleStopTask = () => {
    if (!connected || !socket) return
    socket.emit('stop_task')
    setTaskStatus((prev) => ({
      ...prev,
      is_running: false,
      is_paused: false,
      current_task: null,
    }))
    addSystemLog('Stopping task...', 'INFO')
  }

  const handlePauseTask = () => {
    if (!connected || !socket) return
    socket.emit('pause_task')
    setTaskStatus((prev) => ({
      ...prev,
      is_paused: true,
    }))
    addSystemLog('Pausing task...', 'INFO')
  }

  const handleResumeTask = () => {
    if (!connected || !socket) return
    socket.emit('resume_task')
    setTaskStatus((prev) => ({
      ...prev,
      is_paused: false,
    }))
    addSystemLog('Resuming task...', 'INFO')
  }

  const clearLogs = () => {
    setLogs([])
  }

  return (
    <div className="sidepanel-container">
      {/* Header */}
      <header className="sidepanel-header">
        <div className="header-content">
          <div className="header-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#667eea" />
              <path
                d="M2 17L12 22L22 17M2 12L12 17L22 12"
                stroke="#667eea"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <h1>Browser.AI</h1>
          </div>
          <div className="header-actions">
            <button 
              className="settings-button" 
              onClick={openOptionsPage}
              title="Settings"
            >
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
              </svg>
            </button>
            <div className="connection-status">
              <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`}></span>
              <span className="status-text">{connected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="sidepanel-content">
        {/* Task Status Banner */}
        <TaskStatus
          isRunning={taskStatus.is_running}
          currentTask={taskStatus.current_task}
          isPaused={taskStatus.is_paused}
        />

        {/* Control Buttons */}
        <ControlButtons
          isRunning={taskStatus.is_running}
          isPaused={taskStatus.is_paused || false}
          connected={connected}
          onPause={handlePauseTask}
          onResume={handleResumeTask}
          onStop={handleStopTask}
        />

        {/* Execution Logs */}
        <ExecutionLog 
          logs={logs} 
          onClear={clearLogs} 
          devMode={settings.devMode}
        />
      </div>

      {/* Chat Input at Bottom */}
      <div className="sidepanel-footer">
        <ChatInput
          onSendMessage={handleStartTask}
          disabled={taskStatus.is_running}
          placeholder="What would you like me to automate? (e.g., 'Search for Python tutorials')"
        />
      </div>
    </div>
  )
}

export default SidePanel
