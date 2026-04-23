export default function QuestionProgress({ current, total, questionText }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div className="card">
      <div className="flex justify-between text-xs text-gray-500 mb-2">
        <span>Question {current} of {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
        <div
          className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      {questionText && (
        <p className="text-sm font-medium text-gray-800 leading-relaxed">
          {questionText}
        </p>
      )}
    </div>
  )
}
