import React from 'react'
import { createRoot } from 'react-dom/client'
import { Overlay } from './Overlay'

// Create a container for the overlay
const container = document.createElement('div')
container.id = 'browser-ai-overlay-root'
// Ensure it's on top of everything and doesn't interfere with layout
container.style.position = 'fixed'
container.style.zIndex = '2147483647' // Max z-index
container.style.top = '0'
container.style.left = '0'
container.style.width = '0'
container.style.height = '0'
container.style.pointerEvents = 'none' // Allow clicks to pass through by default

document.body.appendChild(container)

const root = createRoot(container)
root.render(<Overlay />)

console.log('Browser.AI Overlay injected')
