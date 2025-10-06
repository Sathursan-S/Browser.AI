import React from 'react'
import ReactDOM from 'react-dom/client'
import { DevTools } from './DevTools'
import './index.css'

const rootEl = document.getElementById('app')
if (!rootEl) {
  throw new Error(
    'DevTools panel root element #app not found. Ensure devtools.html includes this script as the panel UI.',
  )
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <DevTools />
  </React.StrictMode>,
)
