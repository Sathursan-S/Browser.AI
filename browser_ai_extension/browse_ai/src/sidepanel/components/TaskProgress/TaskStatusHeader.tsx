import React, { useState, useEffect } from 'react'

interface TaskStatusHeaderProps {
  task: string
  status: 'running' | 'completed' | 'failed' | 'paused'
  result?: string
  onClose?: () => void
}

export const TaskStatusHeader: React.FC<TaskStatusHeaderProps> = ({ task, status, result, onClose }) => {
  const [expanded, setExpanded] = useState(false)

  // Auto-expand on completion
  useEffect(() => {
    if (status === 'completed') {
      setExpanded(true)
    }
  }, [status])

  return (
    <div
      className={`
        sticky top-0 z-30 transition-all duration-300 ease-in-out shadow-sm
        ${expanded
          ? 'bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800'
          : 'bg-white/95 dark:bg-slate-950/95 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800'}
      `}
    >
      <div className="p-4">
        <div className="flex gap-3 items-start">
          {/* Status Indicator */}
          <div className="mt-1.5 relative shrink-0">
             {status === 'running' && (
               <>
                 <div className="absolute inset-0 bg-blue-500 blur-sm opacity-20 animate-pulse rounded-full" />
                 <div className="relative w-2.5 h-2.5 rounded-full bg-blue-500" />
               </>
             )}
             {status === 'completed' && <div className="w-2.5 h-2.5 rounded-full bg-green-500 shadow-sm shadow-green-500/50" />}
             {status === 'failed' && <div className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-sm shadow-red-500/50" />}
             {status === 'paused' && <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start gap-2">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-0.5">
                  {status === 'running' ? 'Current Task' : 'Task Finished'}
                </h3>
                <p className={`text-sm font-medium text-slate-900 dark:text-slate-100 break-words leading-snug ${expanded ? '' : 'line-clamp-2'}`}>
                  {task}
                </p>
              </div>

              {/* Expand/Collapse Toggle */}
              {(status === 'completed' || status === 'failed') && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <svg
                    width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                    className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
                  >
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              )}
            </div>

            {/* Expanded Result View */}
            <div
              className={`
                grid transition-all duration-300 ease-in-out
                ${expanded ? 'grid-rows-[1fr] opacity-100 mt-3' : 'grid-rows-[0fr] opacity-0'}
              `}
            >
              <div className="overflow-hidden">
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wide">
                    Result
                  </h4>
                  <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono max-h-[200px] overflow-y-auto custom-scrollbar">
                    {result || "Task completed successfully."}
                  </div>
                  <div className="flex justify-end mt-3 gap-2">
                     <button
                       onClick={() => { navigator.clipboard.writeText(result || '') }}
                       className="text-xs px-2 py-1 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600"
                     >
                       Copy Result
                     </button>
                     {onClose && (
                       <button
                         onClick={onClose}
                         className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600"
                       >
                         Dismiss
                       </button>
                     )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
