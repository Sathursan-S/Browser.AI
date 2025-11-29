import React from 'react'
import { Button } from '../../ui/Button'

export interface ControlButtonsProps {
  isRunning: boolean
  isPaused: boolean
  connected: boolean
  onStart?: () => void
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
  onClearChat?: () => void
}

const ControlButtonsComponent: React.FC<ControlButtonsProps> = ({
  isRunning,
  isPaused,
  connected,
  onStart,
  onPause,
  onResume,
  onStop,
  onClearChat,
}: ControlButtonsProps) => {
  // Only show control buttons when a task is actually running
  if (!isRunning) {
    return (
      <div className="flex items-center justify-between p-3 bg-white/5 border border-white/10 rounded-xl mb-4 animate-in slide-in-from-top-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-400 animate-pulse"></div>
          <span className="text-sm font-medium text-white/80">Idle</span>
        </div>
        <div className="flex gap-2">
          {onStart && (
            <Button
              onClick={onStart}
              disabled={!connected}
              title="Start Task"
              size="sm"
              className="gap-2"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
                <polygon points="10,8 16,12 10,16" fill="currentColor" />
              </svg>
              Start
            </Button>
          )}
          {onClearChat && (
            <Button
              onClick={onClearChat}
              variant="outline"
              size="sm"
              title="Clear Chat"
              className="gap-2"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m7 7 10 10M7 17 17 7" />
              </svg>
              Clear
            </Button>
          )}

        </div>
        {!onStart && (
          <div className="px-3 py-2 text-xs text-white/60 bg-white/5 rounded-md" title="No start action available">
            Waiting for task...
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between p-3 bg-white/5 border border-white/10 rounded-xl mb-4 animate-in slide-in-from-top-2">
      <div className="flex gap-2">
        {isPaused ? (
          <Button
            variant="default"
            size="sm"
            onClick={onResume}
            disabled={!connected}
            title="Resume Task"
            className="gap-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M8 5V19L19 12L8 5Z" fill="currentColor" />
            </svg>
            Resume
          </Button>
        ) : (
          <Button
            variant="default"
            size="sm"
            onClick={onPause}
            disabled={!connected}
            title="Pause Task"
            className="gap-2 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect x="6" y="4" width="4" height="16" fill="currentColor" />
              <rect x="14" y="4" width="4" height="16" fill="currentColor" />
            </svg>
            Pause
          </Button>
        )}

        <Button
          variant="destructive"
          size="sm"
          onClick={onStop}
          disabled={!connected}
          title="Stop Task"
          className="gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" />
          </svg>
          Stop
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse shadow-lg shadow-green-400/40"></div>
        <span className="text-sm font-medium text-white/90">{isPaused ? 'Paused' : 'Running'}</span>
      </div>
    </div>
  )
}

export const ControlButtons = React.memo(ControlButtonsComponent)
