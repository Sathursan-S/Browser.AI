import React from 'react'
import ReactDOM from 'react-dom/client'
import { SidePanel } from './SidePanel'
import { ThemeProvider } from '../utils/theme'
import './index.css'

ReactDOM.createRoot(document.getElementById('app') as HTMLElement).render(
  <React.StrictMode>
    <ThemeProvider>
      <SidePanel />
    </ThemeProvider>
  </React.StrictMode>,
)
