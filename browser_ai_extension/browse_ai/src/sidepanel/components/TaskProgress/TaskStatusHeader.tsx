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
          {/* Animated Bot Head / Status Icon */}
          <div className="mt-1 relative shrink-0 w-8 h-8 flex items-center justify-center">
             {status === 'running' ? (
               <div className="relative w-full h-full">
                 {/* Copilot-style ring animation */}
                 <div className="absolute inset-0 border-2 border-blue-500 rounded-full animate-[spin_3s_linear_infinite]" style={{ borderTopColor: 'transparent', borderRightColor: 'transparent' }} />
                 <div className="absolute inset-1 border-2 border-purple-500 rounded-full animate-[spin_2s_linear_infinite_reverse]" style={{ borderBottomColor: 'transparent', borderLeftColor: 'transparent' }} />

                 {/* Central Bot Face */}
                 <div className="absolute inset-2 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                      <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
                      <rect x="4" y="8" width="16" height="12" rx="2" />
                      <path d="M9 14h.01M15 14h.01" strokeLinecap="round" />
                    </svg>
                 </div>
               </div>
             ) : status === 'completed' ? (
               <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center shadow-lg shadow-green-500/30 animate-[fadeIn_0.3s_ease-out]">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                   <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                 </svg>
               </div>
             ) : status === 'failed' ? (
               <div className="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center shadow-lg shadow-red-500/30">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                   <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
                 </svg>
               </div>
             ) : (
               <div className="w-8 h-8 rounded-full bg-yellow-500 text-white flex items-center justify-center">
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                   <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.77a2 2 0 0 0-1.94 1.51l-1.1 6a2 2 0 0 0 .2 1.49l1.2 2.12" />
                 </svg>
               </div>
             )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start gap-2">
              <div onClick={() => setExpanded(!expanded)} className="cursor-pointer">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-0.5">
                  {status === 'running' ? 'AI Agent Working...' : status === 'completed' ? 'Task Completed' : 'Task Failed'}
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
                         className="text-xs px-2 py-1 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded hover:bg-red-100 dark:hover:bg-red-900/30"
                       >
                         Dismiss & Clear
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
