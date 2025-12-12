/**
 * Converts a Float32Array (Web Audio API default) to Int16Array (PCM required by Gemini).
 * Scales the float values (-1.0 to 1.0) to 16-bit integers (-32768 to 32767).
 */
export function float32ToInt16(float32: Float32Array): Int16Array {
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return int16;
}

/**
 * Encodes a Uint8Array (representing raw bytes) to a base64 string.
 * Used for sending audio data to the API.
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Decodes a base64 string into a Uint8Array.
 * Used for receiving audio data from the API.
 */
export function base64ToArrayBuffer(base64: string): Uint8Array {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

/**
 * Creates an AudioBuffer from raw PCM data (Int16).
 */
export function pcmToAudioBuffer(
  pcmData: Int16Array | Uint8Array,
  context: AudioContext,
  sampleRate: number = 24000,
  channels: number = 1
): AudioBuffer {
  // If input is Uint8Array (raw bytes), view it as Int16Array
  const int16 = pcmData instanceof Uint8Array 
    ? new Int16Array(pcmData.buffer, pcmData.byteOffset, pcmData.byteLength / 2)
    : pcmData;
    
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 32768.0;
  }

  const buffer = context.createBuffer(channels, float32.length, sampleRate);
  buffer.copyToChannel(float32, 0);
  return buffer;
}