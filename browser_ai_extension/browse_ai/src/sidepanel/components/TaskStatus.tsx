import './TaskStatus.css'

interface TaskStatusProps {
  isRunning: boolean
  currentTask: string | null
  isPaused?: boolean
}

export const TaskStatus = ({ isRunning, currentTask, isPaused = false }: TaskStatusProps) => {
  if (!isRunning || !currentTask) {
    return null
  }

  return (
    <div className={`task-status-banner ${isPaused ? 'paused' : ''}`}>
      <div className="task-status-indicator">
        <div className="status-spinner"></div>
      </div>
      <div className="task-status-content">
        <div className="task-status-label">{isPaused ? '⏸️ Paused' : '🚀 Running'}</div>
        <div className="task-status-description">{currentTask}</div>
      </div>
    </div>
  )
}
