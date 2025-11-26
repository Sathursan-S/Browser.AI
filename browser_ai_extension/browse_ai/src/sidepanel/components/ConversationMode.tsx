import { useState, useEffect, useRef } from 'react';
import './ConversationMode.css';
import { textToSpeech } from '../../services/TextToSpeech';
import { voiceRecognition } from '../../services/VoiceRecognition';
import {
  voiceConversation,
  type ConversationState,
  type ConversationStateInfo,
} from '../../services/VoiceConversation';
import { VoiceVisualizer } from 'react-voice-visualizer';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface Intent {
  task_description: string;
  is_ready: boolean;
  confidence: number;
}

interface ConversationModeProps {
  socket: any;
  connected: boolean;
  onStartTask: (task: string, cdpEndpoint: string) => void;
  cdpEndpoint: string;
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  intent: Intent | null;
  setIntent: (intent: Intent | null) => void;
  onSwitchToAgent?: () => void;
}

export const ConversationMode = ({
  socket,
  connected,
  onStartTask,
  cdpEndpoint,
  messages,
  setMessages,
  intent,
  setIntent,
  onSwitchToAgent,
}: ConversationModeProps) => {
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeechEnabled, setIsSpeechEnabled] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const [isLiveVoiceMode, setIsLiveVoiceMode] = useState(false);
  const [conversationState, setConversationState] =
    useState<ConversationState>('idle');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [audioData, setAudioData] = useState<Uint8Array | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastSpokenIndexRef = useRef<number>(-1);
  const isWaitingForResponseRef = useRef<boolean>(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!isSpeechEnabled || !textToSpeech.isSynthesisSupported()) return;

    const assistantMessages = messages.filter((m) => m.role === 'assistant');
    const lastMessageIndex = assistantMessages.length - 1;

    if (
      lastMessageIndex > lastSpokenIndexRef.current &&
      lastMessageIndex >= 0
    ) {
      const newMessage = assistantMessages[lastMessageIndex];
      const cleanText = newMessage.content
        .replace(/\*\*/g, '')
        .replace(/#{1,6}\s/g, '')
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
        .replace(/✅|🚀|👋|🎧|🤔|❓/g, '')
        .trim();

      if (cleanText) {
        setIsSpeaking(true);
        textToSpeech.speak(
          cleanText,
          { rate: 1.0, pitch: 1.0, volume: 0.9 },
          undefined,
          () => {
            setIsSpeaking(false);
          },
          (error) => {
            console.error('Speech error:', error);
            setIsSpeaking(false);
          }
        );
      }

      lastSpokenIndexRef.current = lastMessageIndex;
    }
  }, [messages, isSpeechEnabled]);

  useEffect(() => {
    return () => {
      textToSpeech.stop();
      voiceRecognition.cleanup();
      voiceConversation.cleanup();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!isLiveVoiceMode || !messages.length) return;

    const lastMessage = messages[messages.length - 1];

    if (lastMessage.role === 'assistant' && isWaitingForResponseRef.current) {
      isWaitingForResponseRef.current = false;
      setIsProcessing(false);
      voiceConversation.handleBotResponse(lastMessage.content);
    }
  }, [messages, isLiveVoiceMode]);

  useEffect(() => {
    const isSupported = voiceRecognition.isRecognitionSupported();
    if (isSupported) {
      voiceRecognition.initialize({
        continuous: false,
        interimResults: true,
        language: 'en-US',
      });
    }
  }, []);

  useEffect(() => {
    if (!socket) return;

    const handleChatResponse = (data: {
      role: string;
      content: string;
      intent?: Intent;
    }) => {
      setIsProcessing(false);
      const message: Message = {
        role: data.role as 'user' | 'assistant',
        content: data.content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, message]);
      if (data.intent && data.intent.is_ready) {
        setIntent(data.intent);
      }
    };

    const handleConversationReset = (data: {
      role: string;
      content: string;
    }) => {
      setMessages([
        {
          role: data.role as 'assistant',
          content: data.content,
          timestamp: new Date().toISOString(),
        },
      ]);
      setIntent(null);
    };

    const handleAgentNeedsHelp = (data: {
      reason: string;
      summary: string;
      attempted_actions: string[];
      duration: number;
      suggestion: string;
    }) => {
      const helpMessage: Message = {
        role: 'assistant',
        content: data.summary,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, helpMessage]);
      setIsProcessing(false);
    };

    socket.on('chat_response', handleChatResponse);
    socket.on('conversation_reset', handleConversationReset);
    socket.on('agent_needs_help', handleAgentNeedsHelp);

    if (connected && messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content:
            "👋 Hi! I'm your Browser.AI assistant. What would you like me to help you automate today?",
          timestamp: new Date().toISOString(),
        },
      ]);
    }

    return () => {
      socket.off('chat_response', handleChatResponse);
      socket.off('conversation_reset', handleConversationReset);
      socket.off('agent_needs_help', handleAgentNeedsHelp);
    };
  }, [socket, connected, setMessages, setIntent]);

  const setupAudioVisualizer = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);
      visualize();
    } catch (err) {
      console.error('Error setting up audio visualizer:', err);
    }
  };

  const visualize = () => {
    if (analyserRef.current && dataArrayRef.current) {
      analyserRef.current.getByteTimeDomainData(dataArrayRef.current);
      setAudioData(new Uint8Array(dataArrayRef.current));
      animationFrameRef.current = requestAnimationFrame(visualize);
    }
  };

  const handleSendMessage = () => {
    if (!input.trim() || !connected || isProcessing) return;
    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsProcessing(true);
    const lastMessage = messages[messages.length - 1];
    const isHelpRequest =
      lastMessage &&
      lastMessage.content.includes('🤔 **The agent appears to be stuck**');
    if (isHelpRequest) {
      socket.emit('user_help_response', { response: input.trim() });
    } else {
      socket.emit('chat_message', { message: input.trim() });
    }
    setInput('');
  };

  const handleStartAutomation = () => {
    if (!intent) return;
    socket.emit('start_clarified_task', {
      task: intent.task_description,
      cdp_endpoint: cdpEndpoint,
      is_extension: true,
    });
    setIntent(null);
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: '🚀 Perfect! Starting the automation now...',
        timestamp: new Date().toISOString(),
      },
    ]);
  };

  const toggleLiveVoiceMode = () => {
    if (!voiceConversation.isSupported()) {
      setVoiceError(
        'Live voice mode requires both microphone and speaker support'
      );
      return;
    }
    if (isLiveVoiceMode) {
      voiceConversation.stop();
      setIsLiveVoiceMode(false);
      setConversationState('idle');
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    } else {
      setVoiceError(null);
      setIsLiveVoiceMode(true);
      if (isListening) {
        voiceRecognition.stopListening();
        setIsListening(false);
      }
      setupAudioVisualizer();
      voiceConversation.start(
        (stateInfo: ConversationStateInfo) => {
          setConversationState(stateInfo.state);
          if (stateInfo.transcript) {
            setLiveTranscript(stateInfo.transcript);
          }
        },
        (message: string) => {
          const userMessage: Message = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, userMessage]);
          setIsProcessing(true);
          isWaitingForResponseRef.current = true;
          setLiveTranscript('');
          socket.emit('chat_message', { message });
        },
        (error: string) => {
          setVoiceError(error);
        }
      );
    }
  };

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';
    return (
      <div
        key={index}
        className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}
      >
        <div
          className={`message-bubble ${
            isUser ? 'user-message' : 'assistant-message'
          }`}
        >
          <div className="message-text">{message.content}</div>
        </div>
      </div>
    );
  };

  return (
    <div className="conversation-mode">
      {isLiveVoiceMode && (
        <div className="live-voice-overlay">
          <div className="listening-indicator">
            {conversationState === 'listening' && 'Listening...'}
            {conversationState === 'processing' && 'Processing...'}
            {conversationState === 'speaking' && 'Speaking...'}
          </div>
          <VoiceVisualizer
            audioData={audioData || new Uint8Array(0)}
            className="voice-visualizer"
            mainBarColor="#4F46E5"
            secondaryBarColor="#A5B4FC"
            barWidth={4}
            gap={2}
          />
          <div className="live-transcript">{liveTranscript}</div>
          <button onClick={toggleLiveVoiceMode} className="exit-live-btn">
            Exit
          </button>
        </div>
      )}

      <div className="messages-container">
        {messages.map((msg, idx) => renderMessage(msg, idx))}
        {isProcessing && (
          <div className="message-wrapper assistant">
            <div className="message-bubble assistant-message typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {intent && intent.is_ready && (
        <div className="intent-confirmation">
          <button
            className="start-automation-btn"
            onClick={handleStartAutomation}
            disabled={!connected}
          >
            Start Automation
          </button>
        </div>
      )}

      <div className="input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Type your message..."
          rows={1}
        />
        <button
          className="action-btn voice-btn"
          onClick={toggleLiveVoiceMode}
          title="Toggle Live Voice Mode"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
          </svg>
        </button>
        <button
          className="action-btn send-btn"
          onClick={handleSendMessage}
          disabled={!input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
};
