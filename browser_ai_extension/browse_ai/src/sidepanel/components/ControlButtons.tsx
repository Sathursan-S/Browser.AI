import React from 'react'
import './ControlButtons.css'

export interface ControlButtonsProps {
  isRunning: boolean
  isPaused: boolean
  connected: boolean
  onStart?: () => void
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
}

const ControlButtonsComponent: React.FC<ControlButtonsProps> = ({
  isRunning,
  isPaused,
  connected,
  onStart,
  onPause,
  onResume,
  onStop,
}: ControlButtonsProps) => {
  // Only show control buttons when a task is actually running
  if (!isRunning) {
    return (
      <div className="control-buttons-container">
        <div className="control-status">
          <div className="status-pulse status-idle"></div>
          <span>Idle</span>
        </div>
        {onStart && (
          <button
            className="control-btn control-btn-start"
            onClick={onStart}
            disabled={!connected}
            title="Start Task"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
              <polygon points="10,8 16,12 10,16" fill="currentColor" />
            </svg>
            Start
          </button>
        )}
        {!onStart && (
          <div className="control-btn control-btn-disabled" title="No start action available">
            Waiting for task...
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="control-buttons-container">
      <div className="control-buttons-group">
        {isPaused ? (
          <button
            className="control-btn control-btn-resume"
            onClick={onResume}
            disabled={!connected}
            title="Resume Task"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M8 5V19L19 12L8 5Z" fill="currentColor" />
            </svg>
            Resume
          </button>
        ) : (
          <button
            className="control-btn control-btn-pause"
            onClick={onPause}
            disabled={!connected}
            title="Pause Task"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect x="6" y="4" width="4" height="16" fill="currentColor" />
              <rect x="14" y="4" width="4" height="16" fill="currentColor" />
            </svg>
            Pause
          </button>
        )}

        <button
          className="control-btn control-btn-stop"
          onClick={onStop}
          disabled={!connected}
          title="Stop Task"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" />
          </svg>
          Stop
        </button>
      </div>

      <div className="control-status">
        <div className="status-pulse"></div>
        <span>{isPaused ? 'Paused' : 'Running'}</span>
      </div>
    </div>
  )
}

export const ControlButtons = React.memo(ControlButtonsComponent)
