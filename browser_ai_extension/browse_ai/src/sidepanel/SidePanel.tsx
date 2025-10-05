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
  ActionResult,
  DEFAULT_SERVER_URL,
  MAX_RECONNECTION_ATTEMPTS,
  RECONNECTION_DELAY_MS,
  MAX_LOGS,
  WEBSOCKET_NAMESPACE,
} from '../types/protocol'

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
  const [serverUrl, setServerUrl] = useState(DEFAULT_SERVER_URL)
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Add log to list with bounded size
  const addLog = (event: LogEvent) => {
    setLogs((prev) => {
      const updated = [...prev, event]
      return updated.length > MAX_LOGS ? updated.slice(-MAX_LOGS) : updated
    })
  }

  // Show notification popup
  const showNotificationPopup = async (
    notificationType: 'user_interaction' | 'task_complete' | 'error',
    message: string,
    details?: string,
  ) => {
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

  // Initialize socket connection
  useEffect(() => {
    const newSocket = io(`${serverUrl}${WEBSOCKET_NAMESPACE}`, {
      transports: ['websocket'],
      reconnection: true,
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
    })

    newSocket.on(
      'task_action_result',
      (result: { success: boolean; message?: string; error?: string }) => {
        console.log('Task action result:', result)
      },
    )

    newSocket.on('error', (data: { message: string }) => {
      console.error('Server error:', data.message)
      addSystemLog(data.message, 'ERROR')
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [serverUrl])

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
      return updated.length > MAX_LOGS ? updated.slice(-MAX_LOGS) : updated
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

    addSystemLog(`Starting task: ${task}`, 'INFO')
  }

  const handleStopTask = () => {
    if (!connected || !socket) return
    socket.emit('stop_task')
    addSystemLog('Stopping task...', 'INFO')
  }

  const handlePauseTask = () => {
    if (!connected || !socket) return
    socket.emit('pause_task')
    addSystemLog('Pausing task...', 'INFO')
  }

  const handleResumeTask = () => {
    if (!connected || !socket) return
    socket.emit('resume_task')
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
          <div className="connection-status">
            <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="sidepanel-content">
        {/* Server Configuration */}
        <div className="config-section">
          <div className="config-label">Server URL</div>
          <input
            type="text"
            className="server-url-input"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            placeholder="http://localhost:5000"
            disabled={connected}
          />
        </div>

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
        <ExecutionLog logs={logs} onClear={clearLogs} />
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
