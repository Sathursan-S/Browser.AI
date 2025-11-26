import React, { useEffect, useState } from 'react'
import { StepItem, StepData } from './StepItem'
import { LogEvent } from '../ExecutionLog'

interface StepListProps {
  logs: LogEvent[]
  isRunning: boolean
}

export const StepList: React.FC<StepListProps> = ({ logs, isRunning }) => {
  const [steps, setSteps] = useState<StepData[]>([])

  useEffect(() => {
    const newSteps: StepData[] = []
    let currentStep: StepData | null = null

    const commitStep = () => {
      if (currentStep) {
        newSteps.push(currentStep)
        currentStep = null
      }
    }

    logs.forEach((log) => {
      if (log.event_type === 'agent_step') {
        commitStep()
        const title = log.message.replace(/Step \d+:/i, '').trim() || log.message
        currentStep = {
          id: `step-${log.timestamp}`,
          title: title,
          status: 'running',
          logs: [],
          timestamp: new Date(log.timestamp).getTime()
        }
      }
      else if (currentStep) {
        if (log.level === 'ERROR' || log.event_type === 'agent_error') {
          currentStep.status = 'failed'
          currentStep.logs.push(`❌ ${log.message}`)
        }
        else if (['agent_action', 'agent_result'].includes(log.event_type)) {
           currentStep.logs.push(log.message)
        }
        else if (log.level === 'INFO' && !log.message.includes('Step')) {
           currentStep.logs.push(log.message)
        }
      } else {
        if (!newSteps.find(s => s.id === 'init')) {
           newSteps.push({
             id: 'init',
             title: 'Initializing Task',
             status: 'completed',
             logs: [log.message],
             timestamp: 0
           })
        } else {
           newSteps[0].logs.push(log.message)
        }
      }
    })

    commitStep()

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
