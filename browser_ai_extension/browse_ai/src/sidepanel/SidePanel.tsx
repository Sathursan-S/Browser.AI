import { useState, useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

import './SidePanel.css'

interface LogEvent {
  timestamp: string
  level: string
  logger_name: string
  message: string
  event_type: string
  metadata?: Record<string, any>
}

interface TaskStatus {
  is_running: boolean
  current_task: string | null
  has_agent: boolean
  cdp_endpoint?: string
}

export const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [taskInput, setTaskInput] = useState('')
  const [logs, setLogs] = useState<LogEvent[]>([])
  const [taskStatus, setTaskStatus] = useState<TaskStatus>({
    is_running: false,
    current_task: null,
    has_agent: false,
  })
  const [serverUrl, setServerUrl] = useState('http://localhost:5000')
  const [cdpEndpoint, setCdpEndpoint] = useState('')
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  // Initialize socket connection
  useEffect(() => {
    const newSocket = io(`${serverUrl}/extension`, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
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

    newSocket.on('status', (status: TaskStatus) => {
      setTaskStatus(status)
    })

    newSocket.on('log_event', (event: LogEvent) => {
      setLogs((prev) => [...prev, event])
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
    setLogs((prev) => [...prev, event])
  }

  const handleStartTask = async () => {
    if (!taskInput.trim()) {
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

    socket.emit('start_task', {
      task: taskInput,
      cdp_endpoint: endpoint,
      is_extension: true, // Indicate this is running in extension mode
    })

    addSystemLog(`Starting task: ${taskInput}`, 'INFO')
    setTaskInput('')
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

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'agent_start':
        return '🚀'
      case 'agent_step':
        return '📍'
      case 'agent_action':
        return '⚡'
      case 'agent_result':
        return '✨'
      case 'agent_complete':
        return '✅'
      case 'agent_error':
        return '❌'
      case 'agent_pause':
        return '⏸️'
      case 'agent_resume':
        return '▶️'
      case 'agent_stop':
        return '⏹️'
      default:
        return '📝'
    }
  }

  const getLogLevelClass = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'log-error'
      case 'WARNING':
        return 'log-warning'
      case 'RESULT':
        return 'log-result'
      case 'INFO':
        return 'log-info'
      default:
        return 'log-debug'
    }
  }

  return (
    <div className="sidepanel-container">
      <header className="sidepanel-header">
        <h1>🤖 Browser.AI</h1>
        <div className="connection-status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></span>
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>

      {/* Server Configuration */}
      <div className="config-section">
        <input
          type="text"
          className="server-url-input"
          value={serverUrl}
          onChange={(e) => setServerUrl(e.target.value)}
          placeholder="Server URL"
          disabled={connected}
        />
      </div>

      {/* Task Status */}
      {taskStatus.is_running && (
        <div className="task-status">
          <div className="task-status-header">
            <span className="status-icon">⚙️</span>
            <span className="status-text">Running Task</span>
          </div>
          <div className="task-description">{taskStatus.current_task}</div>
        </div>
      )}

      {/* Chat Input */}
      <div className="chat-section">
        <textarea
          className="task-input"
          value={taskInput}
          onChange={(e) => setTaskInput(e.target.value)}
          placeholder="Describe what you'd like me to do... (e.g., 'Search for Python tutorials and summarize the top 5 results')"
          rows={3}
          disabled={taskStatus.is_running}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              handleStartTask()
            }
          }}
        />
        <div className="chat-controls">
          {!taskStatus.is_running ? (
            <button
              className="btn btn-primary"
              onClick={handleStartTask}
              disabled={!connected || !taskInput.trim()}
            >
              Start Task
            </button>
          ) : (
            <>
              <button className="btn btn-warning" onClick={handlePauseTask}>
                Pause
              </button>
              <button className="btn btn-danger" onClick={handleStopTask}>
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      {/* Logs Section */}
      <div className="logs-section">
        <div className="logs-header">
          <h3>Live Logs</h3>
          <button className="btn btn-small" onClick={clearLogs}>
            Clear
          </button>
        </div>
        <div className="logs-container">
          {logs.length === 0 ? (
            <div className="logs-empty">
              <p>No logs yet. Start a task to see live updates.</p>
            </div>
          ) : (
            logs.map((log, index) => (
              <div
                key={index}
                className={`log-entry ${getLogLevelClass(log.level)} ${
                  log.event_type === 'agent_step' ? 'log-step' : ''
                }`}
              >
                <div className="log-header">
                  <span className="log-icon">{getEventIcon(log.event_type)}</span>
                  <span className="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className="log-level">{log.level}</span>
                </div>
                <div className="log-message">{log.message}</div>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Footer */}
      <footer className="sidepanel-footer">
        <small>Browser automation powered by Browser.AI</small>
      </footer>
    </div>
  )
}

export default SidePanel
