const API_URL = import.meta.env.VITE_API_URL || "https://vaakazhipeer.onrender.com"
const BASE = `${API_URL}/api`

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
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
  getHealth: () => fetch(`${API_URL}/health`).then(r => {
    if (!r.ok) throw new Error('Unhealthy');
    return r.json();
  }),
}
