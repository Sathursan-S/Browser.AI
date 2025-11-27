import React, { useEffect, useState, useRef } from 'react'
import { StepItem, StepData } from './StepItem'
import { LogEvent } from '../ExecutionLog'

interface StepListProps {
  logs: LogEvent[]
  isRunning: boolean
}

export const StepList: React.FC<StepListProps> = ({ logs, isRunning }) => {
  const [steps, setSteps] = useState<StepData[]>([])

  // Logic to transform flat logs into hierarchical steps
  useEffect(() => {
    const newSteps: StepData[] = []
    let currentStep: StepData | null = null

    // Helper to commit current step
    const commitStep = () => {
      if (currentStep) {
        newSteps.push(currentStep)
        currentStep = null
      }
    }

    // Process all logs sequentially
    logs.forEach((log) => {
      // 1. Detect New Step Start
      if (log.event_type === 'agent_step') {
        commitStep()

        // Extract step number/title if possible
        const title = log.message.replace(/Step \d+:/i, '').trim() || log.message

        currentStep = {
          id: `step-${log.timestamp}`,
          title: title,
          status: 'running',
          logs: [],
          timestamp: new Date(log.timestamp).getTime()
        }
      }
      // 2. Handle Step Completion/Failure
      else if (currentStep) {
        // Check for error in current step
        if (log.level === 'ERROR' || log.event_type === 'agent_error') {
          currentStep.status = 'failed'
          currentStep.logs.push(`❌ ${log.message}`)
        }
        // Check for specific action logs to add as details
        else if (['agent_action', 'agent_result'].includes(log.event_type)) {
           currentStep.logs.push(log.message)
        }
        // General info logs inside a step
        else if (log.level === 'INFO' && !log.message.includes('Step')) {
           currentStep.logs.push(log.message)
        }

        // If we see a "success" marker, mark completed (heuristic)
        // Note: The next 'agent_step' will also auto-complete the previous one effectively in UI logic
        // but explicit completion is better.
      } else {
        // Logs before any step starts (Initialization)
        if (!newSteps.find(s => s.id === 'init')) {
           newSteps.push({
             id: 'init',
             title: 'Initializing Task',
             status: 'completed', // Assume completed if we moved past it
             logs: [log.message],
             timestamp: 0
           })
        } else {
           newSteps[0].logs.push(log.message)
        }
      }
    })

    // Commit final open step
    commitStep()

    // Post-processing:
    // If task is stopped/failed globally, mark last step failed?
    // If we have a new step, the previous one is likely 'completed' unless marked 'failed'.
    for (let i = 0; i < newSteps.length - 1; i++) {
       if (newSteps[i].status === 'running') {
         newSteps[i].status = 'completed'
       }
    }

    setSteps(newSteps)

  }, [logs, isRunning])

  return (
    <div className="py-4 px-2">
      {steps.length === 0 && isRunning && (
        <div className="text-center text-slate-500 py-4 animate-pulse">
          Starting agent...
        </div>
      )}

      {steps.map((step, index) => (
        <StepItem
          key={step.id}
          step={step}
          isLast={index === steps.length - 1}
        />
      ))}
    </div>
  )
}
