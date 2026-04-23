import { useEffect, useState } from 'react'
import { useAdminApi } from '../../hooks/useAdminAuth'

export default function StatsOverview() {
  const { get } = useAdminApi()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    get('/api/admin/stats')
      .then((res) => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="animate-pulse h-48 bg-gray-100 rounded-2xl" />

  const cards = [
    { label: 'Total Surveys', value: stats?.total_surveys ?? 0, color: 'text-indigo-600' },
    { label: 'Total Participants', value: stats?.total_participants ?? 0, color: 'text-gray-800' },
    { label: 'Completed', value: stats?.completed_participants ?? 0, color: 'text-green-600' },
    { label: 'In Progress', value: stats?.in_progress_participants ?? 0, color: 'text-yellow-600' },
    { label: 'Flagged Sessions', value: stats?.flagged_sessions ?? 0, color: 'text-red-600' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="card">
            <p className={`text-3xl font-bold ${c.color}`}>{c.value}</p>
            <p className="text-xs text-gray-500 mt-1">{c.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
