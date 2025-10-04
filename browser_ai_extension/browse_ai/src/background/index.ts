console.log('Browser.AI background service worker is running')

// Track debugger attachments
const debuggerAttachments = new Map<number, boolean>()

// Define message types
interface GetCdpEndpointMessage {
  type: 'GET_CDP_ENDPOINT'
  tabId: number
}

interface AttachDebuggerMessage {
  type: 'ATTACH_DEBUGGER'
  tabId: number
}

interface DetachDebuggerMessage {
  type: 'DETACH_DEBUGGER'
  tabId: number
}

interface SendCdpCommandMessage {
  type: 'SEND_CDP_COMMAND'
  tabId: number
  method: string
  params?: any
  commandId: string
}

interface ShowNotificationMessage {
  type: 'SHOW_NOTIFICATION'
  notificationType: 'user_interaction' | 'task_complete' | 'error'
  message: string
  details?: string
  result?: any
}

type ExtensionMessage =
  | GetCdpEndpointMessage
  | AttachDebuggerMessage
  | DetachDebuggerMessage
  | SendCdpCommandMessage
  | ShowNotificationMessage

// Handle messages from side panel
chrome.runtime.onMessage.addListener((request: ExtensionMessage, sender, sendResponse) => {
  if (request.type === 'GET_CDP_ENDPOINT') {
    handleGetCdpEndpoint(request, sendResponse)
    return true // Will respond asynchronously
  }

  if (request.type === 'ATTACH_DEBUGGER') {
    handleAttachDebugger(request, sendResponse)
    return true // Will respond asynchronously
  }

  if (request.type === 'DETACH_DEBUGGER') {
    handleDetachDebugger(request, sendResponse)
    return true // Will respond asynchronously
  }

  if (request.type === 'SEND_CDP_COMMAND') {
    handleSendCdpCommand(request, sendResponse)
    return true // Will respond asynchronously
  }

  if (request.type === 'SHOW_NOTIFICATION') {
    handleShowNotification(request, sendResponse)
    return true // Will respond asynchronously
  }
})

async function handleGetCdpEndpoint(
  request: GetCdpEndpointMessage,
  sendResponse: (response: any) => void,
) {
  // Since we can't get the WebSocket endpoint in extensions, we return a success
  // indicating that CDP commands can be proxied through this extension
  sendResponse({
    success: true,
    endpoint: 'extension-proxy', // Special marker indicating extension proxy mode
    message: 'CDP commands will be proxied through the extension',
  })
}

async function handleAttachDebugger(
  request: AttachDebuggerMessage,
  sendResponse: (response: any) => void,
) {
  try {
    const { tabId } = request

    // Attach debugger to the tab
    await chrome.debugger.attach({ tabId }, '1.3')
    debuggerAttachments.set(tabId, true)

    console.log(`Debugger attached to tab ${tabId}`)
    sendResponse({ success: true })
  } catch (error) {
    console.error('Failed to attach debugger:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    sendResponse({
      success: false,
      error: errorMessage,
    })
  }
}

async function handleDetachDebugger(
  request: DetachDebuggerMessage,
  sendResponse: (response: any) => void,
) {
  try {
    const { tabId } = request

    if (debuggerAttachments.has(tabId)) {
      await chrome.debugger.detach({ tabId })
      debuggerAttachments.delete(tabId)
      console.log(`Debugger detached from tab ${tabId}`)
    }

    sendResponse({ success: true })
  } catch (error) {
    console.error('Failed to detach debugger:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    sendResponse({
      success: false,
      error: errorMessage,
    })
  }
}

async function handleSendCdpCommand(
  request: SendCdpCommandMessage,
  sendResponse: (response: any) => void,
) {
  try {
    const { tabId, method, params, commandId } = request

    if (!debuggerAttachments.has(tabId)) {
      sendResponse({
        success: false,
        error: 'Debugger not attached to tab',
        commandId,
      })
      return
    }

    const result = await chrome.debugger.sendCommand({ tabId }, method, params || {})

    sendResponse({
      success: true,
      result,
      commandId,
    })
  } catch (error) {
    console.error('Failed to send CDP command:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    sendResponse({
      success: false,
      error: errorMessage,
      commandId: request.commandId,
    })
  }
}

// Clean up debugger attachments when tabs are closed
chrome.tabs.onRemoved.addListener((tabId) => {
  if (debuggerAttachments.has(tabId)) {
    chrome.debugger.detach({ tabId }).catch(console.error)
    debuggerAttachments.delete(tabId)
  }
})

// Handle debugger detach events
chrome.debugger.onDetach.addListener((source, reason) => {
  const tabId = source.tabId
  if (tabId && debuggerAttachments.has(tabId)) {
    debuggerAttachments.delete(tabId)
    console.log(`Debugger detached from tab ${tabId}: ${reason}`)
  }
})

// Open side panel when extension icon is clicked
chrome.action.onClicked.addListener((tab) => {
  if (tab.windowId) {
    // @ts-ignore - sidePanel.open is available in MV3
    chrome.sidePanel.open({ windowId: tab.windowId })
  }
})

async function handleShowNotification(
  request: ShowNotificationMessage,
  sendResponse: (response: any) => void,
) {
  try {
    const { notificationType, message, details, result } = request
    const timestamp = new Date().toISOString()

    // Create notification window
    const width = 500
    const height = 400
    const left = Math.round((screen.width - width) / 2)
    const top = Math.round((screen.height - height) / 2)

    const params = new URLSearchParams({
      type: notificationType,
      message,
      details: details || '',
      result: result ? encodeURIComponent(JSON.stringify(result)) : '',
      timestamp,
    })

    await chrome.windows.create({
      url: `notification.html?${params.toString()}`,
      type: 'popup',
      width,
      height,
      left,
      top,
      focused: true,
    })

    sendResponse({ success: true })
  } catch (error) {
    console.error('Failed to show notification:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    sendResponse({
      success: false,
      error: errorMessage,
    })
  }
}
