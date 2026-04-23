export default function CompletionScreen({ personaName }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-white p-4">
      <div className="card max-w-md w-full text-center animate-slide-up">
        <div className="text-5xl mb-4">🎉</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Survey Complete!</h1>
        <p className="text-gray-600 mb-6">
          Thank you for participating in this Voxora research survey.
          {personaName && (
            <> {personaName} and the research team appreciate your time.</>
          )}
        </p>
        <div className="bg-indigo-50 rounded-xl p-4 text-sm text-indigo-700">
          Your responses have been recorded and will be used to generate research insights.
        </div>
      </div>
    </div>
  )
}
