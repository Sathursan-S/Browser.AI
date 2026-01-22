// Utility functions copied from audioUtils
function float32ToInt16(float32Array) {
  const int16Array = new Int16Array(float32Array.length)
  for (let i = 0; i < float32Array.length; i++) {
    int16Array[i] = Math.max(-32768, Math.min(32767, float32Array[i] * 32768))
  }
  return int16Array
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  const base64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
  let result = ''
  let i
  for (i = 0; i < bytes.length - 2; i += 3) {
    result += base64chars[bytes[i] >> 2]
    result += base64chars[((bytes[i] & 3) << 4) | (bytes[i + 1] >> 4)]
    result += base64chars[((bytes[i + 1] & 15) << 2) | (bytes[i + 2] >> 6)]
    result += base64chars[bytes[i + 2] & 63]
  }
  if (i < bytes.length) {
    result += base64chars[bytes[i] >> 2]
    if (i + 1 < bytes.length) {
      result += base64chars[((bytes[i] & 3) << 4) | (bytes[i + 1] >> 4)]
      result += base64chars[(bytes[i + 1] & 15) << 2]
      result += '='
    } else {
      result += base64chars[(bytes[i] & 3) << 4]
      result += '=='
    }
  }
  return result
}

class AudioProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0]
    if (input.length > 0) {
      const inputData = input[0] // mono channel

      // Calculate volume for visualizer
      let sum = 0
      for (let i = 0; i < inputData.length; i++) sum += inputData[i] * inputData[i]
      const rms = Math.sqrt(sum / inputData.length)
      const volume = Math.min(100, rms * 500)

      // Convert to PCM Int16
      const pcmData = float32ToInt16(inputData)
      const base64Data = arrayBufferToBase64(pcmData.buffer)

      // Send to main thread
      this.port.postMessage({ audioData: base64Data, volume })
    }
    return true
  }
}

registerProcessor('audio-processor', AudioProcessor)
