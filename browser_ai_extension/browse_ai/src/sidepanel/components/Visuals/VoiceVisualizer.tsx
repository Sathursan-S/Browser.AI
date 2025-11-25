import React, { useEffect, useRef } from 'react'

interface VoiceVisualizerProps {
  isListening: boolean
  isSpeaking: boolean
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ isListening, isSpeaking }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || 300
      canvas.height = canvas.parentElement?.clientHeight || 300
    }
    resize()
    window.addEventListener('resize', resize)

    let time = 0
    // Simulated frequency bars
    const bars = Array(20).fill(0)

    const draw = () => {
      if (!ctx || !canvas) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const centerX = canvas.width / 2
      const centerY = canvas.height / 2

      time += 0.05

      // Update bars based on state
      for(let i=0; i<bars.length; i++) {
        // Target height
        let target = 5 // Idle noise
        if (isListening) {
           // Create random movement mostly in the middle
           target = 20 + Math.random() * 80 * Math.sin(time + i)
        } else if (isSpeaking) {
           target = 30 + Math.random() * 50
        }

        // Smooth interpolation
        bars[i] += (target - bars[i]) * 0.2
      }

      // Draw Spectrum (Gemini Style - Center outwards)
      // We'll draw vertical rounded bars centered horizontally

      const barWidth = 12
      const gap = 6
      const totalWidth = bars.length * (barWidth + gap)
      let startX = centerX - totalWidth / 2

      // Gradient for bars
      const gradient = ctx.createLinearGradient(0, centerY - 100, 0, centerY + 100)
      gradient.addColorStop(0, '#3B82F6') // Blue
      gradient.addColorStop(0.5, '#A855F7') // Purple
      gradient.addColorStop(1, '#EC4899') // Pink

      ctx.fillStyle = gradient

      for(let i=0; i<bars.length; i++) {
        const h = bars[i]

        // Draw rounded rect
        ctx.beginPath()
        ctx.roundRect(startX + i * (barWidth + gap), centerY - h/2, barWidth, h, 6)
        ctx.fill()
      }

      // Optional: Add a subtle glow behind
      if (isListening || isSpeaking) {
        ctx.shadowColor = 'rgba(168, 85, 247, 0.5)'
        ctx.shadowBlur = 20
        // Redraw to apply shadow (optimized: usually do this in separate pass but for simple viz it's ok)
      } else {
        ctx.shadowBlur = 0
      }

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
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-slate-950 to-slate-950" />
      <canvas ref={canvasRef} className="relative z-10 w-full h-full" />

      {/* Overlay Text */}
      <div className="absolute bottom-12 left-0 right-0 text-center z-20">
        <p className={`text-lg font-medium transition-opacity duration-300 ${isListening || isSpeaking ? 'opacity-100' : 'opacity-60'} text-white`}>
          {isSpeaking ? "Speaking..." : isListening ? "Listening..." : "Tap mic to speak"}
        </p>
      </div>
    </div>
  )
}
