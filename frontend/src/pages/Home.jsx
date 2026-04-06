import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { api } from '../api'
import ScoreCard    from '../components/ScoreCard'
import CategoryBar  from '../components/CategoryBar'

function SkeletonCard() {
  return (
    <div className="glass" style={{ padding: 28, minHeight: 220 }}>
      <div className="skeleton" style={{ height: 24, width: '60%', marginBottom: 12 }} />
      <div className="skeleton" style={{ height: 48, width: '40%', marginBottom: 16 }} />
      <div className="skeleton" style={{ height: 8,  width: '100%', marginBottom: 20 }} />
      <div className="skeleton" style={{ height: 14, width: '80%' }} />
    </div>
  )
}

export default function Home() {
  const [summary, setSummary]   = useState(null)
  const [health,  setHealth]    = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error,   setError]     = useState(null)

  useEffect(() => {
    Promise.all([api.summary(), api.health()])
      .then(([s, h]) => { setSummary(s); setHealth(h) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // Build radar data from summary categories
  const radarData = summary
    ? (() => {
        const cats = new Set()
        Object.values(summary).forEach(p => Object.keys(p.categories || {}).forEach(c => cats.add(c)))
        return [...cats].map(cat => {
          const row = { category: cat.replace('women and youth', 'Women') }
          Object.entries(summary).forEach(([k, p]) => {
            const c = (p.categories || {})[cat]
            row[k] = c ? c.score : 0
          })
          return row
        })
      })()
    : []

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 24px' }}>

      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 56 }} className="fade-up">
        <h1 style={{
          fontFamily: "'Space Grotesk',sans-serif",
          fontSize: 'clamp(28px,5vw,52px)',
          fontWeight: 900, lineHeight: 1.1,
          background: 'linear-gradient(135deg,#22d3ee 20%,#6366f1 60%,#f59e0b)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          marginBottom: 16,
        }}>
          வாக்காளிபீர்
        </h1>
        <p style={{ fontSize: 16, color: '#64748b', maxWidth: 540, margin: '0 auto 8px' }}>
          Tracking Tamil Nadu political promises — data-driven, unbiased, open.
        </p>
        {health && (
          <p style={{ fontSize: 12, color: '#334155' }}>
            {health.total_articles?.toLocaleString()} articles indexed ·{' '}
            Last updated: {health.last_updated ? new Date(health.last_updated).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
          </p>
        )}
      </div>

      {error && (
        <div style={{ background: 'rgba(239,68,68,.1)', border: '1px solid #ef444440', borderRadius: 12, padding: '16px 20px', marginBottom: 32, color: '#fca5a5' }}>
          ⚠ Could not reach API: {error}. Make sure the backend is running on port 8000.
        </div>
      )}

      {/* Score Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 20, marginBottom: 48 }}>
        {loading
          ? [1,2,3,4].map(i => <SkeletonCard key={i} />)
          : summary && Object.entries(summary).map(([k, d]) => (
              <ScoreCard key={k} partyKey={k} data={d} />
            ))
        }
      </div>

      {/* Radar + Category Breakdowns */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 48 }}>

          {/* Radar */}
          <div className="glass fade-up" style={{ padding: 28 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20, color: '#e2e8f0' }}>Category Radar</h2>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData} outerRadius={100}>
                <PolarGrid stroke="rgba(255,255,255,0.06)" />
                <PolarAngleAxis dataKey="category" tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                {summary && Object.keys(summary).map((k, i) => {
                  const colors = ['#22d3ee','#f59e0b','#6366f1','#10b981']
                  return (
                    <Radar key={k} name={k} dataKey={k}
                      stroke={colors[i % 4]} fill={colors[i % 4]} fillOpacity={0.12} strokeWidth={2}
                    />
                  )
                })}
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Category breakdown for DMK 2021 */}
          {summary['DMK 2021'] && (
            <div className="glass fade-up" style={{ padding: 28 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20, color: '#e2e8f0' }}>
                DMK 2021 — Category Breakdown
              </h2>
              <CategoryBar categories={summary['DMK 2021'].categories} />
            </div>
          )}
        </div>
      )}

      {/* CTA row */}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <Link to="/promises" style={{
          padding: '12px 28px', borderRadius: 10,
          background: 'rgba(34,211,238,.12)', color: '#22d3ee',
          fontWeight: 600, fontSize: 14, textDecoration: 'none',
          border: '1px solid rgba(34,211,238,.25)',
          transition: 'background .2s',
        }}>Browse All Promises →</Link>
        <Link to="/compare" style={{
          padding: '12px 28px', borderRadius: 10,
          background: 'rgba(255,255,255,.04)', color: '#94a3b8',
          fontWeight: 600, fontSize: 14, textDecoration: 'none',
          border: '1px solid rgba(255,255,255,.08)',
          transition: 'background .2s',
        }}>Compare Parties →</Link>
      </div>
    </div>
  )
}
