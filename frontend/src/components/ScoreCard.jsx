import { useEffect, useState } from 'react'

const PARTY_COLORS = {
  DMK:    { accent: '#22d3ee', track: 'rgba(34,211,238,.15)', glow: 'glow-dmk'  },
  AIADMK: { accent: '#f59e0b', track: 'rgba(245,158,11,.15)', glow: 'glow-AIADMK' },
}

export default function ScoreCard({ partyKey, data }) {
  const [animated, setAnimated] = useState(false)
  const party = partyKey.split(' ')[0]                    // 'DMK' or 'AIADMK'
  const year  = partyKey.split(' ')[1] || ''
  const color = PARTY_COLORS[party] || PARTY_COLORS.DMK

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(t)
  }, [])

  const score      = Math.round(data?.score      ?? 0)
  const fulfilled  = Math.round(data?.fulfilled  ?? 0)
  const total      = Math.round(data?.total      ?? 0)
  const topCat     = data?.top_category ?? '—'
  const context    = data?.context    ?? ''
  const period     = data?.period     ?? ''

  return (
    <div className={`glass ${color.glow} fade-up`} style={{ padding: 28, position: 'relative', overflow: 'hidden' }}>
      {/* Background accent blob */}
      <div style={{
        position: 'absolute', top: -40, right: -40,
        width: 140, height: 140, borderRadius: '50%',
        background: color.accent, opacity: .06, filter: 'blur(40px)',
        pointerEvents: 'none',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", color: color.accent }}>
            {party}
          </div>
          <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>
            {year} &nbsp;·&nbsp; {period}
          </div>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 600, padding: '3px 10px',
          borderRadius: 999, textTransform: 'uppercase', letterSpacing: '.06em',
          background: context === 'ruling' ? 'rgba(16,185,129,.15)' : 'rgba(148,163,184,.12)',
          color:      context === 'ruling' ? '#10b981' : '#94a3b8',
        }}>
          {context}
        </span>
      </div>

      {/* Big score */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 14 }}>
        <span style={{ fontSize: 52, fontWeight: 900, lineHeight: 1, fontFamily: "'Space Grotesk',sans-serif", color: color.accent }}>
          {score}
        </span>
        <span style={{ fontSize: 22, color: '#64748b', paddingBottom: 6 }}>%</span>
      </div>

      {/* Progress bar */}
      <div className="progress-track" style={{ marginBottom: 16 }}>
        <div
          className="progress-fill"
          style={{
            width: animated ? `${score}%` : '0%',
            background: `linear-gradient(90deg, ${color.accent}99, ${color.accent})`,
          }}
        />
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: 24 }}>
        <Stat label="Fulfilled" value={fulfilled} color="#10b981" />
        <Stat label="Total"     value={total}     color="#64748b" />
        <Stat label="Top Category" value={topCat} color={color.accent} isText />
      </div>
    </div>
  )
}

function Stat({ label, value, color, isText }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: '#475569', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 3 }}>
        {label}
      </div>
      <div style={{ fontSize: isText ? 13 : 20, fontWeight: isText ? 500 : 700, color, textTransform: isText ? 'capitalize' : 'none' }}>
        {value}
      </div>
    </div>
  )
}
