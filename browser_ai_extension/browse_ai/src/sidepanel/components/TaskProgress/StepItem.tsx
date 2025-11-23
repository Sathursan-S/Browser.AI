import React, { useState } from 'react'

export interface StepData {
  id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  logs: string[]
  timestamp: number
}

interface StepItemProps {
  step: StepData
  isLast: boolean
}

export const StepItem: React.FC<StepItemProps> = ({ step, isLast }) => {
  // Auto-expand if running or failed, otherwise collapsed by default
  const [isExpanded, setIsExpanded] = useState(
    step.status === 'running' || step.status === 'failed'
  )

  // Update expansion state if status changes to running
  React.useEffect(() => {
    if (step.status === 'running') {
      setIsExpanded(true)
    }
  }, [step.status])

  const getStatusIcon = () => {
    switch (step.status) {
      case 'running':
        return (
          <div className="w-5 h-5 flex items-center justify-center">
             <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )
      case 'completed':
        return (
          <div className="w-5 h-5 flex items-center justify-center text-green-500">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        )
      case 'failed':
        return (
          <div className="w-5 h-5 flex items-center justify-center text-red-500">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        )
      default: // pending
        return (
          <div className="w-5 h-5 flex items-center justify-center">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-600" />
          </div>
        )
    }
  }

  return (
    <div className="relative pl-8 pb-4">
      {/* Connector Line */}
      {!isLast && (
        <div
          className={`absolute left-[10px] top-7 bottom-0 w-[2px]
            ${step.status === 'completed' ? 'bg-green-200 dark:bg-green-900' : 'bg-slate-200 dark:bg-slate-700'}
          `}
        />
      )}

      {/* Status Icon */}
      <div className={`absolute left-0 top-1 w-6 h-6 rounded-full bg-white dark:bg-slate-900 border
        ${step.status === 'running' ? 'border-primary shadow-sm shadow-primary/20' :
          step.status === 'completed' ? 'border-green-500/20 bg-green-50 dark:bg-green-900/10' :
          step.status === 'failed' ? 'border-red-500/20 bg-red-50 dark:bg-red-900/10' :
          'border-slate-200 dark:border-slate-700'}
        flex items-center justify-center z-10 transition-colors duration-200
      `}>
        {getStatusIcon()}
      </div>

      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h4 className={`text-sm font-medium transition-colors duration-200
          ${step.status === 'running' ? 'text-primary' :
            step.status === 'completed' ? 'text-slate-700 dark:text-slate-200' :
            step.status === 'failed' ? 'text-red-600 dark:text-red-400' :
            'text-slate-500 dark:text-slate-400'}
        `}>
          {step.title}
        </h4>
        <button className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-transform duration-200" style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* Details (Logs) */}
      <div
        className={`grid transition-all duration-300 ease-in-out ${isExpanded ? 'grid-rows-[1fr] opacity-100 mt-2' : 'grid-rows-[0fr] opacity-0'}`}
      >
        <div className="overflow-hidden">
          <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-800 p-2 font-mono text-xs space-y-1">
            {step.logs.length === 0 ? (
              <div className="text-slate-400 italic px-1">Waiting for details...</div>
            ) : (
              step.logs.map((log, idx) => (
                <div key={idx} className="text-slate-600 dark:text-slate-400 break-words leading-relaxed pl-1 border-l-2 border-slate-200 dark:border-slate-700">
                  {log}
                </div>
              ))
            )}
            {step.status === 'running' && (
              <div className="animate-pulse flex gap-1 px-1">
                <div className="w-1 h-1 bg-primary/50 rounded-full" />
                <div className="w-1 h-1 bg-primary/50 rounded-full animation-delay-150" />
                <div className="w-1 h-1 bg-primary/50 rounded-full animation-delay-300" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
