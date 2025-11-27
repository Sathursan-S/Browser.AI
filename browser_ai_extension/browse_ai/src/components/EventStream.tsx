import React, { useEffect, useState } from 'react';
import { socket } from '../services/socket';

interface AgentEvent {
  topic: string;
  name: string;
  timestamp: number;
  [key: string]: any;
}

const EventStream: React.FC = () => {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    const handleAgentEvent = (event: AgentEvent) => {
      setEvents((prevEvents) => [...prevEvents, event]);
    };

    socket.on('agent_event', handleAgentEvent);

    return () => {
      socket.off('agent_event', handleAgentEvent);
    };
  }, []);

  return (
    <div className="event-stream">
      <h2>Event Stream</h2>
      <ul>
        {events.map((event, index) => (
          <li key={index}>
            <strong>{event.name}</strong> ({event.topic})
            <pre>{JSON.stringify(event, null, 2)}</pre>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EventStream;
