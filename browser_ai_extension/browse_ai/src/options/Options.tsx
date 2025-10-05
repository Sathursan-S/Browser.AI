import { useState, useEffect } from 'react'
import './Options.css'

interface Settings {
  serverUrl: string
  devMode: boolean
  autoReconnect: boolean
  maxLogs: number
  showNotifications: boolean
}

const DEFAULT_SETTINGS: Settings = {
  serverUrl: 'http://localhost:5000',
  devMode: false,
  autoReconnect: true,
  maxLogs: 1000,
  showNotifications: true,
}

export const Options = () => {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  // Load settings from Chrome storage
  useEffect(() => {
    chrome.storage.sync.get(['settings'], (result) => {
      if (result.settings) {
        setSettings({ ...DEFAULT_SETTINGS, ...result.settings })
      }
    })
  }, [])

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

  return (
    <div className="options-container">
      <header className="options-header">
        <h1>🤖 Browser.AI Settings</h1>
        <p className="subtitle">Configure your browser automation extension</p>
      </header>

      <div className="options-content">
        <section className="settings-section">
          <h2>🔌 Connection Settings</h2>
          
          <div className="setting-group">
            <label htmlFor="serverUrl">
              <span className="label-text">Server URL</span>
              <span className="label-description">
                The Browser.AI server endpoint (Python server)
              </span>
            </label>
            <input
              id="serverUrl"
              type="text"
              className="input-text"
              value={settings.serverUrl}
              onChange={(e) => handleChange('serverUrl', e.target.value)}
              placeholder="http://localhost:5000"
            />
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
          <button
            className="btn btn-secondary"
            onClick={handleReset}
          >
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
            {saveStatus === 'idle' && 'Save Settings'}
          </button>
        </div>

        {saveStatus === 'saved' && (
          <div className="save-message success">
            ✓ Settings saved successfully! Changes will apply on next connection.
          </div>
        )}
        {saveStatus === 'error' && (
          <div className="save-message error">
            ✗ Failed to save settings. Please try again.
          </div>
        )}
      </div>

      <footer className="options-footer">
        <p>Browser.AI Extension v1.0.0</p>
        <p>
          <a href="https://github.com/Sathursan-S/Browser.AI" target="_blank" rel="noopener noreferrer">
            View Documentation
          </a>
        </p>
      </footer>
    </div>
  )
}

export default Options
