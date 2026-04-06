// Central API client — all fetches go through here.
// Vite dev-server proxies /api/* → http://localhost:8000
const BASE = '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  scores:    ()                          => get('/score'),
  summary:   ()                          => get('/summary'),
  parties:   ()                          => get('/parties'),
  health:    ()                          => fetch('/health').then(r => r.json()),
  promises:  (params = {})              => {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''))
    ).toString()
    return get(`/promises${q ? `?${q}` : ''}`)
  },
  promise:   (id)                        => get(`/promises/${id}`),
}
