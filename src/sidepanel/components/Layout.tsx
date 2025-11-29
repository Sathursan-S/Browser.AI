import React from 'react'
import { useTheme } from '../../utils/theme'

interface LayoutProps {
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { theme } = useTheme()

  return (
    <div className={`flex flex-col h-screen overflow-hidden transition-colors duration-200
      ${theme === 'dark' ? 'bg-slate-950 text-slate-50' : 'bg-white text-slate-900'}
    `}>
      {children}
    </div>
  )
}
