import { useEffect, useRef } from 'react'

/**
 * AudioVisualizer — renders a real-time waveform bar display
 * using an AnalyserNode derived from the live microphone stream.
 */
export default function AudioVisualizer({ analyserNode, isActive }) {
  const canvasRef = useRef(null)
  const rafRef = useRef(null)

  useEffect(() => {
    if (!analyserNode || !isActive) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      const canvas = canvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      }
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const bufferLength = analyserNode.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      rafRef.current = requestAnimationFrame(draw)
      analyserNode.getByteFrequencyData(dataArray)

      const { width, height } = canvas
      ctx.clearRect(0, 0, width, height)

      const barCount = 40
      const barWidth = (width / barCount) * 0.6
      const gap = (width / barCount) * 0.4
      const step = Math.floor(bufferLength / barCount)

      for (let i = 0; i < barCount; i++) {
        const value = dataArray[i * step] / 255
        const barHeight = Math.max(4, value * height * 0.9)
        const x = i * (barWidth + gap)
        const y = (height - barHeight) / 2

        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight)
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.9)')
        gradient.addColorStop(1, 'rgba(165, 180, 252, 0.4)')

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.roundRect(x, y, barWidth, barHeight, 2)
        ctx.fill()
      }
    }

    draw()
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [analyserNode, isActive])

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={80}
      className="w-full max-w-xs mx-auto"
      aria-hidden="true"
    />
  )
}
