console.log('Browser.AI background service worker is running')

// Track debugger attachments
const debuggerAttachments = new Map()

// Handle messages from side panel
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
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
})

async function handleGetCdpEndpoint(request, sendResponse) {
  try {
    const { tabId } = request
    
    // Get the debugging port (default Chrome debugging port)
    const debugPort = 9222
    
    // Fetch debugger info from Chrome DevTools Protocol
    const response = await fetch(`http://localhost:${debugPort}/json/list`)
    const targets = await response.json()
    
    // Find the target matching our tab
    const target = targets.find(t => t.type === 'page')
    
    if (target && target.webSocketDebuggerUrl) {
      sendResponse({ 
        success: true, 
        endpoint: target.webSocketDebuggerUrl 
      })
    } else {
      sendResponse({ 
        success: false, 
        error: 'CDP endpoint not found. Make sure Chrome is started with --remote-debugging-port=9222' 
      })
    }
  } catch (error) {
    console.error('Failed to get CDP endpoint:', error)
    sendResponse({ 
      success: false, 
      error: error.message 
    })
  }
}

async function handleAttachDebugger(request, sendResponse) {
  try {
    const { tabId } = request
    
    // Attach debugger to the tab
    await chrome.debugger.attach({ tabId }, '1.3')
    debuggerAttachments.set(tabId, true)
    
    console.log(`Debugger attached to tab ${tabId}`)
    sendResponse({ success: true })
  } catch (error) {
    console.error('Failed to attach debugger:', error)
    sendResponse({ 
      success: false, 
      error: error.message 
    })
  }
}

async function handleDetachDebugger(request, sendResponse) {
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
    sendResponse({ 
      success: false, 
      error: error.message 
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
  chrome.sidePanel.open({ windowId: tab.windowId })
})
