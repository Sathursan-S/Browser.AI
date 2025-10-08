/**
 * Browser.AI WebSocket Protocol
 *
 * Shared protocol definitions for communication between the Chrome extension
 * and the Browser.AI server over WebSocket connections.
 *
 * Namespace: /extension
 */

// ============================================================================
// Enums
// ============================================================================

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  RESULT = 'RESULT',
}

export enum EventType {
  LOG = 'log',
  AGENT_START = 'agent_start',
  AGENT_STEP = 'agent_step',
  AGENT_ACTION = 'agent_action',
  AGENT_RESULT = 'agent_result',
  AGENT_COMPLETE = 'agent_complete',
  AGENT_ERROR = 'agent_error',
  AGENT_PAUSE = 'agent_pause',
  AGENT_RESUME = 'agent_resume',
  AGENT_STOP = 'agent_stop',
  USER_HELP_NEEDED = 'user_help_needed',
}

// ============================================================================
// Settings & Configuration
// ============================================================================

/**
 * Extension settings stored in Chrome storage
 */
export interface ExtensionSettings {
  serverUrl: string
  devMode: boolean
  autoReconnect: boolean
  maxLogs: number
  showNotifications: boolean
}

export const DEFAULT_SETTINGS: ExtensionSettings = {
  serverUrl: 'http://localhost:5000',
  devMode: false,
  autoReconnect: true,
  maxLogs: 1000,
  showNotifications: true,
}

// ============================================================================
// Data Structures
// ============================================================================

/**
 * Log event broadcast from server to clients
 */
export interface LogEvent {
  timestamp: string // ISO 8601 format
  level: LogLevel | string
  logger_name: string
  message: string
  event_type: EventType | string
  metadata?: Record<string, any>
}

/**
 * Task status information
 */
export interface TaskStatus {
  is_running: boolean
  current_task: string | null
  has_agent: boolean
  is_paused?: boolean
  cdp_endpoint?: string
}

/**
 * Generic action result
 */
export interface ActionResult {
  success: boolean
  message?: string
  error?: string
}

// ============================================================================
// Client -> Server Events (Emitted by Extension)
// ============================================================================

/**
 * Event: extension_connect
 * Sent when extension client connects to establish session
 * Payload: none
 */
export type ExtensionConnectEvent = void

/**
 * Event: start_task
 * Request to start a new Browser.AI task
 */
export interface StartTaskPayload {
  task: string // Task description
  cdp_endpoint?: string // Optional CDP WebSocket endpoint
  is_extension?: boolean // Flag to indicate extension mode
}

/**
 * Event: stop_task
 * Request to stop the currently running task
 * Payload: none
 */
export type StopTaskEvent = void

/**
 * Event: pause_task
 * Request to pause the currently running task
 * Payload: none
 */
export type PauseTaskEvent = void

/**
 * Event: resume_task
 * Request to resume a paused task
 * Payload: none
 */
export type ResumeTaskEvent = void

/**
 * Event: get_status
 * Request current task status
 * Payload: none
 */
export type GetStatusEvent = void

// ============================================================================
// Server -> Client Events (Received by Extension)
// ============================================================================

/**
 * Event: status
 * Broadcast of current task status (sent on connect and status changes)
 */
export type StatusEvent = TaskStatus

/**
 * Event: log_event
 * Real-time log event from the Browser.AI agent
 */
export type LogEventBroadcast = LogEvent

/**
 * Event: task_started
 * Confirmation that task has started
 */
export interface TaskStartedPayload {
  message: string
  success?: boolean
  error?: string
}

/**
 * Event: task_action_result
 * Result of a task action (stop, pause, resume)
 */
export type TaskActionResultPayload = ActionResult

/**
 * Event: error
 * Error message from server
 */
export interface ErrorPayload {
  message: string
  details?: string
}

// ============================================================================
// Socket Event Map (for type-safe socket.io usage)
// ============================================================================

/**
 * Client to Server event map
 */
export interface ClientToServerEvents {
  extension_connect: () => void
  start_task: (data: StartTaskPayload) => void
  stop_task: () => void
  pause_task: () => void
  resume_task: () => void
  get_status: () => void
}

/**
 * Server to Client event map
 */
export interface ServerToClientEvents {
  status: (status: TaskStatus) => void
  log_event: (event: LogEvent) => void
  task_started: (data: TaskStartedPayload) => void
  task_action_result: (result: ActionResult) => void
  task_result: (result: { task: string; success: boolean; history?: string; agent_id?: string }) => void
  error: (error: ErrorPayload) => void
  structured_event: (event: any) => void // New structured event system
  connect: () => void
  disconnect: () => void
}

// ============================================================================
// Helper Types
// ============================================================================

/**
 * Type-safe socket type for extension
 */
export type ExtensionSocket = {
  on<Event extends keyof ServerToClientEvents>(
    event: Event,
    listener: ServerToClientEvents[Event],
  ): void
  emit<Event extends keyof ClientToServerEvents>(
    event: Event,
    ...args: Parameters<ClientToServerEvents[Event]>
  ): void
  connected: boolean
  close(): void
}

// ============================================================================
// Constants
// ============================================================================

export const WEBSOCKET_NAMESPACE = '/extension'
export const DEFAULT_SERVER_URL = 'http://localhost:5000'
export const MAX_RECONNECTION_ATTEMPTS = 5
export const RECONNECTION_DELAY_MS = 1000
export const MAX_LOGS = 1000

// ============================================================================
// Validation Helpers
// ============================================================================

export function isLogEvent(obj: any): obj is LogEvent {
  return (
    obj &&
    typeof obj.timestamp === 'string' &&
    typeof obj.level === 'string' &&
    typeof obj.logger_name === 'string' &&
    typeof obj.message === 'string' &&
    typeof obj.event_type === 'string'
  )
}

export function isTaskStatus(obj: any): obj is TaskStatus {
  return (
    obj &&
    typeof obj.is_running === 'boolean' &&
    (obj.current_task === null || typeof obj.current_task === 'string') &&
    typeof obj.has_agent === 'boolean'
  )
}

export function isActionResult(obj: any): obj is ActionResult {
  return obj && typeof obj.success === 'boolean'
}
