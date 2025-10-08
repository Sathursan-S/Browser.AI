/**
 * Text-to-Speech Service
 * 
 * Provides text-to-speech functionality using Web Speech API.
 * Handles speech synthesis with customizable voice, rate, pitch, and volume.
 */

export interface TextToSpeechOptions {
  voice?: SpeechSynthesisVoice
  rate?: number // 0.1 to 10 (default: 1)
  pitch?: number // 0 to 2 (default: 1)
  volume?: number // 0 to 1 (default: 1)
  lang?: string
}

export interface SpeechProgress {
  charIndex: number
  charLength: number
  elapsedTime: number
}

export type SpeechProgressCallback = (progress: SpeechProgress) => void
export type SpeechEndCallback = () => void
export type SpeechErrorCallback = (error: string) => void

export class TextToSpeechService {
  private synthesis: SpeechSynthesis | null = null
  private isSupported: boolean = false
  private isSpeaking: boolean = false
  private isPaused: boolean = false
  private currentUtterance: SpeechSynthesisUtterance | null = null
  private availableVoices: SpeechSynthesisVoice[] = []

  constructor() {
    // Check if browser supports Web Speech API
    if ('speechSynthesis' in window) {
      this.isSupported = true
      this.synthesis = window.speechSynthesis
      
      // Load available voices
      this.loadVoices()
      
      // Some browsers load voices asynchronously
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => {
          this.loadVoices()
        }
      }
    } else {
      console.warn('Speech Synthesis API not supported in this browser')
    }
  }

  /**
   * Load available voices
   */
  private loadVoices(): void {
    if (!this.synthesis) return
    this.availableVoices = this.synthesis.getVoices()
    console.log(`Loaded ${this.availableVoices.length} voices`)
  }

  /**
   * Check if speech synthesis is supported
   */
  public isSynthesisSupported(): boolean {
    return this.isSupported
  }

  /**
   * Get available voices
   */
  public getVoices(): SpeechSynthesisVoice[] {
    // Refresh voices in case they weren't loaded yet
    if (this.availableVoices.length === 0) {
      this.loadVoices()
    }
    return this.availableVoices
  }

  /**
   * Get default voice for a language (prefers female voices)
   */
  public getDefaultVoice(lang: string = 'en-US'): SpeechSynthesisVoice | undefined {
    const voices = this.getVoices()
    
    // Helper function to check if voice name suggests female
    const isFemaleVoice = (voice: SpeechSynthesisVoice): boolean => {
      const name = voice.name.toLowerCase()
      const femaleKeywords = ['female', 'woman', 'samantha', 'victoria', 'susan', 'karen', 'zira', 
                              'hazel', 'sara', 'catherine', 'aria', 'joanna', 'salli', 'kimberly',
                              'ivy', 'natalie', 'emma', 'amy', 'clara', 'alice', 'linda', 'heather',
                              'google us english 2', 'google us english 4', 'google us english 6',
                              'google uk english female', 'microsoft zira', 'google हिन्दी']
      return femaleKeywords.some(keyword => name.includes(keyword))
    }
    
    // Try to find female voice for the language
    let voice = voices.find(v => v.lang === lang && isFemaleVoice(v))
    
    // Fallback to any female voice for that language family
    if (!voice) {
      voice = voices.find(v => v.lang.startsWith(lang.split('-')[0]) && isFemaleVoice(v))
    }
    
    // Fallback to any female English voice
    if (!voice) {
      voice = voices.find(v => v.lang.startsWith('en') && isFemaleVoice(v))
    }
    
    // Fallback to default voice for language
    if (!voice) {
      voice = voices.find(v => v.lang === lang && v.default)
    }
    
    // Fallback to any voice for that language
    if (!voice) {
      voice = voices.find(v => v.lang.startsWith(lang.split('-')[0]))
    }
    
    // Fallback to first English voice
    if (!voice) {
      voice = voices.find(v => v.lang.startsWith('en'))
    }
    
    // Final fallback to first available voice
    if (!voice && voices.length > 0) {
      voice = voices[0]
    }
    
    return voice
  }

  /**
   * Check if currently speaking
   */
  public getIsSpeaking(): boolean {
    return this.isSpeaking
  }

  /**
   * Check if paused
   */
  public getIsPaused(): boolean {
    return this.isPaused
  }

  /**
   * Get available female voices
   */
  public getFemaleVoices(lang?: string): SpeechSynthesisVoice[] {
    const voices = this.getVoices()
    
    const isFemaleVoice = (voice: SpeechSynthesisVoice): boolean => {
      const name = voice.name.toLowerCase()
      const femaleKeywords = ['female', 'woman', 'samantha', 'victoria', 'susan', 'karen', 'zira', 
                              'hazel', 'sara', 'catherine', 'aria', 'joanna', 'salli', 'kimberly',
                              'ivy', 'natalie', 'emma', 'amy', 'clara', 'alice', 'linda', 'heather',
                              'google us english 2', 'google us english 4', 'google us english 6',
                              'google uk english female', 'microsoft zira']
      return femaleKeywords.some(keyword => name.includes(keyword))
    }
    
    let femaleVoices = voices.filter(isFemaleVoice)
    
    if (lang) {
      femaleVoices = femaleVoices.filter(v => v.lang.startsWith(lang.split('-')[0]))
    }
    
    return femaleVoices
  }

  /**
   * Speak text with options
   */
  public speak(
    text: string,
    options: TextToSpeechOptions = {},
    onProgress?: SpeechProgressCallback,
    onEnd?: SpeechEndCallback,
    onError?: SpeechErrorCallback
  ): void {
    if (!this.isSupported) {
      const error = 'Speech Synthesis not supported'
      if (onError) onError(error)
      throw new Error(error)
    }

    // Stop any ongoing speech
    this.stop()

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(text)
    this.currentUtterance = utterance

    // Set options
    utterance.voice = options.voice || this.getDefaultVoice(options.lang) || null
    utterance.rate = options.rate ?? 1
    utterance.pitch = options.pitch ?? 1
    utterance.volume = options.volume ?? 1
    utterance.lang = options.lang || 'en-US'

    // Log selected voice for debugging
    if (utterance.voice) {
      console.log(`🎤 Speaking with voice: ${utterance.voice.name} (${utterance.voice.lang})`)
    }

    // Setup event handlers
    utterance.onstart = () => {
      this.isSpeaking = true
      this.isPaused = false
      console.log('Speech started')
    }

    utterance.onend = () => {
      this.isSpeaking = false
      this.isPaused = false
      this.currentUtterance = null
      console.log('Speech ended')
      if (onEnd) onEnd()
    }

    utterance.onerror = (event) => {
      console.error('Speech error:', event.error)
      this.isSpeaking = false
      this.isPaused = false
      this.currentUtterance = null
      
      let errorMessage = 'Unknown error'
      switch (event.error) {
        case 'canceled':
          errorMessage = 'Speech was canceled'
          break
        case 'interrupted':
          errorMessage = 'Speech was interrupted'
          break
        case 'audio-busy':
          errorMessage = 'Audio system is busy'
          break
        case 'audio-hardware':
          errorMessage = 'Audio hardware error'
          break
        case 'network':
          errorMessage = 'Network error occurred'
          break
        case 'synthesis-unavailable':
          errorMessage = 'Speech synthesis unavailable'
          break
        case 'synthesis-failed':
          errorMessage = 'Speech synthesis failed'
          break
        case 'not-allowed':
          errorMessage = 'Speech synthesis not allowed'
          break
        default:
          errorMessage = `Speech error: ${event.error}`
      }
      
      if (onError) onError(errorMessage)
    }

    utterance.onpause = () => {
      this.isPaused = true
      console.log('Speech paused')
    }

    utterance.onresume = () => {
      this.isPaused = false
      console.log('Speech resumed')
    }

    utterance.onboundary = (event) => {
      if (onProgress) {
        onProgress({
          charIndex: event.charIndex,
          charLength: event.charLength,
          elapsedTime: event.elapsedTime
        })
      }
    }

    // Start speaking
    try {
      if (!this.synthesis) {
        throw new Error('Speech synthesis not initialized')
      }
      this.synthesis.speak(utterance)
    } catch (error) {
      console.error('Failed to start speech:', error)
      if (onError) onError('Failed to start speech synthesis')
    }
  }

  /**
   * Pause current speech
   */
  public pause(): void {
    if (this.isSupported && this.synthesis && this.isSpeaking && !this.isPaused) {
      this.synthesis.pause()
    }
  }

  /**
   * Resume paused speech
   */
  public resume(): void {
    if (this.isSupported && this.synthesis && this.isSpeaking && this.isPaused) {
      this.synthesis.resume()
    }
  }

  /**
   * Stop current speech
   */
  public stop(): void {
    if (this.isSupported && this.synthesis && this.isSpeaking) {
      this.synthesis.cancel()
      this.isSpeaking = false
      this.isPaused = false
      this.currentUtterance = null
    }
  }

  /**
   * Speak text with auto-detection of important parts
   * Useful for speaking bot responses while emphasizing key information
   */
  public speakWithEmphasis(
    text: string,
    options: TextToSpeechOptions = {},
    onEnd?: SpeechEndCallback,
    onError?: SpeechErrorCallback
  ): void {
    // Split by emphasis markers (could be emojis or special markers)
    const emphasizedOptions = {
      ...options,
      rate: (options.rate || 1) * 0.95, // Slightly slower for clarity
      pitch: options.pitch || 1
    }
    
    this.speak(text, emphasizedOptions, undefined, onEnd, onError)
  }

  /**
   * Clean up resources
   */
  public cleanup(): void {
    this.stop()
  }
}

// Export singleton instance
export const textToSpeech = new TextToSpeechService()
