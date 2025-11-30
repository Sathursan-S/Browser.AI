/**
 * Voice Recognition Service
 * 
 * Provides speech-to-text  constructor() {
    // Check for browser support
    const SpeechRecognitionClass = 
      (window as any).SpeechRecognition || 
      (window as any).webkitSpeechRecognition

    if (SpeechRecognitionClass) {
      this.isSupported = true
      this.recognition = new SpeechRecognitionClass() as SpeechRecognition
      console.log('✅ Voice Recognition API is supported and initialized')
    } else {
      console.warn('❌ Speech Recognition API not supported in this browser')
      console.log('Available window properties:', Object.keys(window).filter(k => k.toLowerCase().includes('speech')))
    }
  }y using Web Speech API.
 * Handles microphone input, continuous recognition, and interim results.
 */

// Type declarations for Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null
  onend: ((this: SpeechRecognition, ev: Event) => any) | null
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null
  start(): void
  stop(): void
  abort(): void
}

declare var SpeechRecognition: {
  prototype: SpeechRecognition
  new(): SpeechRecognition
}

declare var webkitSpeechRecognition: {
  prototype: SpeechRecognition
  new(): SpeechRecognition
}

export interface VoiceRecognitionOptions {
  continuous?: boolean
  interimResults?: boolean
  language?: string
  maxAlternatives?: number
}

export interface VoiceRecognitionResult {
  transcript: string
  isFinal: boolean
  confidence: number
}

export type VoiceRecognitionCallback = (result: VoiceRecognitionResult) => void
export type VoiceRecognitionErrorCallback = (error: string) => void

export class VoiceRecognitionService {
  private recognition: SpeechRecognition | null = null
  private isSupported: boolean = false
  private isListening: boolean = false
  private onResultCallback: VoiceRecognitionCallback | null = null
  private onErrorCallback: VoiceRecognitionErrorCallback | null = null
  private onEndCallback: (() => void) | null = null

  constructor() {
    // Check if browser supports Web Speech API
    const SpeechRecognitionClass = 
      (window as any).SpeechRecognition || 
      (window as any).webkitSpeechRecognition

    if (SpeechRecognitionClass) {
      this.isSupported = true
      this.recognition = new SpeechRecognitionClass() as SpeechRecognition
    } else {
      console.warn('Speech Recognition API not supported in this browser')
    }
  }

  /**
   * Check if speech recognition is supported
   */
  public isRecognitionSupported(): boolean {
    return this.isSupported
  }

  /**
   * Check if currently listening
   */
  public getIsListening(): boolean {
    return this.isListening
  }

  /**
   * Initialize recognition with options
   */
  public initialize(options: VoiceRecognitionOptions = {}): void {
    if (!this.recognition) {
      throw new Error('Speech Recognition not supported')
    }

    // Set recognition parameters
    this.recognition.continuous = options.continuous ?? false
    this.recognition.interimResults = options.interimResults ?? true
    this.recognition.lang = options.language || 'en-US'
    this.recognition.maxAlternatives = options.maxAlternatives || 1

    // Setup event handlers
    this.setupEventHandlers()
  }

  /**
   * Setup event handlers for recognition
   */
  private setupEventHandlers(): void {
    if (!this.recognition) return

    this.recognition.onstart = () => {
      this.isListening = true
      console.log('Voice recognition started')
    }

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      const result = event.results[event.results.length - 1]
      const transcript = result[0].transcript
      const isFinal = result.isFinal
      const confidence = result[0].confidence

      if (this.onResultCallback) {
        this.onResultCallback({
          transcript,
          isFinal,
          confidence
        })
      }
    }

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Voice recognition error:', event.error)
      this.isListening = false

      let errorMessage = 'Unknown error'
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.'
          break
        case 'audio-capture':
          errorMessage = 'No microphone found. Please check your microphone.'
          break
        case 'not-allowed':
          errorMessage = 'Microphone access denied. Please allow microphone access.'
          break
        case 'network':
          errorMessage = 'Network error occurred. Please check your connection.'
          break
        case 'aborted':
          errorMessage = 'Speech recognition aborted.'
          break
        default:
          errorMessage = `Speech recognition error: ${event.error}`
      }

      if (this.onErrorCallback) {
        this.onErrorCallback(errorMessage)
      }
    }

    this.recognition.onend = () => {
      this.isListening = false
      console.log('Voice recognition ended')
      
      if (this.onEndCallback) {
        this.onEndCallback()
      }
    }
  }

  /**
   * Start listening for voice input
   */
  public startListening(
    onResult: VoiceRecognitionCallback,
    onError?: VoiceRecognitionErrorCallback,
    onEnd?: () => void
  ): void {
    if (!this.recognition) {
      const error = 'Speech Recognition not supported'
      if (onError) onError(error)
      throw new Error(error)
    }

    if (this.isListening) {
      console.warn('Already listening')
      return
    }

    this.onResultCallback = onResult
    this.onErrorCallback = onError || null
    this.onEndCallback = onEnd || null

    try {
      this.recognition.start()
    } catch (error) {
      console.error('Failed to start recognition:', error)
      if (this.onErrorCallback) {
        this.onErrorCallback('Failed to start voice recognition')
      }
    }
  }

  /**
   * Stop listening
   */
  public stopListening(): void {
    if (!this.recognition) return

    if (this.isListening) {
      try {
        this.recognition.stop()
      } catch (error) {
        console.error('Error stopping recognition:', error)
      }
    }
  }

  /**
   * Abort recognition immediately
   */
  public abort(): void {
    if (!this.recognition) return

    if (this.isListening) {
      try {
        this.recognition.abort()
      } catch (error) {
        console.error('Error aborting recognition:', error)
      }
    }
  }

  /**
   * Clean up resources
   */
  public cleanup(): void {
    this.stopListening()
    this.onResultCallback = null
    this.onErrorCallback = null
    this.onEndCallback = null
  }
}

// Export singleton instance
export const voiceRecognition = new VoiceRecognitionService()
