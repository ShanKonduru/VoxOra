import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import CompletionScreen from '../components/survey/CompletionScreen'
import PersonaCard from '../components/survey/PersonaCard'
import QuestionProgress from '../components/survey/QuestionProgress'
import ConnectionStatus from '../components/voice/ConnectionStatus'
import VoiceSession from '../components/voice/VoiceSession'
import { api } from '../services/api'

const STAGES = {
  LOADING: 'LOADING',
  CONSENT: 'CONSENT',
  SESSION: 'SESSION',
  COMPLETED: 'COMPLETED',
  ERROR: 'ERROR',
}

export default function SurveyPage() {
  const { inviteToken } = useParams()
  const [stage, setStage] = useState(STAGES.LOADING)
  const [sessionData, setSessionData] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [consentGiven, setConsentGiven] = useState(false)
  const [questionState, setQuestionState] = useState({ index: 0, text: '', total: 0 })

  useEffect(() => {
    setStage(STAGES.CONSENT)
  }, [])

  const handleConsent = async () => {
    try {
      const { data } = await api.post('/api/sessions/init', {
        invite_token: inviteToken,
        ip_address: null,
        user_agent: navigator.userAgent,
      })
      setSessionData(data)
      setQuestionState({ index: 0, text: '', total: data.total_questions })
      setStage(STAGES.SESSION)
    } catch (err) {
      const status = err?.response?.status
      if (status === 409) setErrorMsg('You have already completed this survey.')
      else if (status === 410) setErrorMsg('This survey invitation has expired.')
      else if (status === 404) setErrorMsg('Invalid survey link.')
      else setErrorMsg('Unable to start session. Please try again later.')
      setStage(STAGES.ERROR)
    }
  }

  const handleQuestionChange = (index, text, total) => {
    setQuestionState({ index, text, total })
  }

  const handleCompleted = () => setStage(STAGES.COMPLETED)

  if (stage === STAGES.LOADING) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-indigo-600 border-t-transparent" />
      </div>
    )
  }

  if (stage === STAGES.ERROR) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="card max-w-md w-full text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Unable to Start Survey</h1>
          <p className="text-gray-600">{errorMsg}</p>
        </div>
      </div>
    )
  }

  if (stage === STAGES.CONSENT) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-white p-4">
        <div className="card max-w-lg w-full animate-fade-in">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
              V
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Voxora Research</h1>
          </div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            Voice Survey Consent
          </h2>
          <div className="bg-indigo-50 rounded-xl p-4 mb-6 text-sm text-gray-700 space-y-2">
            <p>✓ This survey uses <strong>voice interaction</strong>. You will speak your answers aloud.</p>
            <p>✓ Your responses will be <strong>transcribed and recorded</strong> for research purposes.</p>
            <p>✓ Audio data is processed by OpenAI services and stored securely.</p>
            <p>✓ You may end the session at any time by closing this window.</p>
          </div>
          <p className="text-xs text-gray-500 mb-6">
            By clicking "Begin Survey" you consent to the above terms and confirm you
            are at least 18 years of age.
          </p>
          <button onClick={handleConsent} className="btn-primary w-full py-3 text-base">
            Begin Survey
          </button>
        </div>
      </div>
    )
  }

  if (stage === STAGES.COMPLETED) {
    return <CompletionScreen personaName={sessionData?.persona?.name} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col items-center justify-center p-4 gap-4">
      <div className="w-full max-w-2xl space-y-4">
        <div className="flex items-center justify-between">
          <PersonaCard persona={sessionData?.persona} />
          <ConnectionStatus />
        </div>
        <QuestionProgress
          current={questionState.index + 1}
          total={questionState.total}
          questionText={questionState.text}
        />
        <VoiceSession
          sessionData={sessionData}
          onQuestionChange={handleQuestionChange}
          onCompleted={handleCompleted}
        />
      </div>
    </div>
  )
}
