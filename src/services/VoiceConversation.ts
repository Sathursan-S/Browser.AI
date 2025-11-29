/**
 * Voice Conversation Service
 *
 * Orchestrates a continuous, hands-free voice conversation similar to Gemini Live mode.
 * Handles automatic turn-taking between user speech and bot responses without manual intervention.
 */

import { textToSpeech } from './TextToSpeech'
import { voiceRecognition } from './VoiceRecognition'
import type { VoiceRecognitionResult } from './VoiceRecognition'

export interface VoiceConversationConfig {
  autoSendOnFinal?: boolean // Auto-send when user stops speaking
  silenceThreshold?: number // ms of silence before considering speech ended (default: 1500)
  autoRestartListening?: boolean // Restart listening after bot speaks
  interruptOnSpeech?: boolean // Allow user to interrupt bot
  language?: string // Speech recognition language
  speechRate?: number // TTS rate (0.1-10)
  speechPitch?: number // TTS pitch (0-2)
  speechVolume?: number // TTS volume (0-1)
}

export type ConversationState = 'idle' | 'listening' | 'processing' | 'speaking'

export interface ConversationStateInfo {
  state: ConversationState
  transcript?: string
  isInterim?: boolean
}

export type StateChangeCallback = (stateInfo: ConversationStateInfo) => void
export type MessageReadyCallback = (message: string) => void
export type ErrorCallback = (error: string) => void

export class VoiceConversationService {
  private config: Required<VoiceConversationConfig>
  private state: ConversationState = 'idle'
  private isActive: boolean = false
  private pendingTranscript: string = ''
  private finalTranscriptTimeout: NodeJS.Timeout | null = null

  // Callbacks
  private onStateChange: StateChangeCallback | null = null
  private onMessageReady: MessageReadyCallback | null = null
  private onError: ErrorCallback | null = null

  // Default configuration
  private static readonly DEFAULT_CONFIG: Required<VoiceConversationConfig> = {
    autoSendOnFinal: true,
    silenceThreshold: 1500,
    autoRestartListening: true,
    interruptOnSpeech: true,
    language: 'en-US',
    speechRate: 1.0,
    speechPitch: 1.0,
    speechVolume: 0.9,
  }

  constructor(config: VoiceConversationConfig = {}) {
    this.config = { ...VoiceConversationService.DEFAULT_CONFIG, ...config }
  }

  /**
   * Check if voice conversation is supported
   */
  public isSupported(): boolean {
    return voiceRecognition.isRecognitionSupported() && textToSpeech.isSynthesisSupported()
  }

  /**
   * Get current conversation state
   */
  public getState(): ConversationState {
    return this.state
  }

  /**
   * Check if conversation is active
   */
  public isConversationActive(): boolean {
    return this.isActive
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<VoiceConversationConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * Start voice conversation mode
   */
  public start(
    onStateChange: StateChangeCallback,
    onMessageReady: MessageReadyCallback,
    onError?: ErrorCallback,
  ): void {
    if (!this.isSupported()) {
      const error = 'Voice conversation not supported in this browser'
      if (onError) onError(error)
      throw new Error(error)
    }

    if (this.isActive) {
      console.warn('Voice conversation already active')
      return
    }

    console.log('🎙️ Starting voice conversation mode')
    this.isActive = true
    this.onStateChange = onStateChange
    this.onMessageReady = onMessageReady
    this.onError = onError || null

    // Initialize voice recognition
    voiceRecognition.initialize({
      continuous: true,
      interimResults: true,
      language: this.config.language,
    })

    // Start listening
    this.startListening()
  }

  /**
   * Stop voice conversation mode
   */
  public stop(): void {
    if (!this.isActive) return

    console.log('🎙️ Stopping voice conversation mode')
    this.isActive = false

    // Stop all ongoing activities
    this.stopListening()
    this.stopSpeaking()

    // Clear pending transcript
    this.pendingTranscript = ''
    if (this.finalTranscriptTimeout) {
      clearTimeout(this.finalTranscriptTimeout)
      this.finalTranscriptTimeout = null
    }

    // Update state
    this.updateState('idle')
  }

  /**
   * Handle bot response - speak it out and optionally restart listening
   */
  public handleBotResponse(message: string): void {
    if (!this.isActive) return

    console.log('🤖 Bot response received, speaking...')

    // Clean message for better speech
    const cleanText = this.cleanTextForSpeech(message)

    if (!cleanText) {
      // If no speakable content, just restart listening
      if (this.config.autoRestartListening) {
        this.startListening()
      }
      return
    }

    // Update state to speaking
    this.updateState('speaking')

    // Speak the response
    textToSpeech.speak(
      cleanText,
      {
        rate: this.config.speechRate,
        pitch: this.config.speechPitch,
        volume: this.config.speechVolume,
        lang: this.config.language,
      },
      undefined,
      () => {
        console.log('🔊 Finished speaking bot response')

        // After speaking, restart listening if configured
        if (this.isActive && this.config.autoRestartListening) {
          setTimeout(() => {
            this.startListening()
          }, 500) // Small delay before listening again
        } else if (this.isActive) {
          this.updateState('idle')
        }
      },
      (error) => {
        console.error('Speech error:', error)
        if (this.onError) this.onError(`Speech error: ${error}`)

        // On error, try to restart listening
        if (this.isActive && this.config.autoRestartListening) {
          this.startListening()
        }
      },
    )
  }

  /**
   * Manually trigger sending pending transcript
   */
  public sendPendingTranscript(): void {
    if (this.pendingTranscript.trim()) {
      this.sendMessage(this.pendingTranscript.trim())
      this.pendingTranscript = ''
    }
  }

  /**
   * Start listening for user speech
   */
  private startListening(): void {
    if (!this.isActive) return

    console.log('👂 Starting to listen...')
    this.updateState('listening')

    voiceRecognition.startListening(
      (result: VoiceRecognitionResult) => {
        this.handleRecognitionResult(result)
      },
      (error: string) => {
        console.error('Recognition error:', error)
        if (this.onError) this.onError(error)

        // On error, try to restart if still active
        if (this.isActive) {
          setTimeout(() => {
            if (this.isActive) {
              this.startListening()
            }
          }, 1000)
        }
      },
      () => {
        console.log('👂 Recognition ended')

        // If recognition ends but we're still active, restart
        if (this.isActive && this.state === 'listening') {
          setTimeout(() => {
            if (this.isActive && this.state === 'listening') {
              this.startListening()
            }
          }, 500)
        }
      },
    )
  }

  /**
   * Stop listening
   */
  private stopListening(): void {
    voiceRecognition.stopListening()

    if (this.finalTranscriptTimeout) {
      clearTimeout(this.finalTranscriptTimeout)
      this.finalTranscriptTimeout = null
    }
  }

  /**
   * Stop speaking
   */
  private stopSpeaking(): void {
    textToSpeech.stop()
  }

  /**
   * Handle speech recognition result
   */
  private handleRecognitionResult(result: VoiceRecognitionResult): void {
    if (!this.isActive) return

    // If user is speaking while bot is talking, interrupt if configured
    if (this.state === 'speaking' && this.config.interruptOnSpeech) {
      console.log('🚫 User interrupted bot speech')
      this.stopSpeaking()
      this.updateState('listening')
    }

    if (result.isFinal) {
      // Final transcript - add to pending
      console.log('✅ Final transcript:', result.transcript)
      this.pendingTranscript = (this.pendingTranscript + ' ' + result.transcript).trim()

      // Clear any existing timeout
      if (this.finalTranscriptTimeout) {
        clearTimeout(this.finalTranscriptTimeout)
      }

      // Set timeout to send after silence threshold
      if (this.config.autoSendOnFinal) {
        this.finalTranscriptTimeout = setTimeout(() => {
          if (this.pendingTranscript.trim()) {
            console.log('📤 Auto-sending after silence threshold')
            this.sendMessage(this.pendingTranscript.trim())
            this.pendingTranscript = ''
          }
        }, this.config.silenceThreshold)
      }

      // Notify with final transcript
      this.updateState('listening', { transcript: this.pendingTranscript, isInterim: false })
    } else {
      // Interim transcript - just display
      const fullTranscript = this.pendingTranscript
        ? `${this.pendingTranscript} ${result.transcript}`.trim()
        : result.transcript

      this.updateState('listening', { transcript: fullTranscript, isInterim: true })
    }
  }

  /**
   * Send message to the chatbot
   */
  private sendMessage(message: string): void {
    if (!this.onMessageReady) return

    console.log('📨 Sending message:', message)

    // Update state to processing
    this.updateState('processing')

    // Stop listening while processing
    this.stopListening()

    // Notify that message is ready to send
    this.onMessageReady(message)
  }

  /**
   * Update conversation state and notify listeners
   */
  private updateState(
    state: ConversationState,
    extra?: { transcript?: string; isInterim?: boolean },
  ): void {
    this.state = state

    if (this.onStateChange) {
      this.onStateChange({
        state,
        transcript: extra?.transcript,
        isInterim: extra?.isInterim,
      })
    }
  }

  /**
   * Clean text for better speech synthesis
   */
  private cleanTextForSpeech(text: string): string {
    return text
      .replace(/\*\*/g, '') // Remove bold markdown
      .replace(/#{1,6}\s/g, '') // Remove headers
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Remove links, keep text
      .replace(/```[\s\S]*?```/g, '') // Remove code blocks
      .replace(/`[^`]+`/g, '') // Remove inline code
      .replace(/[✅🚀👋🎧🤔❓💡📝🤖🎙️🔊👂📤🚫]/g, '') // Remove common emojis
      .replace(/\n+/g, '. ') // Convert newlines to pauses
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim()
  }

  /**
   * Cleanup resources
   */
  public cleanup(): void {
    this.stop()
    this.onStateChange = null
    this.onMessageReady = null
    this.onError = null
  }
}

// Export singleton instance
export const voiceConversation = new VoiceConversationService()
