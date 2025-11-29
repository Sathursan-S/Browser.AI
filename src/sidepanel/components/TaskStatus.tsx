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
    <div className={`flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-xl mb-4 relative overflow-hidden animate-in slide-in-from-top-2 ${isPaused ? 'bg-yellow-500/10 border-yellow-500/20' : ''}`}>
      {/* Animated top border */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${isPaused ? 'from-yellow-400 to-yellow-500' : 'from-blue-500 via-purple-600 to-blue-500'} ${!isPaused ? 'animate-pulse bg-size-200 animate-shimmer' : ''}`}></div>
      
      <div className="flex items-center justify-center w-10 h-10 bg-white/10 rounded-full backdrop-blur-sm">
        <div className={`w-6 h-6 border-2 border-white/20 rounded-full ${!isPaused ? 'border-t-blue-500 animate-spin' : 'border-t-yellow-500'}`}></div>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${isPaused ? 'text-yellow-400' : 'text-blue-400'}`}>
          {isPaused ? '⏸️ Paused' : '🚀 Running'}
        </div>
        <div className="text-sm text-white/90 font-medium line-clamp-2 leading-relaxed">
          {currentTask}
        </div>
      </div>
    </div>
  )
}
