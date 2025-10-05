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
} as const

/**
 * Load task status from persistent storage
 */
export const loadTaskStatus = async (): Promise<TaskStatus | null> => {
  return new Promise((resolve) => {
    chrome.storage.local.get([STATE_KEYS.TASK_STATUS], (result) => {
      if (result[STATE_KEYS.TASK_STATUS]) {
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
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STATE_KEYS.TASK_STATUS]: status }, () => {
      console.log('[State] Saved task status:', status)
      resolve()
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
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STATE_KEYS.CDP_ENDPOINT]: endpoint }, () => {
      console.log('[State] Saved CDP endpoint:', endpoint)
      resolve()
    })
  })
}

/**
 * Load last task description from persistent storage
 */
export const loadLastTask = async (): Promise<string | null> => {
  return new Promise((resolve) => {
    chrome.storage.local.get([STATE_KEYS.LAST_TASK], (result) => {
      if (result[STATE_KEYS.LAST_TASK]) {
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
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STATE_KEYS.LAST_TASK]: task }, () => {
      console.log('[State] Saved last task:', task)
      resolve()
    })
  })
}

/**
 * Clear all extension state
 */
export const clearExtensionState = async (): Promise<void> => {
  return new Promise((resolve) => {
    chrome.storage.local.remove(Object.values(STATE_KEYS), () => {
      console.log('[State] Cleared all extension state')
      resolve()
    })
  })
}

/**
 * Listen for changes to task status from other extension pages
 */
export const onTaskStatusChanged = (
  callback: (status: TaskStatus) => void
): void => {
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local' && changes[STATE_KEYS.TASK_STATUS]) {
      const newStatus = changes[STATE_KEYS.TASK_STATUS].newValue
      if (newStatus) {
        console.log('[State] Task status changed:', newStatus)
        callback(newStatus)
      }
    }
  })
}
