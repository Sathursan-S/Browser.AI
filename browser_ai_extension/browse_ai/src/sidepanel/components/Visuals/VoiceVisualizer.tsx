import React, { useEffect, useRef } from 'react'

interface VoiceVisualizerProps {
  isListening: boolean
  isSpeaking: boolean // For when the agent is "talking" (future proofing)
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ isListening, isSpeaking }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || 300
      canvas.height = canvas.parentElement?.clientHeight || 300
    }
    resize()
    window.addEventListener('resize', resize)

    let time = 0

    const draw = () => {
      if (!ctx || !canvas) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const centerX = canvas.width / 2
      const centerY = canvas.height / 2

      // Base Orb
      const baseRadius = 40

      // Animation logic
      // If listening: Pulse actively and show "receiving" waves
      // If idle: Slow breathe

      const pulseSpeed = isListening ? 0.1 : 0.02
      const pulseAmount = isListening ? 10 : 5

      time += pulseSpeed

      // Core Glow
      const gradient = ctx.createRadialGradient(centerX, centerY, baseRadius * 0.5, centerX, centerY, baseRadius * 2)
      gradient.addColorStop(0, isListening ? 'rgba(59, 130, 246, 0.8)' : 'rgba(99, 102, 241, 0.6)') // Blue/Indigo
      gradient.addColorStop(0.5, isListening ? 'rgba(59, 130, 246, 0.2)' : 'rgba(99, 102, 241, 0.1)')
      gradient.addColorStop(1, 'transparent')

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 3, 0, Math.PI * 2)
      ctx.fill()

      // Jarvis-style Rings (Rotating)
      ctx.save()
      ctx.translate(centerX, centerY)

      // Ring 1
      ctx.rotate(time)
      ctx.beginPath()
      ctx.arc(0, 0, baseRadius + Math.sin(time) * 5, 0, Math.PI * 1.5)
      ctx.strokeStyle = isListening ? '#60A5FA' : '#818CF8'
      ctx.lineWidth = 2
      ctx.stroke()

      // Ring 2 (Counter rotate)
      ctx.rotate(-time * 1.5)
      ctx.beginPath()
      ctx.arc(0, 0, baseRadius + 15 + Math.cos(time) * 5, 0, Math.PI * 1.2)
      ctx.strokeStyle = isListening ? '#3B82F6' : '#6366F1'
      ctx.lineWidth = 2
      ctx.stroke()

      // Ring 3 (Outer details)
      if (isListening) {
        ctx.rotate(time * 2)
        for(let i=0; i<3; i++) {
           ctx.rotate((Math.PI * 2) / 3)
           ctx.beginPath()
           ctx.arc(baseRadius + 30, 0, 2, 0, Math.PI * 2)
           ctx.fillStyle = '#93C5FD'
           ctx.fill()
        }
      }

      ctx.restore()

      // Center Core
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius + Math.sin(time * 2) * pulseAmount, 0, Math.PI * 2)
      ctx.fillStyle = isListening ? '#EFF6FF' : '#EEF2FF'
      ctx.shadowColor = isListening ? '#3B82F6' : '#6366F1'
      ctx.shadowBlur = 20
      ctx.fill()
      ctx.shadowBlur = 0

      animationRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      window.removeEventListener('resize', resize)
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
    }
  }, [isListening, isSpeaking])

  return (
    <div className="w-full h-full flex items-center justify-center relative overflow-hidden bg-slate-950 rounded-2xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-950 to-slate-950" />
      <canvas ref={canvasRef} className="relative z-10 w-full h-full max-w-[400px] max-h-[400px]" />

      {/* Overlay Text */}
      <div className="absolute bottom-8 left-0 right-0 text-center z-20">
        <p className={`text-lg font-medium transition-opacity duration-300 ${isListening ? 'opacity-100' : 'opacity-60'} text-white`}>
          {isListening ? "Listening..." : "Tap mic to speak"}
        </p>
      </div>
    </div>
  )
}
