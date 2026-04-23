import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAdminApi } from '../../hooks/useAdminAuth'

export default function ResponseViewer() {
  const { sessionId } = useParams()
  const { get } = useAdminApi()
  const [responses, setResponses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) return
    get(`/api/admin/sessions/${sessionId}/responses`)
      .then((res) => setResponses(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) return <div className="animate-pulse h-48 bg-gray-100 rounded-2xl" />

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Session Responses</h1>
      {responses.length === 0 ? (
        <div className="card text-center text-gray-400 py-10">No responses recorded for this session.</div>
      ) : (
        <div className="space-y-4">
          {responses.map((r, i) => (
            <div key={r.id} className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-indigo-600">Response {i + 1}</span>
                {r.moderation_flagged && (
                  <span className="badge-red">⚠ Flagged</span>
                )}
                {r.was_refocused && (
                  <span className="badge-yellow">↩ Refocused</span>
                )}
              </div>
              <p className="text-sm text-gray-800 leading-relaxed">{r.transcript_clean || r.transcript_raw}</p>
              {r.sentiment_score != null && (
                <p className="text-xs text-gray-400 mt-2">Sentiment: {r.sentiment_score}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
