import { useCallback, useEffect, useRef, useState } from 'react'
import { useSessionStore } from '../store/sessionStore'
import { createWebSocketClient } from '../services/websocketClient'

const RMS_THRESHOLD = 0.015
const SILENCE_FRAMES_NEEDED = 40  // ~800ms at 50fps

/**
 * useVoiceSession — orchestrates microphone capture, VAD, WebSocket, and audio playback.
 */
export function useVoiceSession({ sessionData, onQuestionChange, onCompleted }) {
  const setWsStatus = useSessionStore((s) => s.setWsStatus)
  const wsStatus = useSessionStore((s) => s.wsStatus)

  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const streamRef = useRef(null)

  const [isRecording, setIsRecording] = useState(false)
  const [analyserNode, setAnalyserNode] = useState(null)
  const [isMuted, setIsMuted] = useState(false)

  // ── Setup microphone + AudioContext ──────────────────────────────────────

  const initAudio = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      streamRef.current = stream
      const ctx = new AudioContext()
      audioContextRef.current = ctx
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser
      setAnalyserNode(analyser)
    } catch (err) {
      console.error('Failed to get microphone access:', err)
      setWsStatus('error')
    }
  }, [setWsStatus])

  // ── Connect WebSocket ─────────────────────────────────────────────────────

  useEffect(() => {
    if (!sessionData) return

    initAudio()

    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    const ws = createWebSocketClient(`${wsBaseUrl}/ws/session/${sessionData.session_id}`)
    wsRef.current = ws

    ws.onStatusChange((status) => setWsStatus(status))

    ws.onMessage((data) => {
      if (data instanceof Blob || data instanceof ArrayBuffer) {
        // Audio response from the server — play it
        playAudio(data)
      } else if (typeof data === 'string') {
        try {
          const msg = JSON.parse(data)
          if (msg.type === 'control') {
            if (msg.event === 'question') {
              onQuestionChange?.(msg.question_index, msg.question_text, msg.total)
            } else if (msg.event === 'completed') {
              onCompleted?.()
            }
          }
        } catch { /* ignore parse errors */ }
      }
    })

    ws.connect(sessionData.session_token)

    return () => {
      ws.disconnect()
      streamRef.current?.getTracks().forEach((t) => t.stop())
      audioContextRef.current?.close()
    }
  }, [sessionData])

  // ── Audio playback ────────────────────────────────────────────────────────

  const playAudio = async (audioData) => {
    try {
      const arrayBuffer = audioData instanceof Blob
        ? await audioData.arrayBuffer()
        : audioData
      const ctx = audioContextRef.current || new AudioContext()
      const decoded = await ctx.decodeAudioData(arrayBuffer)
      const source = ctx.createBufferSource()
      source.buffer = decoded
      source.connect(ctx.destination)
      source.start()
    } catch (err) {
      console.warn('Audio playback failed:', err)
    }
  }

  // ── Recording (push-to-talk) ──────────────────────────────────────────────

  const startRecording = useCallback(() => {
    if (!streamRef.current || isRecording || isMuted) return
    audioChunksRef.current = []
    const recorder = new MediaRecorder(streamRef.current, { mimeType: 'audio/webm;codecs=opus' })
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data)
    }
    mediaRecorderRef.current = recorder
    recorder.start(100)  // collect in 100ms chunks
    setIsRecording(true)
    setWsStatus('listening')
  }, [isRecording, isMuted, setWsStatus])

  const stopRecording = useCallback(async () => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === 'inactive') return

    return new Promise((resolve) => {
      recorder.onstop = async () => {
        setIsRecording(false)
        setWsStatus('processing')
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' })
        const arrayBuffer = await blob.arrayBuffer()
        wsRef.current?.sendBinary(arrayBuffer)
        audioChunksRef.current = []
        resolve()
      }
      recorder.stop()
    })
  }, [setWsStatus])

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const newMuted = !prev
      streamRef.current?.getAudioTracks().forEach((t) => {
        t.enabled = !newMuted
      })
      return newMuted
    })
  }, [])

  return {
    wsStatus,
    isRecording,
    analyserNode,
    isMuted,
    startRecording,
    stopRecording,
    toggleMute,
  }
}
