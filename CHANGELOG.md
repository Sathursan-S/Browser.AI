# CHANGELOG - Browser.AI

All notable changes to the Browser.AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2025.10.09

### Added - Extension Local Development Simplification

#### Browser Extension (`browser_ai_extension/`)
- **feat**: Added simplified CDP endpoint detection for local Playwright setup
  - Hardcoded `http://localhost:9222` for local development
  - Removed complex dynamic CDP endpoint detection
  - Files: `src/sidepanel/SidePanel.tsx`, `src/background/index.ts`

- **docs**: Added `LOCAL_SETUP_SIMPLIFICATION.md` documentation
  - Explains changes for local Playwright setup
  - Provides usage instructions and architecture comparison
  - Documents commented-out code for future reference

#### Code Optimization
- **chore**: Commented out unnecessary CDP proxy code for local setup
  - Removed `chrome.debugger` API dependency for local development
  - Commented out extension-proxy mode handlers
  - Simplified message handling in background script
  - Files affected:
    - `browser_ai_extension/browse_ai/src/background/index.ts`
    - `browser_ai_extension/browse_ai/src/sidepanel/SidePanel.tsx`

- **perf**: Reduced complexity for local development workflow
  - No tab querying needed
  - No runtime CDP endpoint detection
  - Direct connection to `localhost:9222`

### Changed

#### Extension Architecture
- **update**: Modified CDP connection strategy
  - From: Extension-proxy mode with dynamic tab detection
  - To: Direct CDP mode with hardcoded local endpoint
  - Maintains compatibility for production deployment (code preserved in comments)

#### Background Script
- **update**: Simplified message handler
  - Removed: `GET_CDP_ENDPOINT`, `ATTACH_DEBUGGER`, `DETACH_DEBUGGER`, `SEND_CDP_COMMAND` handlers
  - Kept: `SHOW_NOTIFICATION` handler for task completion popups
  - Maintained: Extension icon click handler for side panel

#### Side Panel
- **update**: Simplified `getCdpEndpoint()` function
  - Removed async tab query logic
  - Removed background script messaging for CDP
  - Added informative log message for local endpoint usage

### Documentation

- **docs**: Enhanced inline code comments
  - Added clear markers for commented-out code sections
  - Explained reasons for code removal/commenting
  - Preserved original functionality documentation

- **docs**: Updated extension documentation structure
  - `LOCAL_SETUP_SIMPLIFICATION.md` - Local development guide
  - `CDP_WEBSOCKET_README.md` - CDP WebSocket architecture
  - `PROTOCOL.md` - WebSocket protocol specification

### Developer Experience

- **feat**: Simplified local development setup
  - One-step CDP endpoint configuration
  - Reduced boilerplate for Playwright integration
  - Clearer separation between local and production modes

- **chore**: Improved code maintainability
  - Commented code preserved for future production use
  - Clear migration path back to full extension mode
  - Comprehensive explanatory comments

---

## [0.2.0] - 2025.10.08

### Added - Chrome Extension Support

#### Browser Extension (`browser_ai_extension/`)
- **feat**: Initial Chrome extension implementation
  - Side panel UI with React + TypeScript
  - WebSocket integration with Browser.AI server
  - Real-time task execution and log streaming
  - Notification system for task completion
  - Settings management with persistence

#### Extension Features
- **feat**: Task management interface
  - Start/stop/pause/resume task controls
  - Real-time status updates
  - Task result display
  - Connection status indicators

- **feat**: CDP (Chrome DevTools Protocol) integration
  - Extension-proxy mode for CDP command routing
  - Tab-specific browser context management
  - Debugger attachment/detachment lifecycle
  - CDP command proxy through background script

- **feat**: WebSocket Protocol implementation
  - `/extension` namespace for extension communication
  - Bidirectional event streaming
  - Type-safe message passing (TypeScript/Python)
  - Auto-reconnection support

#### GUI Components
- **feat**: Web-based GUI (`browser_ai_gui/`)
  - Flask + SocketIO server
  - WebSocket server for extension communication
  - CDP WebSocket server for browser control
  - Event adapter for log streaming

### Documentation

- **docs**: Extension documentation suite
  - `EXTENSION_README.md` - Getting started guide
  - `CDP_WEBSOCKET_README.md` - CDP architecture
  - `PROTOCOL.md` - WebSocket protocol specification
  - `PROTOCOL_IMPLEMENTATION_SUMMARY.md` - Implementation details
  - `LOG_STREAMING_FIX.md` - Log streaming implementation
  - `STATE_MANAGEMENT.md` - State persistence guide
  - `UI_FEATURES.md` - UI components documentation
  - `QUICK_START.md` - Quick start guide

---

## [0.1.0] - 2025.10.04

### Added - Initial Release

#### Core Framework (`browser_ai/`)
- **feat**: Agent service implementation
  - LLM-powered browser automation
  - Multi-model support (OpenAI, Anthropic, etc.)
  - Vision capabilities for screenshot analysis
  - Message management with token awareness

- **feat**: Controller with action registry
  - Modular action system
  - Custom action registration
  - Parameter validation with Pydantic
  - Action exclusion capabilities

- **feat**: Browser service
  - Enhanced Playwright wrapper
  - Browser configuration management
  - Automatic browser lifecycle handling
  - CDP connection support

- **feat**: DOM processing service
  - JavaScript injection for element detection
  - Visual element highlighting
  - Coordinate mapping system
  - Viewport management

#### Examples (`examples/`)
- **feat**: Comprehensive example collection
  - Simple usage examples
  - Browser configuration examples
  - Custom function examples
  - Feature demonstrations
  - Integration examples
  - Use case scenarios

#### Documentation (`docs/`)
- **docs**: Technical specification suite
  - `architecture-overview.md` - System architecture
  - `agent-implementation.md` - Agent details
  - `controller-actions.md` - Action system
  - `browser-management.md` - Browser control
  - `dom-processing.md` - DOM handling
  - `workflows-integration.md` - Integration guide

### Infrastructure

- **chore**: Project setup
  - Python package configuration (`pyproject.toml`)
  - UV package manager integration
  - Development dependencies
  - Testing framework setup

- **chore**: Development tools
  - Launch script for GUI dependencies
  - Test utilities
  - Configuration management

---

## Version History Summary

- **[Unreleased]** - Local Playwright setup simplification (2025.10.09)
- **[0.2.0]** - Chrome extension support (2025.10.08)
- **[0.1.0]** - Initial release (2025.10.04)

---

## Migration Guide

### From Extension-Proxy to Local CDP (v0.2.0 → Unreleased)

If you're using the extension with local Playwright setup:

1. **Update to latest code**
   ```bash
   git pull origin feat/browser-extention
   ```

2. **Rebuild extension**
   ```bash
   cd browser_ai_extension/browse_ai
   npm run build
   ```

3. **Start Chrome with CDP**
   ```bash
   chrome.exe --remote-debugging-port=9222 --user-data-dir=./chrome-debug
   ```

4. **No configuration needed** - Extension automatically uses `localhost:9222`

### Reverting to Extension-Proxy Mode

If you need full extension-proxy functionality:

1. Uncomment CDP proxy code in:
   - `browser_ai_extension/browse_ai/src/background/index.ts`
   - `browser_ai_extension/browse_ai/src/sidepanel/SidePanel.tsx`

2. Rebuild extension

3. Reload in Chrome

---

## Contributing

When adding entries to this changelog:

1. **Group changes** by category: Added, Changed, Removed, Fixed, Deprecated, Security
2. **Use semantic versioning** for version numbers
3. **Include dates** in yyyy.MM.dd format
4. **Reference files** that were changed
5. **Explain impact** on users/developers
6. **Link to issues/PRs** when applicable

---

## Maintainers

- **Project**: Browser.AI
- **Repository**: Browser.AI by Sathursan-S
- **Branch**: feat/browser-extention (development)
- **License**: See LICENSE file

---

*For extension-specific changes, see `browser_ai_extension/browse_ai/CHANGELOG.md`*
