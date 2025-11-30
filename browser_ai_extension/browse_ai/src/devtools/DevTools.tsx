import React, { useState } from 'react'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import SamplePrompts from '../components/SamplePrompts'

export const DevTools = () => {
  const [selectedPrompt, setSelectedPrompt] = useState<string>('')
  const [showWelcome, setShowWelcome] = useState(true)

  const handlePromptSelect = (prompt: string) => {
    setSelectedPrompt(prompt)
    setShowWelcome(false)
    console.log('Selected prompt:', prompt)
    // Here you can integrate with your task execution logic
  }

  const handleGetStarted = () => {
    setShowWelcome(false)
  }

  if (showWelcome) {
    return (
      <main className="min-h-screen p-6 bg-gradient-to-br from-[#4338ca] via-[#6366f1] to-[#1e1b4b] text-white font-sans relative overflow-hidden">
        {/* Background gradient overlay to match screenshot */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#4338ca]/80 via-[#6366f1]/60 to-[#1e1b4b] -z-10" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(139,92,246,0.4)_0%,_transparent_50%)] -z-10" />
        
        <div className="max-w-md mx-auto relative z-10 flex flex-col h-screen justify-between">
          <div>
            <header className="flex items-center gap-3 mb-12 pt-4">
              <span className="text-lg font-bold">Browser.AI</span>
              <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
            </header>

            <div className="text-center mb-16">
              <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
                Good Morning !
              </h1>
              <p className="text-white/70 text-lg">Initializing your task, Hang tight!</p>
            </div>

            {/* Main content area spacer */}
            <div className="h-32 mb-8" />
          </div>

          <div className="space-y-6 pb-8">
            {/* Sample prompt cards */}
            <SamplePrompts onPromptSelect={handlePromptSelect} />

            <Button 
              variant="ghost" 
              className="w-full h-12 rounded-full bg-white/10 border border-white/20 hover:bg-white/15 text-white font-medium"
              onClick={handleGetStarted}
            >
              Get Started
            </Button>
          </div>
        </div>
      </main>
    )
  }

  // Main interface after welcome screen
  return (
    <main className="min-h-screen p-6 bg-gradient-to-br from-[#4338ca] via-[#6366f1] to-[#1e1b4b] text-white font-sans relative overflow-hidden">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#4338ca]/80 via-[#6366f1]/60 to-[#1e1b4b] -z-10" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(139,92,246,0.4)_0%,_transparent_50%)] -z-10" />
      
      <div className="max-w-4xl mx-auto relative z-10">
        <header className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold">Browser.AI</span>
            <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
          </div>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setShowWelcome(true)}
            className="text-white/60 hover:text-white"
          >
            ← Back to Welcome
          </Button>
        </header>

        {/* DevTools Content Area */}
        <div className="space-y-6">
          <Card className="p-6 bg-white/10 backdrop-blur-sm border-white/20">
            <h2 className="text-xl font-semibold mb-4 text-white">Browser Automation DevTools</h2>
            {selectedPrompt && (
              <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
                <p className="text-sm text-white/70">Selected Task:</p>
                <p className="text-white">{selectedPrompt}</p>
              </div>
            )}
            <p className="text-white/70">
              Use this panel to monitor and control browser automation tasks. 
              Select a sample prompt or create your own automation workflow.
            </p>
          </Card>

          <SamplePrompts onPromptSelect={handlePromptSelect} />
        </div>
      </div>
    </main>
  )
}

export default DevTools
