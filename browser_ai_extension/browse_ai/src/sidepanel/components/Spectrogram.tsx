import React, { useEffect, useRef } from 'react';
import './Spectrogram.css';

interface SpectrogramProps {
  isListening: boolean;
  isSpeaking: boolean;
}

const Spectrogram: React.FC<SpectrogramProps> = ({ isListening, isSpeaking }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const bars = 128;
    const barWidth = canvas.width / bars;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
      gradient.addColorStop(0, '#ff00ff');
      gradient.addColorStop(0.5, '#00ffff');
      gradient.addColorStop(1, '#ff00ff');
      ctx.fillStyle = gradient;

      if (isListening || isSpeaking) {
        for (let i = 0; i < bars; i++) {
          const barHeight = Math.random() * canvas.height;
          ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth, barHeight);
        }
      }
      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [isListening, isSpeaking]);

  return <canvas ref={canvasRef} className="spectrogram-canvas" />;
};

export default Spectrogram;
