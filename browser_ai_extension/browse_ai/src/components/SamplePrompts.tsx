import React from 'react'
import { Card } from '../ui/Card'

interface SamplePrompt {
  icon: React.ReactNode
  title: string
  description: string
  prompt: string
}

interface SamplePromptsProps {
  onPromptSelect?: (prompt: string) => void
}

export const SamplePrompts: React.FC<SamplePromptsProps> = ({ onPromptSelect }) => {
  const samplePrompts: SamplePrompt[] = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "Get Page Info",
      description: "Extract page title and meta",
      prompt: "Get the page title, description, and main headings from this website"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
      title: "Find Element",
      description: "Search for specific elements",
      prompt: "Find and click the search button on this page"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
      ),
      title: "Fill Form",
      description: "Auto-fill form fields",
      prompt: "Fill out any forms on this page with sample data"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
      title: "Extract Data",
      description: "Scrape structured data",
      prompt: "Extract all product information from this e-commerce page"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
        </svg>
      ),
      title: "Test UI",
      description: "Validate page elements",
      prompt: "Test all buttons and links on this page to ensure they work properly"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "Monitor Changes",
      description: "Watch for page updates",
      prompt: "Monitor this page for any changes and notify me when content updates"
    }
  ]

  const handlePromptClick = (prompt: SamplePrompt) => {
    if (onPromptSelect) {
      onPromptSelect(prompt.prompt)
    }
  }

  return (
    <div className="grid grid-cols-3 gap-3">
      {samplePrompts.map((prompt, index) => (
        <Card 
          key={index}
          className="p-4 bg-white/10 backdrop-blur-sm border-white/20 hover:bg-white/15 transition-all duration-200 cursor-pointer group"
          onClick={() => handlePromptClick(prompt)}
        >
          <div className="flex flex-col items-center text-center space-y-2">
            <div className="text-white/80 group-hover:text-white transition-colors">
              {prompt.icon}
            </div>
            <h3 className="text-xs font-medium text-white/90 leading-tight">
              {prompt.title}
            </h3>
            <p className="text-xs text-white/60 leading-tight">
              {prompt.description}
            </p>
          </div>
        </Card>
      ))}
    </div>
  )
}

export default SamplePrompts