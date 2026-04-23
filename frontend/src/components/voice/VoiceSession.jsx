import { useVoiceSession } from '../../hooks/useVoiceSession'
import AudioVisualizer from './AudioVisualizer'
import VADProcessor from './VADProcessor'

export default function VoiceSession({ sessionData, onQuestionChange, onCompleted }) {
  const {
    wsStatus,
    isRecording,
    analyserNode,
    isSpeaking,
    startRecording,
    stopRecording,
    isMuted,
    toggleMute,
  } = useVoiceSession({ sessionData, onQuestionChange, onCompleted })

  const canRecord = wsStatus === 'connected' || wsStatus === 'listening'

  return (
    <div className="card flex flex-col items-center gap-6 py-8">
      {/* Waveform */}
      <div className="w-full">
        <AudioVisualizer analyserNode={analyserNode} isActive={isRecording} />
      </div>

      {/* VAD processor (invisible — drives isSpeaking via analyserNode) */}
      {analyserNode && (
        <VADProcessor analyserNode={analyserNode} isActive={isRecording} />
      )}

      {/* Recording button */}
      <div className="flex flex-col items-center gap-3">
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onTouchStart={startRecording}
          onTouchEnd={stopRecording}
          disabled={!canRecord || isMuted}
          className={`w-20 h-20 rounded-full flex items-center justify-center text-white text-3xl transition-all duration-150 shadow-lg
            ${isRecording
              ? 'bg-red-500 scale-110 ring-4 ring-red-300'
              : canRecord && !isMuted
                ? 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'
                : 'bg-gray-300 cursor-not-allowed'
            }`}
          aria-label={isRecording ? 'Recording — release to stop' : 'Hold to speak'}
        >
          🎙
        </button>
        <p className="text-xs text-gray-500">
          {isRecording ? 'Recording… release to send' : 'Hold to speak'}
        </p>
      </div>

      {/* Mute toggle */}
      <button
        onClick={toggleMute}
        className="btn-secondary text-xs"
        aria-label={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? '🔇 Unmuted' : '🔊 Mute'}
      </button>
    </div>
  )
}
