import { useState, useEffect } from 'react';
import { ConversationMode, Message } from './components/ConversationMode';
import { TaskStatus } from './components/TaskStatus';
import { io, Socket } from 'socket.io-client';

const SidePanel = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => {
    const savedMessages = sessionStorage.getItem('chatMessages');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [intent, setIntent] = useState(null);
  const [taskStatus, setTaskStatus] = useState({
    isRunning: false,
    currentTask: null,
    isPaused: false,
  });

  useEffect(() => {
    sessionStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    const newSocket = io('http://localhost:3000');
    setSocket(newSocket);

    newSocket.on('connect', () => {
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
    });

    newSocket.on('status', (status) => {
      setTaskStatus(status);
      if (!status.isRunning) {
        setTimeout(() => {
          setTaskStatus({ isRunning: false, currentTask: null, isPaused: false });
          setMessages([]);
        }, 3000);
      }
    });

    return () => {
      newSocket.close();
    };
  }, []);

  const handleStartTask = (task: string, cdpEndpoint: string) => {
    socket?.emit('start_task', { task, cdpEndpoint });
  };

  const handleDismissTask = () => {
    setTaskStatus({ isRunning: false, currentTask: null, isPaused: false });
    setMessages([]);
  };

  return (
    <div style={{ width: '350px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TaskStatus
        isRunning={taskStatus.isRunning}
        currentTask={taskStatus.currentTask}
        isPaused={taskStatus.isPaused}
        onDismiss={handleDismissTask}
      />
      <ConversationMode
        socket={socket}
        connected={connected}
        onStartTask={handleStartTask}
        cdpEndpoint=""
        messages={messages}
        setMessages={setMessages}
        intent={intent}
        setIntent={setIntent}
      />
    </div>
  );
};

export default SidePanel;
