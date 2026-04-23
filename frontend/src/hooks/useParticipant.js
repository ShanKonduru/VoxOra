import { useCallback, useEffect, useState } from 'react'
import { useAdminApi } from './useAdminAuth'

/**
 * useParticipant — fetches a single participant record for admin views.
 */
export function useParticipant(participantId) {
  const { get } = useAdminApi()
  const [participant, setParticipant] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(() => {
    if (!participantId) return
    setLoading(true)
    setError(null)
    get(`/api/participants/${participantId}`)
      .then((res) => setParticipant(res.data))
      .catch((err) => setError(err))
      .finally(() => setLoading(false))
  }, [participantId])

  useEffect(() => { fetch() }, [fetch])

  return { participant, loading, error, refetch: fetch }
}
