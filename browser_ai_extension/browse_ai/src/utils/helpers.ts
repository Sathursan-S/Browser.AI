/**
 * Utility functions for Browser.AI Extension
 */

import { ExtensionSettings, DEFAULT_SETTINGS } from '../types/protocol'

// Use global chrome API
declare const chrome: any

// ============================================================================
// Settings Management
// ============================================================================

/**
 * Load settings from Chrome storage
 */
export async function loadSettings(): Promise<ExtensionSettings> {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['settings'], (result: any) => {
      if (result.settings) {
        resolve({ ...DEFAULT_SETTINGS, ...result.settings })
      } else {
        resolve(DEFAULT_SETTINGS)
      }
    })
  })
}

/**
 * Save settings to Chrome storage
 */
export async function saveSettings(settings: ExtensionSettings): Promise<void> {
  return new Promise((resolve, reject) => {
    chrome.storage.sync.set({ settings }, () => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError)
      } else {
        resolve()
      }
    })
  })
}

/**
 * Listen for settings changes
 */
export function onSettingsChanged(callback: (settings: ExtensionSettings) => void): void {
  chrome.storage.onChanged.addListener((changes: any, area: string) => {
    if (area === 'sync' && changes.settings) {
      callback(changes.settings.newValue)
    }
  })
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

/**
 * Open options page
 */
export function openOptionsPage(): void {
  chrome.runtime.openOptionsPage()
}
