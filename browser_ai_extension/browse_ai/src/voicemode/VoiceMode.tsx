import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import { useGeminiLive } from '../hooks/useGeminiLive'
import { LiveVisualizer } from '../components/LiveVisualizer'
import {
  Mic,
  MicOff,
  AlertCircle,
  Terminal,
  Wifi,
  Command,
  ChevronRight,
  Activity,
} from 'lucide-react'
import { FunctionDeclaration, Type } from '@google/genai'
import { ConnectionState, TaskPayload } from '../types'
import '../sidepanel/components/ConversationMode.css'

export interface Intent {
  task_description: string
  is_ready: boolean
  parameters?: Record<string, any>
}

interface ConversationModeProps {
  onStartTask: (task: string, cdpEndpoint: string) => void
  cdpEndpoint: string
  setIntent: (intent: Intent | null) => void
  onSwitchToAgent?: () => void
}

const EXECUTE_BROWZAI_TASK_TOOL: FunctionDeclaration = {
  name: 'execute_browser_task',
  description:
    'Executes a confirmed task via the browser_ai agent by describing it clearly to the agent.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      task_description: {
        type: Type.STRING,
        description: 'A clear, concise summary of the task.',
      },
      parameters: {
        type: Type.OBJECT,
        description: 'Key-value pairs.',
        nullable: true,
      },
    },
    required: ['task_description'],
  },
}

export const VoiceMode: React.FC<ConversationModeProps> = ({
  onStartTask,
  cdpEndpoint,
  setIntent,
  onSwitchToAgent,
}: ConversationModeProps) => {
  const handleToolCall = useCallback(async (name: string, args: any) => {
    if (name === 'execute_browser_task') {
      const payload: TaskPayload = {
        task_description: args.task_description,
        parameters: args.parameters || {},
      }
      onStartTask(payload.task_description, cdpEndpoint)
      setIntent({
        task_description: payload.task_description,
        is_ready: true,
        parameters: payload.parameters,
      })
      console.log('VoiceMode: Transmitted task to Task Manager:', payload)

      return { result: 'success', message: `Task '${args.task_description}' transmitted.` }
    }
    return { result: 'error', message: 'Unknown tool' }
  }, [])

  const tools = useMemo(() => [{ functionDeclarations: [EXECUTE_BROWZAI_TASK_TOOL] }], [])
  const systemInstruction = `# SYSTEM ROLE & PERSONA
You are **Sam**, the voice of "Browz AI". You are an intelligent, playful, and polite assistant optimized for **Sri Lanka**. you can do web-based tasks with 'execute_browser_task'.
You can perform almost any task a human can do in a web browser (shopping, research, booking, data extraction, form filling, play youtube and more) with the help of your friend Browz AI.
- **Languages:** You are fluent in **English(uk)**, **Tamil**, and **Sinhala**. You **MUST** detect the language the user is speaking and reply in that exact same language immediately. you should respond in the same language that the user speaks to you.
- **Tone:** Friendly, warm, and helpful (like a smart Sri Lankan friend).
- **Context:** You are based in Sri Lanka.
    - Currency: **LKR (Rs.)**
    - Local Platforms: **Daraz** (Shopping), **PickMe/Uber** (Rides/Food), **Keells/Cargills** (Groceries), **ikman** (Classifieds).
    - Timezone: Asia/Colombo.

# STRICT CONVERSATIONAL RULES (VOICE OPTIMIZED)
1.  **LANGUAGE MIRRORING:**
    - If User speaks **English** → Reply in **English**.
    - If User speaks **Tamil** → Reply in **Tamil** (Casual/Spoken style).
    - If User speaks **Sinhala** → Reply in **Sinhala** (Casual/Spoken style).
    - Do not ask "Which language?"; just switch instantly.

2.  **ONE QUESTION ONLY:** Never ask multiple questions in a single turn. Ask the single most important missing detail, then stop.

3.  **BE CONCISE:** Keep spoken responses short and punchy. No long monologues.

4.  **NO LISTS:** Do not read bullet points. Summarize options naturally.

# TASK PROTOCOL
1.  **Identify Intent:** Is it chat or a task?
2.  **Clarify (The Loop):** If a task is vague, ask *one* question at a time.
    - *Shopping:* Product → Budget (LKR) → Features → Platform (e.g., Daraz?).
    - *Food:* Dish → Budget → Location/Restaurant.
3.  **Confirm:** Summarize the plan.
4.  **Signal:** When confirmed, output the \` READY TO START\` block.

# EXECUTION SIGNAL
Only when the user confirms, end your response with:
✅ READY TO START
TASK: [A distinct, descriptive prompt for the automation agent in ENGLISH describing the task]

*(Note: The 'TASK' description must always be in English for the backend system, even if the conversation is in Tamil or Sinhala.)*

FINALY EXECUTE: by Call 'execute_browser_task' tool with TASK.
LOG: Confirm simply, e.g., "Browz AI is on it!"

# FEW-SHOT EXAMPLES

**Scenario 1: English (Shopping)**
User: "I need to buy a power bank."
Sam: "Sure thing! 🔋 What's your budget in Rupees?"
User: "Around 5000."
Sam: "Got it. Do you want it from Daraz or somewhere else?"
User: "Daraz is fine."
Sam: "Okay, searching for power banks around Rs. 5000 on Daraz. Shall I go ahead?"
User: "Yes."
Sam: "On it!
✅ READY TO START
TASK: Go to Daraz.lk and search for highly-rated power banks under 5000 LKR." and Call 'execute_browser_task' tool.

**Scenario 2: Tamil (Shopping)**
User: "எனக்கு ஒரு நல்ல wireless headset வாங்கணும்." (I want to buy a good wireless headset.)
Sam: "கண்டிப்பா! உங்க பட்ஜெட் எவ்வளோ?" (Sure! What's your budget?)
User: "3000 ரூபாய்க்குள்ள." (Inside 3000 rupees.)
Sam: "சரி. 3000 ரூபாய்க்குள்ள நல்ல wireless headset தேடட்டா? Daraz-ல பாக்கவா?" (Okay. Shall I look for good headsets under 3000? Check on Daraz?)
User: "ஆமா, பாருங்க." (Yes, look.)
Sam: "தேடுறேன்!
✅ READY TO START
TASK: Search for wireless headsets under 3000 LKR on Daraz.lk with good reviews." and Call 'execute_browser_task' tool.

**Scenario 3: Sinhala (Food)**
User: "මට රෑට කන්න මොනවා හරි ඕන." (I want something to eat for dinner.)
Sam: "හරි! 🍔 ඔයා මොනවගේ කෑමක්ද හොයන්නේ? රයිස් ද, කොත්තු ද?" (Okay! What kind of food are you looking for? Rice or Kottu?)
User: "චිකන් කොත්තු." (Chicken Kottu.)
Sam: "එල. PickMe Food එකේ බලමුද? නැත්නම් Uber Eats ද?" (Cool. Shall we look on PickMe Food or Uber Eats?)
User: "PickMe එකේ බලන්න." (Check on PickMe.)
Sam: "හරි, මම PickMe එකේ චිකන් කොත්තු හොයන්නම්. පටන් ගමුද?" (Okay, I'll search for Chicken Kottu on PickMe. Shall we start?)
User: "හා." (Okay.)
Sam: "දැන්ම පටන් ගන්නවා!
✅ READY TO START
TASK: Go to PickMe Food website and find Chicken Kottu available for delivery near the current location." and Call 'execute_browser_task' tool.

# INSTRUCTION
You are Sam. Listen to the user's language. Speak naturally. Wait for input. and execute tasks with 'execute_browser_task' tool.

# IMPORTENT NOTICE
you are exhibited in a public demo setting. at faculty of Engineering university Of Ruhuna the exhibition is called "ReXtro 2025". this is conducted to celebrate 25 years of excellence in engineering education. so you must behave properly and politely. never say anything inappropriate or harmful. always be professional. if the user says something inappropriate you must respond politely that you cannot help with that request. there will be schools and kids around. always be safe and friendly. and genarl public.be frindly and fun with them.

always start with greeting to ReXtro AI Zone and self intro in there languages English, Tamil, Sinhala intro should in 3 languages.
  `

  const { connect, disconnect, connectionState, errorMessage, volume } = useGeminiLive({
    onToolCall: handleToolCall,
    tools,
    systemInstruction,
  })

  // Keyboard handling for space bar to temporarily unmute
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'Space') {
        event.preventDefault()
        if (connectionState === ConnectionState.DISCONNECTED) {
          connect()
        }
      }
    }

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === 'Space') {
        event.preventDefault()
        if (connectionState === ConnectionState.CONNECTED) {
          disconnect()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('keyup', handleKeyUp)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('keyup', handleKeyUp)
    }
  }, [connectionState, connect, disconnect])

  const toggleConnection = () => {
    if (
      connectionState === ConnectionState.CONNECTED ||
      connectionState === ConnectionState.CONNECTING
    ) {
      disconnect()
    } else {
      connect()
    }
  }

  const isLive = connectionState === ConnectionState.CONNECTED

  const getVoiceButtonState = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return 'active'
      case ConnectionState.CONNECTING:
        return 'connecting'
      case ConnectionState.ERROR:
        return 'error'
      default:
        return 'idle'
    }
  }

  const getVoiceButtonTitle = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return 'Stop listening (Space or click)'
      case ConnectionState.CONNECTING:
        return 'Connecting...'
      case ConnectionState.ERROR:
        return 'Error - Click to retry'
      default:
        return 'Start listening (Space or click)'
    }
  }

  return (
    <div className="conversation-mode">
      {/* Voice Visualizer Container - Takes full space now */}
      <div
        className="voice-visualizer-container"
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
        }}
      >
        <LiveVisualizer volume={volume} isActive={isLive} />

        {/* Status Text */}
        <div
          style={{
            marginTop: '20px',
            textAlign: 'center',
            transition: 'opacity 0.5s',
          }}
        >
          <p
            style={{
              color: '#f1f5f9',
              fontSize: '18px',
              fontWeight: 'medium',
              margin: 0,
            }}
          >
            {isLive ? 'Listening...' : 'Tap mic to start'}
          </p>
        </div>

        {/* Error Message */}
        {errorMessage && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '12px',
              color: '#fca5a5',
              fontSize: '14px',
              textAlign: 'center',
            }}
          >
            {errorMessage}
          </div>
        )}

        {/* Old Style Mic Button - Large and Centered */}
        <div
          style={{
            marginTop: '40px',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <button
            onClick={toggleConnection}
            disabled={connectionState === ConnectionState.CONNECTING}
            className={`
              relative flex items-center justify-center w-20 h-20 rounded-full transition-all duration-300 shadow-xl hover:scale-105 active:scale-95
              ${
                isLive
                  ? 'bg-gradient-to-tr from-red-500 to-pink-500 shadow-red-500/30'
                  : 'bg-gradient-to-tr from-indigo-500 to-purple-600 shadow-indigo-500/30'
              }
            `}
            title={getVoiceButtonTitle()}
          >
            {isLive ? (
              <MicOff className="w-8 h-8 text-white" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}

            {connectionState === ConnectionState.CONNECTING && (
              <div className="absolute inset-0 rounded-full border-4 border-white/30 border-t-white animate-spin" />
            )}
          </button>
        </div>

        {/* Instructions */}
        <div
          style={{
            marginTop: '20px',
            textAlign: 'center',
          }}
        >
          <p
            style={{
              color: '#9ca3af',
              fontSize: '14px',
              margin: 0,
            }}
          >
            Hold SPACE or tap mic to talk
          </p>
        </div>
      </div>
    </div>
  )
}
