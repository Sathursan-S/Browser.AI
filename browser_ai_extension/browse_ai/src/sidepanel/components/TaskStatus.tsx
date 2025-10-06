import { R } from 'vite/dist/node/types.d-aGj9QkWt'
import './TaskStatus.css'
import React from 'react'

export interface TaskStatusProps {
  isRunning: boolean
  currentTask: string | null
  isPaused?: boolean
}

export const TaskStatus: React.FC<TaskStatusProps> = ({
  isRunning,
  currentTask,
  isPaused = false,
}: TaskStatusProps) => {
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
