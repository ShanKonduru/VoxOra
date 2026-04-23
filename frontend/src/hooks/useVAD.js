import { useEffect, useRef, useState } from 'react'

const RMS_THRESHOLD = 0.015
const SPEECH_START_FRAMES = 3    // consecutive frames above threshold to trigger start
const SILENCE_FRAMES_END = 40    // ~800ms at 50 fps to trigger end

/**
 * useVAD — client-side Voice Activity Detection via AnalyserNode RMS energy.
 */
export function useVAD({ analyserNode, isActive, onSpeechStart, onSpeechEnd }) {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const frameRef = useRef(null)
  const consecutiveSpeechRef = useRef(0)
  const silenceFramesRef = useRef(0)
  const speakingRef = useRef(false)

  useEffect(() => {
    if (!analyserNode || !isActive) {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
      return
    }

    const bufferLength = analyserNode.fftSize
    const dataArray = new Float32Array(bufferLength)

    const tick = () => {
      frameRef.current = requestAnimationFrame(tick)
      analyserNode.getFloatTimeDomainData(dataArray)

      let sum = 0
      for (let i = 0; i < bufferLength; i++) sum += dataArray[i] ** 2
      const rms = Math.sqrt(sum / bufferLength)

      if (rms > RMS_THRESHOLD) {
        consecutiveSpeechRef.current++
        silenceFramesRef.current = 0
        if (!speakingRef.current && consecutiveSpeechRef.current >= SPEECH_START_FRAMES) {
          speakingRef.current = true
          setIsSpeaking(true)
          onSpeechStart?.()
        }
      } else {
        consecutiveSpeechRef.current = 0
        if (speakingRef.current) {
          silenceFramesRef.current++
          if (silenceFramesRef.current >= SILENCE_FRAMES_END) {
            speakingRef.current = false
            silenceFramesRef.current = 0
            setIsSpeaking(false)
            onSpeechEnd?.()
          }
        }
      }
    }

    tick()
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [analyserNode, isActive, onSpeechStart, onSpeechEnd])

  return { isSpeaking }
}
