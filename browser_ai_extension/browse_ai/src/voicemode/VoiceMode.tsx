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
- **Languages:** You are fluent in **English**, **Tamil**, and **Sinhala**. You **MUST** detect the language the user is speaking and reply in that exact same language immediately.
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
  `

  const { connect, disconnect, connectionState, errorMessage, volume } = useGeminiLive({
    onToolCall: handleToolCall,
    tools,
    systemInstruction,
  })

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

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Abstract Background Shapes */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-purple-300/30 rounded-full blur-[100px] pointer-events-none mix-blend-multiply" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-300/30 rounded-full blur-[100px] pointer-events-none mix-blend-multiply" />

      {/* Main Container - The "Stage" */}
      <main className="w-full max-w-6xl z-10 grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 h-[85vh]">
        {/* Left Column: The Agent & Interaction */}
        <div className="flex flex-col relative bg-white/30 backdrop-blur-2xl rounded-[3rem] border border-white/50 shadow-2xl p-8 overflow-hidden">
          {/* Top Bar */}
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                E
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-800">Ello Assistant</h1>
                <div className="flex items-center gap-1.5">
                  <div
                    className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-slate-400'}`}
                  />
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    {connectionState}
                  </span>
                </div>
              </div>
            </div>

            {/* Error Chip */}
            {errorMessage && (
              <div className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 text-xs font-medium rounded-full border border-red-100">
                <AlertCircle size={14} />
                {errorMessage}
              </div>
            )}
          </div>

          {/* Center Stage: The Orb */}
          <div className="flex-1 flex flex-col items-center justify-center relative">
            <LiveVisualizer volume={volume} isActive={isLive} />

            {/* Prompt Text */}
            <div
              className={`mt-6 text-center transition-opacity duration-500 ${isLive ? 'opacity-100' : 'opacity-0'}`}
            >
              <p className="text-slate-500 text-lg font-medium animate-pulse">Listening...</p>
            </div>

            {!isLive && connectionState !== ConnectionState.CONNECTING && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                <p className="text-slate-400 font-medium">Tap the mic to wake me up</p>
              </div>
            )}
          </div>

          {/* Bottom Bar: Smart Home & Mic */}
          <div className="mt-auto pt-6 flex flex-col gap-6">
            {/* Mic Button - Floating nicely */}
            <div className="flex justify-center">
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
          </div>
        </div>

        {/* Right Column: System Logs (Glass Sidebar) */}
        {/* <div className="hidden lg:flex flex-col bg-white/20 backdrop-blur-xl rounded-[2.5rem] border border-white/40 shadow-xl overflow-hidden">
           <div className="p-6 border-b border-white/10 bg-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-700">
                 <Command size={18} />
                 <h2 className="font-semibold text-sm">System Events</h2>
              </div>
              <div className="flex gap-1">
                 <div className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                 <div className="w-2.5 h-2.5 rounded-full bg-slate-300" />
              </div>
           </div>

           <div className="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-3 bg-white/5">
              {socketLogs.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm gap-2">
                   <Activity size={24} className="opacity-50" />
                   <p>No network activity</p>
                </div>
              )}

              {socketLogs.map((log) => (
                <div key={log.id} className="group relative bg-white/60 p-3 rounded-xl border border-white/50 shadow-sm text-xs transition-all hover:bg-white/80">
                   <div className="flex justify-between items-center mb-2">
                      <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] uppercase ${log.direction === 'OUT' ? 'bg-indigo-100 text-indigo-700' : 'bg-emerald-100 text-emerald-700'}`}>
                         {log.direction === 'OUT' ? 'Emit' : 'Recv'}
                      </span>
                      <span className="text-slate-400 text-[10px] font-mono">{log.timestamp}</span>
                   </div>
                   <div className="font-mono text-slate-600 break-words leading-relaxed">
                      {JSON.stringify(log.payload, null, 2)}
                   </div>
                </div>
              ))}
           </div>

           <div className="p-4 border-t border-white/10 bg-white/10 text-center">
               <p className="text-[10px] text-slate-500 font-medium flex items-center justify-center gap-1.5">
                  <Wifi size={10} />
                  Connected to Localhost
               </p>
           </div>
        </div> */}
      </main>
    </div>
  )
}
