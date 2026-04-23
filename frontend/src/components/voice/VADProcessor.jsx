import { useEffect } from 'react'
import { useVAD } from '../../hooks/useVAD'

/**
 * VADProcessor — invisible component.
 * Uses the AnalyserNode to detect speech start/end via RMS energy.
 * Notifies parent via onSpeechStart / onSpeechEnd if provided.
 */
export default function VADProcessor({
  analyserNode,
  isActive,
  onSpeechStart,
  onSpeechEnd,
}) {
  const { isSpeaking } = useVAD({ analyserNode, isActive, onSpeechStart, onSpeechEnd })
  return null  // Render nothing — purely behavioural
}
