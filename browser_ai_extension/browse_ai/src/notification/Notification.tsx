import { useEffect, useState } from 'react'

import './Notification.css'

interface NotificationData {
  type: 'user_interaction' | 'task_complete' | 'error'
  message: string
  details?: string
  result?: any
  timestamp: string
}

function Notification() {
  const [notification, setNotification] = useState<NotificationData | null>(null)
  const [show, setShow] = useState(false)

  useEffect(() => {
    // Get notification data from URL params
    const params = new URLSearchParams(window.location.search)
    const type = params.get('type') as NotificationData['type']
    const message = params.get('message') || ''
    const details = params.get('details') || ''
    const result = params.get('result') || ''
    const timestamp = params.get('timestamp') || new Date().toISOString()

    if (type && message) {
      let parsedResult = null
      if (result) {
        try {
          parsedResult = JSON.parse(decodeURIComponent(result))
        } catch (e) {
          console.error('Failed to parse result from URL:', e)
        }
      }
      setNotification({
        type,
        message,
        details,
        result: parsedResult,
        timestamp,
      })
      setShow(true)
    }

    // Listen for messages from background script
    const messageListener = (request: any) => {
      if (request.type === 'SHOW_NOTIFICATION') {
        setNotification(request.data)
        setShow(true)
      }
    }

    chrome.runtime.onMessage.addListener(messageListener)

    return () => {
      chrome.runtime.onMessage.removeListener(messageListener)
    }
  }, [])

  const handleClose = () => {
    setShow(false)
    setTimeout(() => window.close(), 300)
  }

  const handleOpenSidePanel = async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (tab?.windowId) {
        if ('sidePanel' in chrome) {
          await (chrome as any).sidePanel.open({ windowId: tab.windowId })
          handleClose()
        } else {
          console.error('Side panel API not available')
        }
      }
    } catch (error) {
      console.error('Failed to open side panel:', error)
    }
  }

  if (!notification) {
    return (
      <div className="notification-container">
        <div className="notification-loading">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  const getIcon = () => {
    switch (notification.type) {
      case 'user_interaction':
        return '⚠️'
      case 'task_complete':
        return '✅'
      case 'error':
        return '❌'
      default:
        return 'ℹ️'
    }
  }

  const getTitle = () => {
    switch (notification.type) {
      case 'user_interaction':
        return 'User Interaction Required'
      case 'task_complete':
        return 'Task Completed'
      case 'error':
        return 'Error Occurred'
      default:
        return 'Notification'
    }
  }

  return (
    <div className={`notification-container ${show ? 'show' : ''}`}>
      <div className={`notification-card ${notification.type}`}>
        <div className="notification-header">
          <div className="notification-icon">{getIcon()}</div>
          <h2 className="notification-title">{getTitle()}</h2>
          <button className="notification-close" onClick={handleClose}>
            ✕
          </button>
        </div>

        <div className="notification-body">
          <p className="notification-message">{notification.message}</p>
          {notification.details && (
            <div className="notification-details">
              <p>{notification.details}</p>
            </div>
          )}
          {notification.result && (
            <div className="notification-result">
              <h4>Result:</h4>
              <pre>{JSON.stringify(notification.result, null, 2)}</pre>
            </div>
          )}
        </div>

        <div className="notification-footer">
          <div className="notification-timestamp">
            {new Date(notification.timestamp).toLocaleString()}
          </div>
          <div className="notification-actions">
            {notification.type === 'user_interaction' && (
              <button className="btn-primary" onClick={handleOpenSidePanel}>
                Open Side Panel
              </button>
            )}
            <button className="btn-secondary" onClick={handleClose}>
              {notification.type === 'user_interaction' ? 'Dismiss' : 'Close'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Notification
