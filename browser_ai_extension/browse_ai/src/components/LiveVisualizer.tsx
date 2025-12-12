import React, { useEffect, useState } from 'react';

interface LiveVisualizerProps {
  volume: number; // 0 to 100
  isActive: boolean;
}

export const LiveVisualizer: React.FC<LiveVisualizerProps> = ({ volume, isActive }) => {
  // Smooth out the volume for the squish/stretch animation
  const [smoothVol, setSmoothVol] = useState(0);
  
  // Blink state
  const [isBlinking, setIsBlinking] = useState(false);

  useEffect(() => {
    // Lerp volume for smoothness
    const timeout = setTimeout(() => {
      setSmoothVol(prev => prev + (volume - prev) * 0.3);
    }, 16);
    return () => clearTimeout(timeout);
  }, [volume]);

  // Random blinking logic
  useEffect(() => {
    const blinkLoop = () => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 150);
      const nextBlink = Math.random() * 3000 + 2000; // Blink every 2-5 seconds
      setTimeout(blinkLoop, nextBlink);
    };
    const timer = setTimeout(blinkLoop, 2000);
    return () => clearTimeout(timer);
  }, []);

  // Calculate dynamic styles based on volume
  // When talking (volume up), the orb stretches vertically slightly and bounces
  const verticalScale = 1 + (smoothVol / 300); 
  const horizontalScale = 1 - (smoothVol / 600);
  const translateY = -(smoothVol / 5); // Move up slightly when loud

  return (
    <div className="relative flex items-center justify-center w-80 h-80">
      
      {/* 1. The Shadow (Grounding) */}
      <div 
        className="absolute bottom-10 w-32 h-6 bg-indigo-900/10 rounded-[100%] blur-md transition-all duration-100"
        style={{ 
          transform: `scale(${1 - (smoothVol/200)})`, // Shadow shrinks when orb jumps up
          opacity: isActive ? 0.6 : 0.3
        }}
      />

      {/* 2. The Main Orb Body */}
      <div 
        className={`
          relative w-56 h-56 rounded-full transition-all duration-300 ease-out
          ${isActive ? 'shadow-[0_20px_60px_-10px_rgba(124,58,237,0.5)]' : 'shadow-none opacity-50 grayscale'}
        `}
        style={{
          background: 'linear-gradient(135deg, #a78bfa 0%, #7c3aed 50%, #4c1d95 100%)',
          transform: isActive 
            ? `translateY(${translateY}px) scale(${horizontalScale}, ${verticalScale})` 
            : 'scale(0.9)',
        }}
      >
        {/* Inner Glow / Highlight (Top Left) */}
        <div className="absolute top-0 left-0 w-full h-full rounded-full opacity-60"
             style={{ background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 25%)' }} 
        />
        
        {/* Rim Light (Bottom Right) */}
        <div className="absolute inset-0 rounded-full opacity-40"
             style={{ boxShadow: 'inset -10px -10px 20px rgba(76, 29, 149, 0.5)' }} 
        />

        {/* 3. The Face Container */}
        <div className="absolute inset-0 flex items-center justify-center gap-6">
            
            {/* Left Eye */}
            <div 
              className="bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.8)] transition-all duration-75"
              style={{
                width: '18px',
                height: isBlinking ? '4px' : '42px', // Blink animation
                transform: `translateY(${isBlinking ? '10px' : '0px'})`,
                opacity: isActive ? 1 : 0
              }}
            />

            {/* Right Eye */}
            <div 
              className="bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.8)] transition-all duration-75"
              style={{
                width: '18px',
                height: isBlinking ? '4px' : '42px', // Blink animation
                transform: `translateY(${isBlinking ? '10px' : '0px'})`,
                opacity: isActive ? 1 : 0
              }}
            />
        </div>

      </div>

      {/* 4. Ambient Particle Ring (Optional, subtle magic dust) */}
      {isActive && (
        <div className="absolute inset-0 animate-spin-slow pointer-events-none">
           <div className="absolute top-10 left-10 w-2 h-2 bg-purple-400 rounded-full blur-[1px] animate-pulse" />
           <div className="absolute bottom-20 right-10 w-3 h-3 bg-indigo-300 rounded-full blur-[2px] animate-bounce" />
           <div className="absolute top-1/2 right-0 w-1 h-1 bg-pink-300 rounded-full blur-[1px]" />
        </div>
      )}

    </div>
  );
};