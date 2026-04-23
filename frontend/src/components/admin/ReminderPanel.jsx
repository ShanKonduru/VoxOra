import { useState } from 'react'
import { useAdminApi } from '../../hooks/useAdminAuth'

export default function ReminderPanel() {
  const { post } = useAdminApi()
  const [participantIds, setParticipantIds] = useState('')
  const [customMessage, setCustomMessage] = useState(
    'We wanted to remind you that your survey is still waiting to be completed.'
  )
  const [baseUrl, setBaseUrl] = useState(window.location.origin)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSend = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)

    const ids = participantIds
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean)

    if (ids.length === 0) {
      setError('Please enter at least one participant ID.')
      return
    }

    setLoading(true)
    try {
      const { data } = await post('/api/admin/reminders', {
        participant_ids: ids,
        base_url: baseUrl,
        custom_message: customMessage,
      })
      setResult(data)
    } catch {
      setError('Failed to send reminders. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Send Reminders</h1>
      <div className="card max-w-2xl">
        <form onSubmit={handleSend} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Participant IDs (comma or newline separated)
            </label>
            <textarea
              className="input-field min-h-[100px] font-mono text-xs"
              value={participantIds}
              onChange={(e) => setParticipantIds(e.target.value)}
              placeholder="uuid1, uuid2, uuid3..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Custom Message
            </label>
            <textarea
              className="input-field min-h-[80px]"
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Survey Base URL
            </label>
            <input
              type="url"
              className="input-field"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          {result && (
            <p className="text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">
              ✓ Sent {result.sent} of {result.total} reminders successfully.
            </p>
          )}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Sending…' : 'Send Reminders'}
          </button>
        </form>
      </div>
    </div>
  )
}
