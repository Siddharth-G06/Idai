/**
 * api/client.js — Vaakazhipeer
 *
 * All requests go through the Vite dev-server proxy (/api/* → localhost:8000)
 * so there are no CORS issues in development.
 * In production (Vercel), the rewrites in vercel.json forward /api/* to Render.
 */

async function get(path) {
  const res = await fetch(`/api${path}`)
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try { detail = (await res.json()).detail || detail } catch (_) {}
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  // GET /api/score  → full scores.json
  getScore: () => get('/score'),

  // GET /api/summary → per-party summary with top_category
  getSummary: () => get('/summary'),

  // GET /api/parties → list of parties + years
  getParties: () => get('/parties'),

  // GET /api/promises?party=DMK&year=2021&category=...&status=...
  getPromises: (params = {}) => {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '' && v !== null)
    )
    const q = new URLSearchParams(clean).toString()
    return get(`/promises${q ? `?${q}` : ''}`)
  },

  // GET /api/promises/:id
  getPromise: (id) => get(`/promises/${id}`),

  // GET /health
  getHealth: () => fetch('/health').then(r => r.json()),
}
