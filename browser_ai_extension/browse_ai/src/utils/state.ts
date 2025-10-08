/**
 * Global Extension State Manager
 *
 * Handles persistent state management for the extension using Chrome storage.
 * Ensures state is maintained across extension reloads, tab changes, and browser restarts.
 */

import { TaskStatus } from '../types/protocol'

const STATE_KEYS = {
  TASK_STATUS: 'taskStatus',
  CDP_ENDPOINT: 'cdpEndpoint',
  LAST_TASK: 'lastTask',
  CONVERSATION_MESSAGES: 'conversationMessages',
  CONVERSATION_INTENT: 'conversationIntent',
} as const

/**
 * Load task status from persistent storage
 */
export const loadTaskStatus = async (): Promise<TaskStatus | null> => {
  return new Promise((resolve) => {
    chrome.storage.local.get([STATE_KEYS.TASK_STATUS], (result) => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to load task status:', chrome.runtime.lastError)
        resolve(null)
      } else if (result[STATE_KEYS.TASK_STATUS]) {
        console.log('[State] Loaded task status:', result[STATE_KEYS.TASK_STATUS])
        resolve(result[STATE_KEYS.TASK_STATUS])
      } else {
        resolve(null)
      }
    })
  })
}

/**
 * Save task status to persistent storage
 */
export const saveTaskStatus = async (status: TaskStatus): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ [STATE_KEYS.TASK_STATUS]: status }, () => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to save task status:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else {
        console.log('[State] Saved task status:', status)
        resolve()
      }
    })
  })
}

/**
 * Load CDP endpoint from persistent storage
 */
export const loadCdpEndpoint = async (): Promise<string | null> => {
  return new Promise((resolve) => {
    chrome.storage.local.get([STATE_KEYS.CDP_ENDPOINT], (result) => {
      if (result[STATE_KEYS.CDP_ENDPOINT]) {
        console.log('[State] Loaded CDP endpoint:', result[STATE_KEYS.CDP_ENDPOINT])
        resolve(result[STATE_KEYS.CDP_ENDPOINT])
      } else {
        resolve(null)
      }
    })
  })
}

/**
 * Save CDP endpoint to persistent storage
 */
export const saveCdpEndpoint = async (endpoint: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ [STATE_KEYS.CDP_ENDPOINT]: endpoint }, () => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to save CDP endpoint:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else {
        console.log('[State] Saved CDP endpoint:', endpoint)
        resolve()
      }
    })
  })
}

/**
 * Load last task description from persistent storage
 */
export const loadLastTask = async (): Promise<string | null> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get([STATE_KEYS.LAST_TASK], (result) => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to load last task:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else if (result[STATE_KEYS.LAST_TASK]) {
        console.log('[State] Loaded last task:', result[STATE_KEYS.LAST_TASK])
        resolve(result[STATE_KEYS.LAST_TASK])
      } else {
        resolve(null)
      }
    })
  })
}

/**
 * Save last task description to persistent storage
 */
export const saveLastTask = async (task: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ [STATE_KEYS.LAST_TASK]: task }, () => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to save last task:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else {
        console.log('[State] Saved last task:', task)
        resolve()
      }
    })
  })
}

/**
 * Clear all extension state
 */
export const clearExtensionState = async (): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.remove(Object.values(STATE_KEYS), () => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to clear extension state:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else {
        console.log('[State] Cleared all extension state')
        resolve()
      }
    })
  })
}

/**
 * Listen for changes to task status from other extension pages
 */
export const onTaskStatusChanged = (callback: (status: TaskStatus) => void): (() => void) => {
  const listener = (changes: any, areaName: string) => {
    console.log('[State] Storage change detected:', changes, areaName)
    if (areaName === 'local' && changes[STATE_KEYS.TASK_STATUS]) {
      const newStatus = changes[STATE_KEYS.TASK_STATUS].newValue
      if (
        newStatus &&
        newStatus !== changes[STATE_KEYS.TASK_STATUS].oldValue
      ) {
        console.log('[State] Task status changed:', newStatus)
        callback(newStatus)
      }
    }
  }
  chrome.storage.onChanged.addListener(listener)
  return () => {
    chrome.storage.onChanged.removeListener(listener)
  }
}

/**
 * Message type for conversation persistence
 */
export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

/**
 * Intent type for conversation persistence
 */
export interface ConversationIntent {
  task_description: string
  is_ready: boolean
  confidence: number
}

/**
 * Load conversation messages from persistent storage
 */
export const loadConversationMessages = async (): Promise<ConversationMessage[]> => {
  return new Promise((resolve) => {
    chrome.storage.local.get([STATE_KEYS.CONVERSATION_MESSAGES], (result) => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to load conversation messages:', chrome.runtime.lastError)
        resolve([])
      } else if (result[STATE_KEYS.CONVERSATION_MESSAGES]) {
        console.log('[State] Loaded conversation messages:', result[STATE_KEYS.CONVERSATION_MESSAGES])
        resolve(result[STATE_KEYS.CONVERSATION_MESSAGES])
      } else {
        resolve([])
      }
    })
  })
}

/**
 * Save conversation messages to persistent storage
 */
export const saveConversationMessages = async (messages: ConversationMessage[]): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ [STATE_KEYS.CONVERSATION_MESSAGES]: messages }, () => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to save conversation messages:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else {
        console.log('[State] Saved conversation messages:', messages.length, 'messages')
        resolve()
      }
    })
  })
}

/**
 * Load conversation intent from persistent storage
 */
export const loadConversationIntent = async (): Promise<ConversationIntent | null> => {
  return new Promise((resolve) => {
    chrome.storage.local.get([STATE_KEYS.CONVERSATION_INTENT], (result) => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to load conversation intent:', chrome.runtime.lastError)
        resolve(null)
      } else if (result[STATE_KEYS.CONVERSATION_INTENT]) {
        console.log('[State] Loaded conversation intent:', result[STATE_KEYS.CONVERSATION_INTENT])
        resolve(result[STATE_KEYS.CONVERSATION_INTENT])
      } else {
        resolve(null)
      }
    })
  })
}

/**
 * Save conversation intent to persistent storage
 */
export const saveConversationIntent = async (intent: ConversationIntent | null): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ [STATE_KEYS.CONVERSATION_INTENT]: intent }, () => {
      if (chrome.runtime.lastError) {
        console.error('[State] Failed to save conversation intent:', chrome.runtime.lastError)
        reject(chrome.runtime.lastError)
      } else {
        console.log('[State] Saved conversation intent:', intent)
        resolve()
      }
    })
  })
}

/**
 * Clear conversation state
 */
export const clearConversationState = async (): Promise<void> => {
  return new Promise((resolve, reject) => {
    chrome.storage.local.remove(
      [STATE_KEYS.CONVERSATION_MESSAGES, STATE_KEYS.CONVERSATION_INTENT],
      () => {
        if (chrome.runtime.lastError) {
          console.error('[State] Failed to clear conversation state:', chrome.runtime.lastError)
          reject(chrome.runtime.lastError)
        } else {
          console.log('[State] Cleared conversation state')
          resolve()
        }
      }
    )
  })
}
