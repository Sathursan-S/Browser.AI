import { useState, useEffect } from 'react'
import './Options.css'

interface Settings {
  serverUrl: string
  devMode: boolean
  autoReconnect: boolean
  maxLogs: number
  showNotifications: boolean
}

interface LLMConfig {
  provider: string
  model: string
  temperature: number
  api_key: string
}

interface BrowserConfig {
  headless: boolean
  disable_security: boolean
}

interface AgentConfig {
  use_vision: boolean
  max_failures: number
  max_steps: number
}

interface ServerConfig {
  llm: LLMConfig
  browser: BrowserConfig
  agent: AgentConfig
  supported_providers: string[]
  default_models: Record<string, string[]>
}

const DEFAULT_SETTINGS: Settings = {
  serverUrl: 'http://localhost:5000',
  devMode: false,
  autoReconnect: true,
  maxLogs: 1000,
  showNotifications: true,
}

const DEFAULT_SERVER_CONFIG: ServerConfig = {
  llm: {
    provider: 'openai',
    model: 'gpt-4o',
    temperature: 0.0,
    api_key: '',
  },
  browser: {
    headless: false,
    disable_security: true,
  },
  agent: {
    use_vision: true,
    max_failures: 3,
    max_steps: 50,
  },
  supported_providers: [],
  default_models: {},
}

export const Options = () => {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [serverConfig, setServerConfig] = useState<ServerConfig>(DEFAULT_SERVER_CONFIG)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [configStatus, setConfigStatus] = useState<
    'idle' | 'loading' | 'saving' | 'saved' | 'error'
  >('idle')
  const [connectionStatus, setConnectionStatus] = useState<
    'disconnected' | 'connecting' | 'connected' | 'error'
  >('disconnected')
  const [activeTab, setActiveTab] = useState<'extension' | 'server'>('extension')

  // Load settings from Chrome storage
  useEffect(() => {
    chrome.storage.sync.get(['settings'], (result) => {
      if (result.settings) {
        setSettings({ ...DEFAULT_SETTINGS, ...result.settings })
      }
    })
  }, [])

  // Load server config when component mounts or server URL changes
  useEffect(() => {
    if (settings.serverUrl) {
      loadServerConfig()
    }
  }, [settings.serverUrl])

  const loadServerConfig = async () => {
    setConfigStatus('loading')
    setConnectionStatus('connecting')

    try {
      const response = await fetch(`${settings.serverUrl}/api/config`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const config = await response.json()
      setServerConfig({
        ...config,
        llm: {
          ...config.llm,
          api_key: config.llm.has_api_key ? '••••••••' : '',
        },
      })
      setConfigStatus('idle')
      setConnectionStatus('connected')
    } catch (error) {
      console.error('Failed to load server config:', error)
      setConfigStatus('error')
      setConnectionStatus('error')
    }
  }

  const saveServerConfig = async () => {
    setConfigStatus('saving')

    try {
      const configToSend = {
        llm: {
          ...serverConfig.llm,
          // Only send API key if it's not the masked value
          ...(serverConfig.llm.api_key !== '••••••••' && { api_key: serverConfig.llm.api_key }),
        },
        browser: serverConfig.browser,
        agent: serverConfig.agent,
      }

      const response = await fetch(`${settings.serverUrl}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configToSend),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      if (result.success) {
        setConfigStatus('saved')
        setTimeout(() => setConfigStatus('idle'), 2000)
      } else {
        throw new Error(result.error || 'Unknown error')
      }
    } catch (error) {
      console.error('Failed to save server config:', error)
      setConfigStatus('error')
      setTimeout(() => setConfigStatus('idle'), 2000)
    }
  }

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      await chrome.storage.sync.set({ settings })
      setSaveStatus('saved')


      // Notify all tabs about settings update
      chrome.runtime.sendMessage({
        type: 'SETTINGS_UPDATED',
        settings,
      })


      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 2000)
    }
  }

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS)
  }

  const handleChange = (key: keyof Settings, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const handleServerConfigChange = (
    section: 'llm' | 'browser' | 'agent',
    key: string,
    value: any,
  ) => {
    setServerConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }))
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return '#22c55e'
      case 'connecting':
        return '#f59e0b'
      case 'error':
        return '#ef4444'
      default:
        return '#6b7280'
    }
  }

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return '🟢 Connected'
      case 'connecting':
        return '🟡 Connecting...'
      case 'error':
        return '🔴 Connection Failed'
      default:
        return '⚪ Disconnected'
    }
  }

  return (
    <div className="options-container">
      <header className="options-header">
        <h1>Browze.AI Settings</h1>
        <p className="subtitle">Configure your browser automation extension</p>

        <div className="connection-status" style={{ color: getConnectionStatusColor() }}>
          {getConnectionStatusText()}
        </div>
      </header>

      <nav className="settings-tabs">
        <button
          className={`tab-button ${activeTab === 'extension' ? 'active' : ''}`}
          onClick={() => setActiveTab('extension')}
        >
          🔌 Extension Settings
        </button>
        <button
          className={`tab-button ${activeTab === 'server' ? 'active' : ''}`}
          onClick={() => setActiveTab('server')}
          disabled={connectionStatus !== 'connected'}
        >
          ⚙️ Server Configuration
        </button>
      </nav>

      <div className="options-content">
        {activeTab === 'extension' && (
          <>
            <section className="settings-section">
              <h2>🔌 Connection Settings</h2>

              <div className="setting-group">
                <label htmlFor="serverUrl">
                  <span className="label-text">Server URL</span>
                  <span className="label-description">
                    The Browser.AI server endpoint (Python server)
                  </span>
                </label>
                <div className="input-with-button">
                  <input
                    id="serverUrl"
                    type="text"
                    className="input-text"
                    value={settings.serverUrl}
                    onChange={(e) => handleChange('serverUrl', e.target.value)}
                    placeholder="http://localhost:5000"
                  />
                  <button
                    className="btn btn-secondary"
                    onClick={loadServerConfig}
                    disabled={configStatus === 'loading'}
                  >
                    {configStatus === 'loading' ? 'Testing...' : 'Test Connection'}
                  </button>
                </div>
              </div>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.autoReconnect}
                    onChange={(e) => handleChange('autoReconnect', e.target.checked)}
                  />
                  <span className="checkbox-text">
                    <strong>Auto-reconnect</strong>
                    <span className="checkbox-description">
                      Automatically reconnect when connection is lost
                    </span>
                  </span>
                </label>
              </div>
            </section>

            <section className="settings-section">
              <h2>🎨 Display Settings</h2>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.devMode}
                    onChange={(e) => handleChange('devMode', e.target.checked)}
                  />
                  <span className="checkbox-text">
                    <strong>Developer Mode</strong>
                    <span className="checkbox-description">
                      Show detailed technical logs (for debugging)
                    </span>
                  </span>
                </label>
              </div>

              <div className="setting-group">
                <label htmlFor="maxLogs">
                  <span className="label-text">Maximum Logs</span>
                  <span className="label-description">
                    Maximum number of log entries to keep in memory
                  </span>
                </label>
                <input
                  id="maxLogs"
                  type="number"
                  className="input-number"
                  min="100"
                  max="10000"
                  step="100"
                  value={settings.maxLogs}
                  onChange={(e) => handleChange('maxLogs', parseInt(e.target.value))}
                />
              </div>
            </section>

            <section className="settings-section">
              <h2>🔔 Notifications</h2>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.showNotifications}
                    onChange={(e) => handleChange('showNotifications', e.target.checked)}
                  />
                  <span className="checkbox-text">
                    <strong>Enable Notifications</strong>
                    <span className="checkbox-description">
                      Show popup notifications for important events
                    </span>
                  </span>
                </label>
              </div>
            </section>

            <div className="settings-actions">
              <button className="btn btn-secondary" onClick={handleReset}>
                Reset to Defaults
              </button>
              <button
                className={`btn btn-primary ${saveStatus === 'saving' ? 'loading' : ''}`}
                onClick={handleSave}
                disabled={saveStatus === 'saving'}
              >
                {saveStatus === 'saving' && 'Saving...'}
                {saveStatus === 'saved' && '✓ Saved!'}
                {saveStatus === 'error' && '✗ Error'}
                {saveStatus === 'idle' && 'Save Extension Settings'}
              </button>
            </div>

            {saveStatus === 'saved' && (
              <div className="save-message success">
                ✓ Extension settings saved successfully! Changes will apply on next connection.
              </div>
            )}
            {saveStatus === 'error' && (
              <div className="save-message error">
                ✗ Failed to save extension settings. Please try again.
              </div>
            )}
          </>
        )}

        {activeTab === 'server' && (
          <>
            <section className="settings-section">
              <h2>🤖 LLM Configuration</h2>

              <div className="setting-group">
                <label htmlFor="llm-provider">
                  <span className="label-text">Provider</span>
                  <span className="label-description">The LLM provider to use for AI tasks</span>
                </label>
                <select
                  id="llm-provider"
                  className="input-select"
                  value={serverConfig.llm.provider}
                  onChange={(e) => handleServerConfigChange('llm', 'provider', e.target.value)}
                >
                  {serverConfig.supported_providers.map((provider) => (
                    <option key={provider} value={provider}>
                      {provider.charAt(0).toUpperCase() + provider.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="setting-group">
                <label htmlFor="llm-model">
                  <span className="label-text">Model</span>
                  <span className="label-description">
                    The specific model to use from the selected provider
                  </span>
                </label>
                <select
                  id="llm-model"
                  className="input-select"
                  value={serverConfig.llm.model}
                  onChange={(e) => handleServerConfigChange('llm', 'model', e.target.value)}
                >
                  {(serverConfig.default_models[serverConfig.llm.provider] || []).map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              <div className="setting-group">
                <label htmlFor="llm-temperature">
                  <span className="label-text">Temperature</span>
                  <span className="label-description">
                    Controls randomness in responses (0.0 = deterministic, 1.0 = creative)
                  </span>
                </label>
                <input
                  id="llm-temperature"
                  type="number"
                  className="input-number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={serverConfig.llm.temperature}
                  onChange={(e) =>
                    handleServerConfigChange('llm', 'temperature', parseFloat(e.target.value))
                  }
                />
              </div>

              <div className="setting-group">
                <label htmlFor="llm-api-key">
                  <span className="label-text">API Key</span>
                  <span className="label-description">
                    Your API key for the selected provider (leave blank to keep existing)
                  </span>
                </label>
                <input
                  id="llm-api-key"
                  type="password"
                  className="input-text"
                  value={serverConfig.llm.api_key}
                  onChange={(e) => handleServerConfigChange('llm', 'api_key', e.target.value)}
                  placeholder="Enter API key or leave blank to keep existing"
                />
              </div>
            </section>

            <section className="settings-section">
              <h2>🌐 Browser Configuration</h2>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={serverConfig.browser.headless}
                    onChange={(e) =>
                      handleServerConfigChange('browser', 'headless', e.target.checked)
                    }
                  />
                  <span className="checkbox-text">
                    <strong>Headless Mode</strong>
                    <span className="checkbox-description">
                      Run browser without visible window (faster but harder to debug)
                    </span>
                  </span>
                </label>
              </div>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={serverConfig.browser.disable_security}
                    onChange={(e) =>
                      handleServerConfigChange('browser', 'disable_security', e.target.checked)
                    }
                  />
                  <span className="checkbox-text">
                    <strong>Disable Security</strong>
                    <span className="checkbox-description">
                      Bypass CORS and CSP restrictions (recommended for automation)
                    </span>
                  </span>
                </label>
              </div>
            </section>

            <section className="settings-section">
              <h2>🎯 Agent Configuration</h2>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={serverConfig.agent.use_vision}
                    onChange={(e) =>
                      handleServerConfigChange('agent', 'use_vision', e.target.checked)
                    }
                  />
                  <span className="checkbox-text">
                    <strong>Use Vision</strong>
                    <span className="checkbox-description">
                      Enable screenshot analysis for better element understanding
                    </span>
                  </span>
                </label>
              </div>

              <div className="setting-group">
                <label htmlFor="agent-max-failures">
                  <span className="label-text">Max Failures</span>
                  <span className="label-description">
                    Maximum number of consecutive failures before stopping
                  </span>
                </label>
                <input
                  id="agent-max-failures"
                  type="number"
                  className="input-number"
                  min="1"
                  max="10"
                  value={serverConfig.agent.max_failures}
                  onChange={(e) =>
                    handleServerConfigChange('agent', 'max_failures', parseInt(e.target.value))
                  }
                />
              </div>

              <div className="setting-group">
                <label htmlFor="agent-max-steps">
                  <span className="label-text">Max Steps</span>
                  <span className="label-description">
                    Maximum number of steps the agent can take per task
                  </span>
                </label>
                <input
                  id="agent-max-steps"
                  type="number"
                  className="input-number"
                  min="10"
                  max="200"
                  value={serverConfig.agent.max_steps}
                  onChange={(e) =>
                    handleServerConfigChange('agent', 'max_steps', parseInt(e.target.value))
                  }
                />
              </div>
            </section>

            <div className="settings-actions">
              <button
                className="btn btn-secondary"
                onClick={loadServerConfig}
                disabled={configStatus === 'loading'}
              >
                {configStatus === 'loading' ? 'Reloading...' : 'Reload from Server'}
              </button>
              <button
                className={`btn btn-primary ${configStatus === 'saving' ? 'loading' : ''}`}
                onClick={saveServerConfig}
                disabled={configStatus === 'saving'}
              >
                {configStatus === 'saving' && 'Saving...'}
                {configStatus === 'saved' && '✓ Saved!'}
                {configStatus === 'error' && '✗ Error'}
                {configStatus === 'idle' && 'Save Server Configuration'}
              </button>
            </div>

            {configStatus === 'saved' && (
              <div className="save-message success">
                ✓ Server configuration saved successfully! Changes are now active.
              </div>
            )}
            {configStatus === 'error' && (
              <div className="save-message error">
                ✗ Failed to save server configuration. Please check your connection and try again.
              </div>
            )}
          </>
        )}
      </div>

      <footer className="options-footer">
        <p>Browser.AI Extension v1.0.0</p>
        <p>
          <a
            href="https://github.com/Sathursan-S/Browser.AI"
            target="_blank"
            rel="noopener noreferrer"
          >
            View Documentation
          </a>
        </p>
      </footer>
    </div>
  )
}

export default Options
