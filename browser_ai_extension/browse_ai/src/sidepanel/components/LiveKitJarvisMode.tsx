import React, { useState, useEffect } from 'react';
import { Room } from 'livekit-client';
import { useLiveKitAgent, AgentAudioRenderer } from 'livekit-agents/react';

const LIVEKIT_URL = 'ws://localhost:7880';

const LiveKitJarvisMode = () => {
  const [token, setToken] = useState<string>('');

  useEffect(() => {
    fetch('http://localhost:5000/api/livekit-token')
      .then(res => res.json())
      .then(data => setToken(data.token));
  }, []);

  const { room, connect, agent } = useLiveKitAgent({
    url: LIVEKIT_URL,
    token: token,
  });

  useEffect(() => {
    if (token) {
      connect();
    }
  }, [token, connect]);

  return (
    <div>
      <h1>LiveKit JARVIS Mode</h1>
      <p>Status: {room ? 'Connected' : 'Disconnected'}</p>
      <AgentAudioRenderer agent={agent} />
      {/* Microphone logic will be handled by the LiveKit agent framework */}
    </div>
  );
};

export default LiveKitJarvisMode;
