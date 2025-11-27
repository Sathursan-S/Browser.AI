# Frontend Integration Guide - Structured Events

This guide shows how to integrate the structured event system into the Browser.AI extension frontend.

## Overview

The new structured event system provides rich, type-safe events that replace log parsing with proper event handling.

## TypeScript Definitions

Import the structured event types:

```typescript
import { 
  StructuredEvent,
  AgentProgressEvent,
  AgentCompleteEvent,
  AgentErrorEvent,
  isAgentProgressEvent,
  isAgentCompleteEvent,
  isAgentErrorEvent,
  getEventIcon,
  getSeverityColor
} from '@/types/structured-events'
```

## WebSocket Event Handling

### Basic Setup

```typescript
import { io } from 'socket.io-client'
import { StructuredEvent } from '@/types/structured-events'

// Connect to server
const socket = io('http://localhost:5000/extension')

// Subscribe to structured events
socket.on('structured_event', (event: StructuredEvent) => {
  handleStructuredEvent(event)
})
```

### Event Handlers

```typescript
function handleStructuredEvent(event: StructuredEvent) {
  // Log for debugging
  console.log(`Event: ${event.event_type}`, event)
  
  // Handle specific event types
  if (isAgentProgressEvent(event)) {
    updateProgressUI(event)
  } else if (isAgentCompleteEvent(event)) {
    handleTaskCompletion(event)
  } else if (isAgentErrorEvent(event)) {
    handleError(event)
  }
}
```

## UI Components

### Progress Display

```typescript
function updateProgressUI(event: AgentProgressEvent) {
  // Update progress bar
  const progressBar = document.getElementById('progress-bar')
  if (progressBar) {
    progressBar.style.width = `${event.progress_percentage}%`
    progressBar.setAttribute('aria-valuenow', event.progress_percentage.toString())
  }
  
  // Update status message
  const statusText = document.getElementById('status-text')
  if (statusText && event.status_message) {
    statusText.textContent = event.status_message
  }
  
  // Update step counter
  const stepCounter = document.getElementById('step-counter')
  if (stepCounter && event.total_steps) {
    stepCounter.textContent = `Step ${event.current_step} of ${event.total_steps}`
  }
}
```

### Task Completion

```typescript
function handleTaskCompletion(event: AgentCompleteEvent) {
  if (event.success) {
    // Show success notification
    showNotification({
      type: 'success',
      title: 'Task Completed',
      message: event.result || 'Task completed successfully',
      duration: 5000
    })
    
    // Update UI
    updateTaskStatus('completed')
    
    // Show execution stats
    if (event.execution_time_ms && event.steps_executed) {
      const stats = `Completed in ${(event.execution_time_ms / 1000).toFixed(1)}s (${event.steps_executed} steps)`
      displayStats(stats)
    }
  } else {
    // Show warning
    showNotification({
      type: 'warning',
      title: 'Task Incomplete',
      message: 'Task ended without full completion',
      duration: 5000
    })
  }
}
```

### Error Handling

```typescript
function handleError(event: AgentErrorEvent) {
  // Show error notification
  showNotification({
    type: 'error',
    title: event.error_type,
    message: event.error_message,
    duration: 0 // Don't auto-dismiss errors
  })
  
  // Log details for debugging
  if (event.error_details) {
    console.error('Error details:', event.error_details)
  }
  
  // If recoverable, show retry option
  if (event.recoverable) {
    showRetryButton()
  }
}
```

## React Integration

### Custom Hook

```typescript
import { useEffect, useState } from 'react'
import { StructuredEvent } from '@/types/structured-events'

export function useStructuredEvents(socket: any) {
  const [events, setEvents] = useState<StructuredEvent[]>([])
  
  useEffect(() => {
    if (!socket) return
    
    const handleEvent = (event: StructuredEvent) => {
      setEvents(prev => [...prev, event])
    }
    
    socket.on('structured_event', handleEvent)
    
    return () => {
      socket.off('structured_event', handleEvent)
    }
  }, [socket])
  
  return events
}
```

### Progress Component

```typescript
import React from 'react'
import { AgentProgressEvent } from '@/types/structured-events'

interface ProgressProps {
  event: AgentProgressEvent | null
}

export function Progress({ event }: ProgressProps) {
  if (!event) return null
  
  return (
    <div className="progress-container">
      <div className="progress-bar-wrapper">
        <div 
          className="progress-bar" 
          style={{ width: `${event.progress_percentage}%` }}
        />
      </div>
      <div className="progress-info">
        <span className="progress-percentage">
          {event.progress_percentage.toFixed(1)}%
        </span>
        {event.status_message && (
          <span className="progress-message">
            {event.status_message}
          </span>
        )}
        {event.total_steps && (
          <span className="progress-steps">
            Step {event.current_step} / {event.total_steps}
          </span>
        )}
      </div>
    </div>
  )
}
```

### Event Feed Component

```typescript
import React from 'react'
import { StructuredEvent, getEventIcon, getSeverityColor } from '@/types/structured-events'

interface EventFeedProps {
  events: StructuredEvent[]
}

export function EventFeed({ events }: EventFeedProps) {
  return (
    <div className="event-feed">
      {events.map(event => (
        <div 
          key={event.event_id} 
          className="event-item"
          style={{ borderLeftColor: getSeverityColor(event.severity) }}
        >
          <span className="event-icon">{getEventIcon(event)}</span>
          <div className="event-content">
            <div className="event-type">{event.event_type}</div>
            <div className="event-time">
              {new Date(event.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
```

## Event Filtering

### Filter by Category

```typescript
import { EventCategory, filterByCategory } from '@/types/structured-events'

// Get only agent events
const agentEvents = filterByCategory(allEvents, EventCategory.AGENT)

// Get only progress events
const progressEvents = filterByCategory(allEvents, EventCategory.PROGRESS)
```

### Filter by Agent ID

```typescript
import { filterByAgentId } from '@/types/structured-events'

// Get events for specific agent
const myAgentEvents = filterByAgentId(allEvents, currentAgentId)
```

### Filter by Severity

```typescript
import { EventSeverity, filterBySeverity } from '@/types/structured-events'

// Get only errors
const errors = filterBySeverity(allEvents, EventSeverity.ERROR)

// Get warnings and errors
const issues = allEvents.filter(e => 
  e.severity === EventSeverity.WARNING || 
  e.severity === EventSeverity.ERROR
)
```

## State Management

### Redux/Zustand Integration

```typescript
// Zustand store example
import create from 'zustand'
import { StructuredEvent, AgentProgressEvent } from '@/types/structured-events'

interface EventStore {
  events: StructuredEvent[]
  currentProgress: AgentProgressEvent | null
  addEvent: (event: StructuredEvent) => void
  clearEvents: () => void
}

export const useEventStore = create<EventStore>((set) => ({
  events: [],
  currentProgress: null,
  
  addEvent: (event) => set((state) => {
    const newEvents = [...state.events, event]
    
    // Update current progress if it's a progress event
    const currentProgress = event.event_type === 'agent.progress' 
      ? event as AgentProgressEvent
      : state.currentProgress
    
    return { events: newEvents, currentProgress }
  }),
  
  clearEvents: () => set({ events: [], currentProgress: null })
}))
```

## Best Practices

### 1. Type Guards

Always use type guards to safely access event-specific fields:

```typescript
// ❌ Bad - might cause runtime errors
const progress = event.progress_percentage

// ✅ Good - type-safe
if (isAgentProgressEvent(event)) {
  const progress = event.progress_percentage
}
```

### 2. Event Batching

Batch UI updates to avoid performance issues:

```typescript
const [eventBatch, setEventBatch] = useState<StructuredEvent[]>([])

useEffect(() => {
  const timer = setInterval(() => {
    if (eventBatch.length > 0) {
      processEvents(eventBatch)
      setEventBatch([])
    }
  }, 100) // Process every 100ms
  
  return () => clearInterval(timer)
}, [eventBatch])
```

### 3. Event Cleanup

Limit stored events to prevent memory issues:

```typescript
const MAX_EVENTS = 1000

function addEvent(event: StructuredEvent) {
  setEvents(prev => {
    const newEvents = [...prev, event]
    // Keep only last MAX_EVENTS
    return newEvents.slice(-MAX_EVENTS)
  })
}
```

### 4. Error Boundaries

Wrap event handlers in error boundaries:

```typescript
function safeHandleEvent(event: StructuredEvent) {
  try {
    handleStructuredEvent(event)
  } catch (error) {
    console.error('Error handling event:', error, event)
    // Fallback UI or notification
  }
}
```

## Migration from Log Events

### Before (Log Parsing)

```typescript
socket.on('log_event', (log) => {
  if (log.message.includes('Step')) {
    // Parse step number from message
    const match = log.message.match(/Step (\d+)/)
    if (match) {
      updateStep(parseInt(match[1]))
    }
  }
})
```

### After (Structured Events)

```typescript
socket.on('structured_event', (event) => {
  if (isAgentStepEvent(event)) {
    updateStep(event.step_number)
  }
})
```

## Complete Example

```typescript
import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'
import {
  StructuredEvent,
  AgentProgressEvent,
  isAgentStartEvent,
  isAgentProgressEvent,
  isAgentCompleteEvent,
  isAgentErrorEvent,
  getEventIcon
} from '@/types/structured-events'

export function TaskMonitor() {
  const [socket, setSocket] = useState(null)
  const [events, setEvents] = useState<StructuredEvent[]>([])
  const [progress, setProgress] = useState<AgentProgressEvent | null>(null)
  const [status, setStatus] = useState<'idle' | 'running' | 'complete' | 'error'>('idle')
  
  useEffect(() => {
    const socket = io('http://localhost:5000/extension')
    
    socket.on('structured_event', (event: StructuredEvent) => {
      // Add to event list
      setEvents(prev => [...prev, event])
      
      // Update status based on event type
      if (isAgentStartEvent(event)) {
        setStatus('running')
      } else if (isAgentProgressEvent(event)) {
        setProgress(event)
      } else if (isAgentCompleteEvent(event)) {
        setStatus(event.success ? 'complete' : 'error')
      } else if (isAgentErrorEvent(event)) {
        setStatus('error')
      }
    })
    
    setSocket(socket)
    
    return () => {
      socket.close()
    }
  }, [])
  
  return (
    <div className="task-monitor">
      <div className="status-bar">
        Status: {status}
      </div>
      
      {progress && (
        <div className="progress">
          <div className="progress-bar" style={{ width: `${progress.progress_percentage}%` }} />
          <div className="progress-text">
            {progress.status_message || `${progress.progress_percentage.toFixed(0)}%`}
          </div>
        </div>
      )}
      
      <div className="events">
        {events.map(event => (
          <div key={event.event_id} className="event">
            <span className="icon">{getEventIcon(event)}</span>
            <span className="type">{event.event_type}</span>
            <span className="time">{new Date(event.timestamp).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

## Testing

```typescript
import { describe, it, expect } from 'vitest'
import { isAgentProgressEvent, AgentProgressEvent, EventCategory, EventSeverity } from '@/types/structured-events'

describe('Structured Events', () => {
  it('should identify progress events', () => {
    const event: AgentProgressEvent = {
      event_id: 'test-123',
      event_type: 'agent.progress',
      category: EventCategory.PROGRESS,
      timestamp: new Date().toISOString(),
      severity: EventSeverity.INFO,
      agent_id: 'agent-1',
      progress_percentage: 50,
      current_step: 5,
      total_steps: 10
    }
    
    expect(isAgentProgressEvent(event)).toBe(true)
  })
})
```

## Resources

- [Structured Events Documentation](../docs/STRUCTURED_EVENTS.md)
- [Python Event Schemas](../browser_ai_gui/events/schemas.py)
- [Demo](../structured_events_demo.py)
