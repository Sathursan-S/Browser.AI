import React, { useState, useEffect, useRef } from 'react';
import Lottie from 'lottie-react';
import botHeadAnimation from '../../assets/bot-head.json';

export interface TaskStatusProps {
  isRunning: boolean;
  currentTask: string | null;
  isPaused?: boolean;
  onDismiss: () => void;
}

export const TaskStatus: React.FC<TaskStatusProps> = ({
  isRunning,
  currentTask,
  isPaused = false,
  onDismiss,
}: TaskStatusProps) => {
  const [isVisible, setIsVisible] = useState(isRunning);
  const taskStatusRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsVisible(isRunning);
  }, [isRunning]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (taskStatusRef.current && !taskStatusRef.current.contains(event.target as Node)) {
        setIsVisible(false);
        onDismiss();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onDismiss]);

  if (!isVisible || !currentTask) {
    return null;
  }

  return (
    <div ref={taskStatusRef} className="task-status-container">
      <div className="bot-head">
        <Lottie animationData={botHeadAnimation} loop={true} />
      </div>
      <div className="task-info">
        <div className={`status-badge ${isPaused ? 'paused' : 'running'}`}>
          {isPaused ? 'Paused' : 'Running'}
        </div>
        <div className="task-description">{currentTask}</div>
      </div>
      <button className="dismiss-btn" onClick={() => { setIsVisible(false); onDismiss(); }}>
        ✕
      </button>
    </div>
  );
};
