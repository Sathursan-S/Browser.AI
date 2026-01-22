import { useState, useRef, useCallback, useEffect } from 'react'
import {
  GoogleGenAI,
  LiveServerMessage,
  Modality,
  FunctionDeclaration,
  Type,
  Tool,
} from '@google/genai'
import { ConnectionState } from '../types'
import { base64ToArrayBuffer, pcmToAudioBuffer } from '../utils/audioUtils'

// Helper to check if env is set
const API_KEY = import.meta.env.VITE_GEMINI_API_KEY || ''

interface UseGeminiLiveProps {
  onToolCall: (name: string, args: any) => Promise<any>
  systemInstruction?: string
  tools?: Tool[]
}

export const useGeminiLive = ({ onToolCall, systemInstruction, tools }: UseGeminiLiveProps) => {
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED,
  )
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [volume, setVolume] = useState<number>(0)

  // Audio Contexts and Nodes
  const inputAudioContextRef = useRef<AudioContext | null>(null)
  const outputAudioContextRef = useRef<AudioContext | null>(null)
  const inputSourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const workletNodeRef = useRef<AudioWorkletNode | null>(null)

  // Session Management
  const sessionPromiseRef = useRef<Promise<any> | null>(null)
  const nextStartTimeRef = useRef<number>(0)
  const scheduledSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set())

  // Keep the latest tool call handler available to the session without reconnection
  const onToolCallRef = useRef(onToolCall)
  useEffect(() => {
    onToolCallRef.current = onToolCall
  }, [onToolCall])

  const disconnect = useCallback(() => {
    if (inputAudioContextRef.current) {
      inputAudioContextRef.current.close()
      inputAudioContextRef.current = null
    }
    if (outputAudioContextRef.current) {
      outputAudioContextRef.current.close()
      outputAudioContextRef.current = null
    }

    // Stop all scheduled audio
    scheduledSourcesRef.current.forEach((source) => {
      try {
        source.stop()
      } catch (e) {
        /* ignore */
      }
    })
    scheduledSourcesRef.current.clear()
    nextStartTimeRef.current = 0

    // We can't explicitly "close" the session object easily without the reference returned by connect,
    // but closing the audio context effectively kills the stream processing.
    // Ideally, we would call session.close() if we stored the resolved session.

    setConnectionState(ConnectionState.DISCONNECTED)
    setVolume(0)
  }, [])

  const connect = useCallback(async () => {
    if (!API_KEY) {
      setErrorMessage('API Key is missing in environment variables.')
      setConnectionState(ConnectionState.ERROR)
      return
    }

    setConnectionState(ConnectionState.CONNECTING)
    setErrorMessage(null)

    try {
      const ai = new GoogleGenAI({ apiKey: API_KEY })

      // 1. Setup Input Audio (Microphone) -> 16kHz
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      inputAudioContextRef.current = new (window.AudioContext ||
        (window as any).webkitAudioContext)({ sampleRate: 16000 })
      inputSourceRef.current = inputAudioContextRef.current.createMediaStreamSource(stream)

      // Load AudioWorklet module
      await inputAudioContextRef.current.audioWorklet.addModule('/worklets/audio-processor.js')

      // Create AudioWorkletNode for streaming data
      workletNodeRef.current = new AudioWorkletNode(inputAudioContextRef.current, 'audio-processor')

      // Handle messages from worklet
      workletNodeRef.current.port.onmessage = (event) => {
        const { audioData, volume } = event.data
        setVolume(volume)

        // Send to Gemini
        sessionPromise.then((session) => {
          session.sendRealtimeInput({
            media: {
              mimeType: 'audio/pcm;rate=16000',
              data: audioData,
            },
          })
        })
      }

      inputSourceRef.current.connect(workletNodeRef.current)
      workletNodeRef.current.connect(inputAudioContextRef.current.destination)

      // 2. Setup Output Audio (Speaker) -> 24kHz
      outputAudioContextRef.current = new (window.AudioContext ||
        (window as any).webkitAudioContext)({ sampleRate: 24000 })
      nextStartTimeRef.current = outputAudioContextRef.current.currentTime

      // 3. Connect to Gemini Live
      const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          systemInstruction: systemInstruction,
          tools: [
            ...(tools || []),
            {
              googleSearch: {},
            },
          ],
        },
        callbacks: {
          onopen: () => {
            console.log('Gemini Live Connected')
            setConnectionState(ConnectionState.CONNECTED)
          },
          onmessage: async (message: LiveServerMessage) => {
            // Handle Tool Calls
            if (message.toolCall) {
              const responses: any[] = []
              for (const fc of message.toolCall?.functionCalls || []) {
                // if (!fc.name) continue
                try {
                  // Use the ref to ensure we call the latest version of the handler
                  const result = await onToolCallRef.current(fc.name || '', fc.args)
                  responses.push({
                    id: fc.id,
                    name: fc.name,
                    response: { result },
                  })
                } catch (err: any) {
                  console.error(`Error executing tool ${fc.name}:`, err)
                  responses.push({
                    id: fc.id,
                    name: fc.name,
                    response: { error: err.message },
                  })
                }
              }

              // Send tool response back
              sessionPromise.then((session) => {
                session.sendToolResponse({
                  functionResponses: responses,
                })
              })
            }

            // Handle Audio Output
            const base64Audio = message.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data
            if (base64Audio && outputAudioContextRef.current) {
              const ctx = outputAudioContextRef.current
              const rawData = base64ToArrayBuffer(base64Audio)
              const audioBuffer = pcmToAudioBuffer(rawData, ctx, 24000) // Live API outputs 24kHz

              // Schedule playback
              const source = ctx.createBufferSource()
              source.buffer = audioBuffer
              source.connect(ctx.destination)

              // Ensure smooth playback without gaps
              const now = ctx.currentTime
              // If we fell behind, reset start time to now
              if (nextStartTimeRef.current < now) {
                nextStartTimeRef.current = now
              }

              source.start(nextStartTimeRef.current)
              nextStartTimeRef.current += audioBuffer.duration

              scheduledSourcesRef.current.add(source)
              source.onended = () => {
                scheduledSourcesRef.current.delete(source)
              }
            }

            // Handle Interruption
            if (message.serverContent?.interrupted) {
              console.log('Interrupted by user')
              // Stop all currently playing sources
              scheduledSourcesRef.current.forEach((src) => {
                try {
                  src.stop()
                } catch (e) {}
              })
              scheduledSourcesRef.current.clear()
              nextStartTimeRef.current = outputAudioContextRef.current?.currentTime || 0
            }
          },
          onclose: (e) => {
            console.log('Gemini Live Closed', e)
            setConnectionState(ConnectionState.DISCONNECTED)
          },
          onerror: (err) => {
            console.error('Gemini Live Error', err)
            setErrorMessage('Connection error occurred.')
            setConnectionState(ConnectionState.ERROR)
            disconnect()
          },
        },
      })

      sessionPromiseRef.current = sessionPromise

      // Audio streaming is handled by AudioWorkletNode
    } catch (err: any) {
      console.error('Failed to connect:', err)
      setErrorMessage(err.message)
      setConnectionState(ConnectionState.ERROR)
    }
  }, [disconnect, systemInstruction, tools]) // Removed onToolCall from deps, using ref instead

  return { connect, disconnect, connectionState, errorMessage, volume }
}
