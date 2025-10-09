import React from 'react'

interface CustomScrollProps {
  children: React.ReactNode
  className?: string
  maxHeight?: string
}

export const CustomScroll: React.FC<CustomScrollProps> = ({ 
  children, 
  className = '', 
  maxHeight = '100%' 
}) => {
  const scrollRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const scrollElement = scrollRef.current
    if (!scrollElement) return

    // Add custom scrollbar styles via JavaScript
    const styleSheet = document.createElement('style')
    styleSheet.textContent = `
      .custom-scroll::-webkit-scrollbar {
        width: 8px;
      }
      
      .custom-scroll::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
      }
      
      .custom-scroll::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        transition: background-color 0.2s ease;
      }
      
      .custom-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
      }
      
      .custom-scroll::-webkit-scrollbar-corner {
        background: transparent;
      }
    `
    
    if (!document.head.querySelector('#custom-scroll-styles')) {
      styleSheet.id = 'custom-scroll-styles'
      document.head.appendChild(styleSheet)
    }

    return () => {
      const existingStyle = document.head.querySelector('#custom-scroll-styles')
      if (existingStyle && existingStyle === styleSheet) {
        document.head.removeChild(styleSheet)
      }
    }
  }, [])

  return (
    <div 
      className={`relative overflow-hidden ${className}`}
      style={{ maxHeight }}
    >
      <div 
        ref={scrollRef}
        className="custom-scroll overflow-y-auto overflow-x-hidden h-full pr-1"
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05)',
        }}
      >
        {children}
      </div>
    </div>
  )
}

export default CustomScroll