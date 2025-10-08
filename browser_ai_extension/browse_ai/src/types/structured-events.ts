/**
 * Structured Event System - TypeScript Definitions
 * 
 * Type definitions for the new structured event system.
 * These match the Python event schemas in browser_ai_gui/events/schemas.py
 */

// ============================================================================
// Enums
// ============================================================================

export enum EventCategory {
  AGENT = 'agent',
  TASK = 'task',
  LLM = 'llm',
  BROWSER = 'browser',
  PROGRESS = 'progress',
  SYSTEM = 'system',
}

export enum EventSeverity {
  DEBUG = 'debug',
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

// ============================================================================
// Base Event
// ============================================================================

export interface BaseEvent {
  event_id: string
  event_type: string
  category: EventCategory
  timestamp: string // ISO 8601 format
  severity: EventSeverity
  session_id?: string
  task_id?: string
  metadata?: Record<string, any>
}

// ============================================================================
// Agent Events
// ============================================================================

export interface AgentStartEvent extends BaseEvent {
  event_type: 'agent.start'
  category: EventCategory.AGENT
  task_description: string
  agent_id: string
  configuration: Record<string, any>
}

export interface AgentStepEvent extends BaseEvent {
  event_type: 'agent.step'
  category: EventCategory.AGENT
  step_number: number
  step_description: string
  agent_id: string
  total_steps?: number
}

export interface AgentActionEvent extends BaseEvent {
  event_type: 'agent.action'
  category: EventCategory.AGENT
  action_type: string
  action_description: string
  agent_id: string
  action_parameters: Record<string, any>
  action_result?: string
}

export interface AgentProgressEvent extends BaseEvent {
  event_type: 'agent.progress'
  category: EventCategory.PROGRESS
  agent_id: string
  progress_percentage: number // 0.0 to 100.0
  current_step: number
  total_steps?: number
  status_message?: string
}

export interface AgentStateEvent extends BaseEvent {
  event_type: 'agent.state_change'
  category: EventCategory.AGENT
  agent_id: string
  old_state: string
  new_state: string
  state_data: Record<string, any>
}

export interface AgentCompleteEvent extends BaseEvent {
  event_type: 'agent.complete'
  category: EventCategory.AGENT
  agent_id: string
  success: boolean
  result?: string
  execution_time_ms?: number
  steps_executed?: number
}

export interface AgentErrorEvent extends BaseEvent {
  event_type: 'agent.error'
  category: EventCategory.AGENT
  severity: EventSeverity.ERROR
  agent_id: string
  error_type: string
  error_message: string
  error_details?: string
  recoverable: boolean
}

// ============================================================================
// LLM Events
// ============================================================================

export interface LLMOutputEvent extends BaseEvent {
  event_type: 'llm.output'
  category: EventCategory.LLM
  agent_id: string
  llm_provider: string
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
  model_name?: string
  response_preview?: string // First 200 chars
  latency_ms?: number
}

// ============================================================================
// Task Events
// ============================================================================

export interface TaskStateChangeEvent extends BaseEvent {
  event_type: 'task.state_change'
  category: EventCategory.TASK
  task_description: string
  old_state: string
  new_state: string
  agent_id?: string
}

// ============================================================================
// Union Type for All Events
// ============================================================================

export type StructuredEvent =
  | AgentStartEvent
  | AgentStepEvent
  | AgentActionEvent
  | AgentProgressEvent
  | AgentStateEvent
  | AgentCompleteEvent
  | AgentErrorEvent
  | LLMOutputEvent
  | TaskStateChangeEvent

// ============================================================================
// Event Handlers
// ============================================================================

export type EventHandler<T extends StructuredEvent = StructuredEvent> = (event: T) => void

export interface EventSubscription {
  id: string
  handler: EventHandler
  filter?: string // Event type filter
  categoryFilter?: EventCategory // Category filter
}

// ============================================================================
// Type Guards
// ============================================================================

export function isStructuredEvent(obj: any): obj is StructuredEvent {
  return (
    obj &&
    typeof obj.event_id === 'string' &&
    typeof obj.event_type === 'string' &&
    typeof obj.category === 'string' &&
    typeof obj.timestamp === 'string' &&
    typeof obj.severity === 'string'
  )
}

export function isAgentStartEvent(event: StructuredEvent): event is AgentStartEvent {
  return event.event_type === 'agent.start'
}

export function isAgentStepEvent(event: StructuredEvent): event is AgentStepEvent {
  return event.event_type === 'agent.step'
}

export function isAgentActionEvent(event: StructuredEvent): event is AgentActionEvent {
  return event.event_type === 'agent.action'
}

export function isAgentProgressEvent(event: StructuredEvent): event is AgentProgressEvent {
  return event.event_type === 'agent.progress'
}

export function isAgentCompleteEvent(event: StructuredEvent): event is AgentCompleteEvent {
  return event.event_type === 'agent.complete'
}

export function isAgentErrorEvent(event: StructuredEvent): event is AgentErrorEvent {
  return event.event_type === 'agent.error'
}

export function isLLMOutputEvent(event: StructuredEvent): event is LLMOutputEvent {
  return event.event_type === 'llm.output'
}

export function isTaskStateChangeEvent(event: StructuredEvent): event is TaskStateChangeEvent {
  return event.event_type === 'task.state_change'
}

// ============================================================================
// Event Filtering Helpers
// ============================================================================

export function filterByCategory(events: StructuredEvent[], category: EventCategory): StructuredEvent[] {
  return events.filter(event => event.category === category)
}

export function filterByType(events: StructuredEvent[], eventType: string): StructuredEvent[] {
  return events.filter(event => event.event_type === eventType)
}

export function filterBySeverity(events: StructuredEvent[], severity: EventSeverity): StructuredEvent[] {
  return events.filter(event => event.severity === severity)
}

export function filterByAgentId(events: StructuredEvent[], agentId: string): StructuredEvent[] {
  return events.filter(event => {
    return 'agent_id' in event && event.agent_id === agentId
  })
}

// ============================================================================
// Event Formatting Helpers
// ============================================================================

export function formatEventTimestamp(event: StructuredEvent): string {
  return new Date(event.timestamp).toLocaleString()
}

export function getEventIcon(event: StructuredEvent): string {
  if (isAgentStartEvent(event)) return '🚀'
  if (isAgentStepEvent(event)) return '📍'
  if (isAgentActionEvent(event)) return '🔧'
  if (isAgentProgressEvent(event)) return '📊'
  if (isAgentCompleteEvent(event)) return event.success ? '✅' : '⚠️'
  if (isAgentErrorEvent(event)) return '❌'
  if (isLLMOutputEvent(event)) return '🤖'
  if (isTaskStateChangeEvent(event)) return '🔄'
  return '📡'
}

export function getSeverityColor(severity: EventSeverity): string {
  switch (severity) {
    case EventSeverity.DEBUG:
      return '#888888'
    case EventSeverity.INFO:
      return '#0066cc'
    case EventSeverity.WARNING:
      return '#ff9900'
    case EventSeverity.ERROR:
      return '#cc0000'
    case EventSeverity.CRITICAL:
      return '#990000'
    default:
      return '#000000'
  }
}

// ============================================================================
// Example Usage
// ============================================================================

/*
// Subscribe to structured events
socket.on('structured_event', (event: StructuredEvent) => {
  console.log(`Event: ${event.event_type}`)
  
  if (isAgentProgressEvent(event)) {
    updateProgressBar(event.progress_percentage)
  }
  
  if (isAgentCompleteEvent(event)) {
    if (event.success) {
      showNotification('Task completed successfully!')
    }
  }
  
  if (isAgentErrorEvent(event)) {
    console.error(`Error: ${event.error_message}`)
  }
})

// Filter events by category
const agentEvents = filterByCategory(allEvents, EventCategory.AGENT)

// Filter events by agent ID
const myAgentEvents = filterByAgentId(allEvents, 'agent-123')

// Display with icons
events.forEach(event => {
  console.log(`${getEventIcon(event)} ${event.event_type}`)
})
*/
