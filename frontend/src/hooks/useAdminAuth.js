import { useCallback } from 'react'
import { useAdminStore } from '../store/adminStore'
import { api } from '../services/api'

/**
 * useAdminAuth — manages admin JWT state.
 * Provides login/logout helpers and an isAuthenticated flag.
 */
export function useAdminAuth() {
  const { token, setToken, clearToken } = useAdminStore()

  const login = useCallback(async (username, password) => {
    const { data } = await api.post('/api/auth/login', { username, password })
    setToken(data.access_token)
    return data
  }, [setToken])

  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout')
    } catch { /* ignore */ }
    clearToken()
  }, [clearToken])

  return {
    isAuthenticated: !!token,
    token,
    login,
    logout,
  }
}

/**
 * useAdminApi — provides pre-authenticated API helpers for admin routes.
 */
export function useAdminApi() {
  const { token } = useAdminStore()
  const headers = token ? { Authorization: `Bearer ${token}` } : {}
  return {
    get:    (url, config = {}) => api.get(url,  { ...config, headers: { ...headers, ...config.headers } }),
    post:   (url, data, config = {}) => api.post(url, data, { ...config, headers: { ...headers, ...config.headers } }),
    patch:  (url, data, config = {}) => api.patch(url, data, { ...config, headers: { ...headers, ...config.headers } }),
    delete: (url, config = {}) => api.delete(url, { ...config, headers: { ...headers, ...config.headers } }),
  }
}
