import './ControlButtons.css'

interface ControlButtonsProps {
  isRunning: boolean
  isPaused: boolean
  connected: boolean
  onStart?: () => void
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
}

export const ControlButtons = ({
  isRunning,
  isPaused,
  connected,
  onStart,
  onPause,
  onResume,
  onStop,
}: ControlButtonsProps) => {
  if (!isRunning) {
    return null
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
