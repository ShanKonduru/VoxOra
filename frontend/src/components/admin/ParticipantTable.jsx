import { useEffect, useState } from 'react'
import { useAdminApi } from '../../hooks/useAdminAuth'

const STATUS_BADGE = {
  PENDING:     'badge-yellow',
  IN_PROGRESS: 'badge-blue',
  COMPLETED:   'badge-green',
  FLAGGED:     'badge-red',
  EXPIRED:     'badge-gray',
}

export default function ParticipantTable() {
  const { get } = useAdminApi()
  const [participants, setParticipants] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const PAGE_SIZE = 50

  const fetchParticipants = (p = 1) => {
    setLoading(true)
    get(`/api/participants/?page=${p}&page_size=${PAGE_SIZE}`)
      .then((res) => {
        setParticipants(res.data.items)
        setTotal(res.data.total)
        setPage(p)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchParticipants() }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Participants</h1>
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-left">
              <th className="px-4 py-3 font-medium text-gray-600">Name</th>
              <th className="px-4 py-3 font-medium text-gray-600">Email</th>
              <th className="px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="px-4 py-3 font-medium text-gray-600">Reminders</th>
              <th className="px-4 py-3 font-medium text-gray-600">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="text-center py-10 text-gray-400">Loading…</td>
              </tr>
            ) : participants.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-10 text-gray-400">No participants found.</td>
              </tr>
            ) : (
              participants.map((p) => (
                <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{p.name ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{p.email}</td>
                  <td className="px-4 py-3">
                    <span className={STATUS_BADGE[p.status] || 'badge-gray'}>{p.status}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{p.reminder_count ?? 0}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {total > PAGE_SIZE && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">{total} total</span>
            <div className="flex gap-2">
              <button
                className="btn-secondary text-xs py-1 px-2"
                onClick={() => fetchParticipants(page - 1)}
                disabled={page <= 1}
              >← Prev</button>
              <button
                className="btn-secondary text-xs py-1 px-2"
                onClick={() => fetchParticipants(page + 1)}
                disabled={page * PAGE_SIZE >= total}
              >Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
