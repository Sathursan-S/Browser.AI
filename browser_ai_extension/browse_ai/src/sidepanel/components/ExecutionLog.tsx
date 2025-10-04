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
}

export const ExecutionLog = ({ logs, onClear }: ExecutionLogProps) => {
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
          <h3>Execution Logs</h3>
          <span className="log-count">{logs.length}</span>
        </div>
        {onClear && logs.length > 0 && (
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
        {logs.length === 0 ? (
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
            <p>No logs yet</p>
            <span>Start a task to see live execution details</span>
          </div>
        ) : (
          <div className="log-entries">
            {logs.map((log, index) => (
              <div
                key={index}
                className={`log-entry ${getLogLevelClass(log.level)} ${
                  isStepLog(log.event_type) ? 'log-step-entry' : ''
                } log-entry-animate log-entry-${Math.min(index, 5)}`}
              >
                <div className="log-entry-header">
                  <span className="log-icon">{getEventIcon(log.event_type, log.level)}</span>
                  <span className="log-timestamp">{formatTime(log.timestamp)}</span>
                  <span className={`log-badge ${getLogLevelClass(log.level)}`}>{log.level}</span>
                </div>
                <div className="log-message">{log.message}</div>
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <div className="log-metadata">
                    {Object.entries(log.metadata).map(([key, value]) => (
                      <div key={key} className="metadata-item">
                        <span className="metadata-key">{key}:</span>
                        <span className="metadata-value">{JSON.stringify(value)}</span>
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
