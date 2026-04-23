---
description: "Use when writing or editing React components, hooks, Zustand stores, Axios services, or WebSocket client code. Covers thin-component pattern, hook architecture, auth token storage, and admin API patterns."
applyTo: "frontend/src/**/*.{js,jsx}"
---

# Frontend Conventions

## Component Architecture

Components are **thin** — no direct API calls, no business logic. All state and side-effects live in hooks.

```jsx
// ✅ Correct — component delegates to hook
export default function VoiceSession({ sessionData, onCompleted }) {
  const { isRecording, startRecording, stopRecording } = useVoiceSession(...)
  return <button onMouseDown={startRecording} onMouseUp={stopRecording} />
}

// ❌ Never — API call inside component
export default function VoiceSession() {
  const [data, setData] = useState(null)
  useEffect(() => { fetch('/api/...').then(...) }, [])
}
```

## Hook Conventions

All stateful logic, API calls, and WebSocket management live in `src/hooks/`.

- `useAdminAuth` — login/logout/isAuthenticated; wraps `useAdminStore`
- `useAdminApi` — pre-authed HTTP helpers (`get`, `post`, `patch`, `delete`); always use this in admin components instead of importing `api` directly
- `useVoiceSession` — microphone, MediaRecorder, AudioContext, WebSocket lifecycle
- `useVAD` — RMS energy voice activity detection (see voice-pipeline instructions)

## Auth Token Storage

- **Access token**: Zustand `adminStore` with `sessionStorage` persistence (clears on tab close)
- **Refresh token**: httpOnly cookie — managed server-side, never read from JS
- **Never** store tokens in `localStorage` or state that survives cross-tab

```js
// ✅ Correct — sessionStorage via Zustand persist custom adapter
export const useAdminStore = create(
  persist(
    (set) => ({ token: null, setToken: (t) => set({ token: t }), clearToken: () => set({ token: null }) }),
    {
      name: 'voxora-admin',
      storage: {
        getItem: (k) => { const v = sessionStorage.getItem(k); return v ? JSON.parse(v) : null },
        setItem: (k, v) => sessionStorage.setItem(k, JSON.stringify(v)),
        removeItem: (k) => sessionStorage.removeItem(k),
      },
    }
  )
)
```

## Axios API Service

`src/services/api.js` is the single Axios instance. Key behaviours:

1. Request interceptor attaches `Authorization: Bearer {token}` from `adminStore`
2. Response interceptor on 401: calls `POST /api/auth/refresh`, updates token, **retries original request**
3. Concurrent 401s are queued — only one refresh call is made
4. On refresh failure: clears token, redirects to `/admin/login`

```js
// ✅ Correct — use api via useAdminApi hook in components
const { get } = useAdminApi()
const { data } = await get('/api/admin/stats')

// ❌ Never — direct import of api in components
import { api } from '../services/api'
```

## Zustand Store Rules

- `sessionStore` — voice session state; only persist non-sensitive data (question index, totals) to `localStorage`
- `adminStore` — JWT token; persisted to `sessionStorage` only
- Call stores with selector functions, not full state object: `useAdminStore(s => s.token)`

## Styling

Use Tailwind utility classes. Custom component classes defined in `styles/index.css`:
- `.btn-primary`, `.btn-secondary` — buttons
- `.card` — white rounded-2xl shadow panel
- `.input-field` — form inputs
- `.badge`, `.badge-green`, `.badge-yellow`, `.badge-red`, `.badge-gray`, `.badge-blue` — status badges
