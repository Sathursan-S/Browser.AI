import { useEffect, useRef } from 'react'
import './ExecutionLog.css'

export interface LogEvent {
  timestamp: string
  level: string
  logger_name: string
  message: string
  event_type: string
  metadata?: Record<string, any>
}

interface ExecutionLogProps {
  logs: LogEvent[]
  onClear?: () => void
  devMode?: boolean
}

export const ExecutionLog = ({ logs, onClear, devMode = false }: ExecutionLogProps) => {
  const logsEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [logs])

  const getEventIcon = (eventType: string, level: string): string => {
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
      case 'user_help_needed':
        return '🙋'
      default:
        if (level === 'ERROR') return '🔴'
        if (level === 'WARNING') return '⚠️'
        if (level === 'RESULT') return '💡'
        return '📝'
    }
  }

  const getLogLevelClass = (level: string): string => {
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

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) {
      return 'Invalid time'
    }
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  }

  const isStepLog = (eventType: string): boolean => {
    return ['agent_step', 'agent_action', 'agent_result'].includes(eventType)
  }

  const shouldShowLog = (log: LogEvent): boolean => {
    // In dev mode, show all logs
    if (devMode) return true

    // Filter out technical/debug logs for regular users
    const msg = log.message.toLowerCase()

    // Skip debug logs
    if (log.level === 'DEBUG') return false

    // Skip verbose technical logs
    const skipPatterns = [
      'xpath',
      'selector',
      'dom tree',
      'screenshot',
      'memory',
      'cache',
      'token',
      'llm',
      'model',
      'api key',
      'endpoint',
      'cdp',
    ]

    for (const pattern of skipPatterns) {
      if (msg.includes(pattern)) return false
    }

    // Show important events
    const importantEvents = [
      'agent_start',
      'agent_complete',
      'agent_error',
      'agent_step',
      'agent_action',
      'agent_result',
      'user_help_needed',
      'agent_pause',
      'agent_resume',
      'agent_stop',
    ]

    if (importantEvents.includes(log.event_type)) return true

    // Show errors and warnings
    if (log.level === 'ERROR' || log.level === 'WARNING') return true

    // Show result logs
    if (log.level === 'RESULT') return true

    // Default to showing INFO logs
    return true
  }

  const formatUserMessage = (log: LogEvent): string => {
    // In dev mode, return original message
    if (devMode) return log.message

    console.log('Formatting user message:', log)

    const msg = log.message.toLowerCase()

    // Task lifecycle messages
    if (msg.includes('starting task') || msg.includes('🚀')) {
      return '🚀 Starting your automation task...'
    }

    if (msg.includes('task completed successfully')) {
      return '✅ Task completed successfully!'
    }

    if (msg.includes('task failed') || msg.includes('❌')) {
      return '❌ Task failed. Please check the details.'
    }

    if (msg.includes('task stopped') || msg.includes('⏹️')) {
      return '⏹️ Task has been stopped'
    }

    if (msg.includes('pausing') || msg.includes('⏸️')) {
      return '⏸️ Task paused'
    }

    if (msg.includes('resuming') || msg.includes('▶️')) {
      return '▶️ Resuming task...'
    }

    if (msg.includes('result:') && log.level === 'INFO') {
      return '📄 Result : ' + msg.split('result:')[1].trim()
    }

    // Step messages
    if (msg.includes('step') && log.event_type === 'agent_step') {
      const stepMatch = msg.match(/step (\d+)/i)
      if (stepMatch) {
        return `📍 Processing step ${stepMatch[1]}...`
      }
      return '📍 Processing next step...'
    }

    // Action messages
    if (msg.includes('clicked') || msg.includes('clicking')) {
      return '⚡ Clicking element...'
    }

    if (msg.includes('typing') || msg.includes('input')) {
      return '⚡ Entering text...'
    }

    if (msg.includes('navigat') || msg.includes('going to')) {
      return '⚡ Navigating to page...'
    }

    if (msg.includes('scrolling') || msg.includes('scroll')) {
      return '⚡ Scrolling page...'
    }

    if (msg.includes('waiting')) {
      return '⏱️ Waiting for page to load...'
    }

    // Result messages
    if (log.event_type === 'agent_result' || msg.includes('extracted') || msg.includes('found')) {
      return '✨ Data collected successfully'
    }

    // Error messages (show some detail but simplified)
    if (log.level === 'ERROR') {
      if (msg.includes('timeout')) {
        return '⚠️ Operation timed out. Retrying...'
      }
      if (msg.includes('element not found')) {
        return '⚠️ Could not find element on page'
      }
      if (msg.includes('connection')) {
        return '⚠️ Connection issue detected'
      }
      return '⚠️ An error occurred'
    }

    // Warning messages
    if (log.level === 'WARNING') {
      return '⚠️ ' + log.message
    }

    // User interaction needed
    if (msg.includes('requesting user help') || msg.includes('🙋')) {
      return '🙋 Your input is needed'
    }

    // Default: return original for INFO level
    return log.message
  }

  // Filter logs based on dev mode
  const filteredLogs = logs.filter(shouldShowLog)

  return (
    <div className="execution-log-container">
      <div className="execution-log-header">
        <div className="log-header-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2L2 7L12 12L22 7L12 2Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M2 17L12 22L22 17"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M2 12L12 17L22 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <h3>{devMode ? 'Developer Logs' : 'Activity'}</h3>
          <span className="log-count">{filteredLogs.length}</span>
        </div>
        {onClear && filteredLogs.length > 0 && (
          <button className="log-clear-btn" onClick={onClear}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path
                d="M6 18L18 6M6 6L18 18"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            Clear
          </button>
        )}
      </div>

      <div className="execution-log-content" ref={containerRef}>
        {filteredLogs.length === 0 ? (
          <div className="log-empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" />
              <path
                d="M12 8V12L14.5 14.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            <p>No activity yet</p>
            <span>Start a task to see what's happening</span>
          </div>
        ) : (
          <div className="log-entries">
            {filteredLogs.map((log, index) => (
              <div
                key={`${log.timestamp}-${index}`}
                className={`log-entry ${getLogLevelClass(log.level)} ${
                  isStepLog(log.event_type) ? 'log-step-entry' : ''
                } log-entry-animate log-entry-${Math.min(index, 5)}`}
              >
                <div className="log-entry-header">
                  <span className="log-icon">{getEventIcon(log.event_type, log.level)}</span>
                  <span className="log-timestamp">{formatTime(log.timestamp)}</span>
                  {devMode && (
                    <span className={`log-badge ${getLogLevelClass(log.level)}`}>{log.level}</span>
                  )}
                </div>
                <div className="log-message">{formatUserMessage(log)}</div>
                {devMode && log.metadata && Object.keys(log.metadata).length > 0 && (
                  <div className="log-metadata">
                    {Object.entries(log.metadata).map(([key, value]) => (
                      <div key={key} className="metadata-item">
                        <span className="metadata-key">{key}:</span>
                        <span className="metadata-value">
                          {(() => {
                            try {
                              return JSON.stringify(value)
                            } catch {
                              return '[Unstringifiable value]'
                            }
                          })()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
    </div>
  )
}
