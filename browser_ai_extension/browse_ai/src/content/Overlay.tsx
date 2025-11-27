import React, { useEffect, useState } from 'react'

export const Overlay = () => {
  const [isVisible, setIsVisible] = useState(false)
  const [status, setStatus] = useState<string>('')
  const [isError, setIsError] = useState(false)

  useEffect(() => {
    const handleMessage = (request: any, sender: any, sendResponse: any) => {
      if (request.type === 'SHOW_OVERLAY_STATUS') {
        setIsVisible(true)
        setStatus(request.message)
        setIsError(request.isError || false)
      } else if (request.type === 'HIDE_OVERLAY') {
        setIsVisible(false)
      }
    }

    chrome.runtime.onMessage.addListener(handleMessage)

    return () => {
      chrome.runtime.onMessage.removeListener(handleMessage)
    }
  }, [])

  if (!isVisible) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        padding: '12px 20px',
        background: isError ? 'rgba(239, 68, 68, 0.9)' : 'rgba(37, 99, 235, 0.9)',
        backdropFilter: 'blur(8px)',
        borderRadius: '12px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        color: 'white',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: '14px',
        fontWeight: '500',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        pointerEvents: 'auto',
        animation: 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      {!isError && (
        <div
          style={{
            width: '8px',
            height: '8px',
            background: 'white',
            borderRadius: '50%',
            animation: 'pulse 2s infinite',
          }}
        />
      )}
      <span>{status}</span>
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
          100% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  )
}
