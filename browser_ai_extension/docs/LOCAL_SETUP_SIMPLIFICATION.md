# Local Playwright Setup Simplification

## Overview

This document explains the code changes made to simplify the Browser.AI extension for local Playwright setup with CDP debug mode.

## Changes Made

### 1. Background Script (`browse_ai/src/background/index.ts`)

**What was commented out:**
- ❌ CDP proxy message handlers (`GET_CDP_ENDPOINT`, `ATTACH_DEBUGGER`, `DETACH_DEBUGGER`, `SEND_CDP_COMMAND`)
- ❌ `chrome.debugger` API calls
- ❌ Debugger attachment tracking
- ❌ Tab lifecycle management for CDP

**What remains active:**
- ✅ `SHOW_NOTIFICATION` handler (for task completion notifications)
- ✅ Extension action handler (opens side panel)

**Reason:** 
With local Playwright setup running Chrome with `--remote-debugging-port=9222`, you have direct CDP access. The extension doesn't need to act as a CDP proxy.

### 2. Side Panel (`browse_ai/src/sidepanel/SidePanel.tsx`)

**Original Implementation:**
```typescript
// Complex CDP endpoint detection via background script
const getCdpEndpoint = async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  const response = await chrome.runtime.sendMessage({
    type: 'GET_CDP_ENDPOINT',
    tabId: tab.id,
  })
  // ... complex proxy logic
}
```

**Simplified Implementation:**
```typescript
// Direct CDP endpoint for local setup
const getCdpEndpoint = async () => {
  const endpoint = 'http://localhost:9222'
  setCdpEndpoint(endpoint)
  addSystemLog('Using local CDP endpoint: http://localhost:9222', 'INFO')
  return endpoint
}
```

**Reason:**
For local development, the CDP endpoint is always `http://localhost:9222`. No need for dynamic detection or tab queries.

## Architecture Comparison

### Before (Extension Proxy Mode)
```
┌──────────────┐      ┌────────────────┐      ┌──────────────┐
│  Side Panel  │─────►│ Background     │─────►│ chrome.      │
│   (React)    │      │ Script         │      │ debugger API │
└──────────────┘      │ (CDP Proxy)    │      └──────────────┘
                      └────────────────┘              │
                              │                       │
                              ▼                       ▼
                      ┌────────────────┐      ┌──────────────┐
                      │  Server        │      │  Browser Tab │
                      │  (Browser.AI)  │      │              │
                      └────────────────┘      └──────────────┘
```

### After (Direct CDP Mode)
```
┌──────────────┐      
│  Side Panel  │──────┐
│   (React)    │      │
└──────────────┘      │
                      ▼
              ┌────────────────┐      ┌──────────────────────┐
              │  Server        │─────►│  Playwright Browser  │
              │  (Browser.AI)  │ CDP  │  (localhost:9222)    │
              └────────────────┘      └──────────────────────┘
```

## Usage for Local Development

### 1. Start Chrome with Debug Mode
```bash
chrome.exe --remote-debugging-port=9222 --user-data-dir=./chrome-debug-profile
```

### 2. Start Browser.AI Server
```bash
uv run .\browser_ai_gui\main.py web --port 5000
```

### 3. Load Extension
1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Load unpacked extension from `browser_ai_extension/browse_ai/build`

### 4. Use Extension
1. Click extension icon to open side panel
2. Enter a task
3. Click "Start Task"
4. The extension will automatically use `http://localhost:9222` as the CDP endpoint

## Files Modified

1. **`browser_ai_extension/browse_ai/src/background/index.ts`**
   - Commented out CDP proxy handlers
   - Removed chrome.debugger API usage
   - Kept notification handler active

2. **`browser_ai_extension/browse_ai/src/sidepanel/SidePanel.tsx`**
   - Simplified `getCdpEndpoint()` to return hardcoded localhost:9222
   - Removed dynamic tab detection
   - Removed background script communication for CDP

## What This Means

### ✅ You CAN:
- Run tasks through the extension UI
- Use direct CDP connection at localhost:9222
- Develop and test without complex proxy setup
- See task logs and notifications

### ❌ You DON'T NEED:
- `chrome.debugger` permissions (can be removed from manifest if desired)
- Tab-specific CDP endpoint detection
- Extension proxy mode
- Background script CDP message passing

## Reverting to Full Extension Mode

If you later want to use the extension in production (non-local setup), uncomment:
1. All CDP proxy code in `background/index.ts`
2. Original `getCdpEndpoint()` implementation in `SidePanel.tsx`

## Notes

- The commented code is preserved with explanatory comments
- Original functionality can be restored by uncommenting
- This simplification is specifically for local Playwright development
- Production deployment would need the full CDP proxy implementation

## Testing

After these changes, test:
1. ✅ Extension loads without errors
2. ✅ Side panel opens when clicking extension icon
3. ✅ Can connect to server at localhost:5000
4. ✅ Can start tasks using localhost:9222 CDP endpoint
5. ✅ Receives task logs and completion notifications

## Questions?

If you encounter issues:
1. Check Chrome is running with `--remote-debugging-port=9222`
2. Verify server is running on `localhost:5000`
3. Check browser console for errors
4. Ensure extension is properly built and loaded
