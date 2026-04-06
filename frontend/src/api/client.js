const BASE = import.meta.env.VITE_API_URL

export const api = {
  getScore:    () => fetch(`${BASE}/api/score`).then(r => r.json()),
  getParties:  () => fetch(`${BASE}/api/parties`).then(r => r.json()),
  getSummary:  () => fetch(`${BASE}/api/summary`).then(r => r.json()),
  getHealth:   () => fetch(`${BASE}/health`).then(r => r.json()),
  getPromises: (params) => {
    // Strip raw undefined/empty string to avoid '?party=&year=' clutter
    const cleanParams = Object.fromEntries(
      Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== '')
    )
    const q = new URLSearchParams(cleanParams).toString()
    return fetch(`${BASE}/api/promises${q ? `?${q}` : ''}`).then(r => r.json())
  },
  getPromise:  (id) => fetch(`${BASE}/api/promises/${id}`).then(r => r.json()),
}
