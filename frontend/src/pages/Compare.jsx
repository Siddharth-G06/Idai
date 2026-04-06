import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import CategoryBar from '../components/CategoryBar'

const PARTY_OPTS = [
  { key: 'DMK 2021',   label: 'DMK 2021',   color: '#22d3ee' },
  { key: 'DMK 2016',   label: 'DMK 2016',   color: '#38bdf8' },
  { key: 'AIADMK 2021',label: 'AIADMK 2021',color: '#f59e0b' },
  { key: 'AIADMK 2016',label: 'AIADMK 2016',color: '#fbbf24' },
]

function Panel({ children, style = {} }) {
  return <div className="glass fade-up" style={{ padding: 24, ...style }}>{children}</div>
}

function Radio({ opts, value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      {opts.map(o => (
        <button
          key={o.key}
          onClick={() => onChange(o.key)}
          style={{
            padding: '6px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500,
            border: `1px solid ${value === o.key ? o.color : 'rgba(255,255,255,0.08)'}`,
            background: value === o.key ? `${o.color}18` : '#1a2535',
            color: value === o.key ? o.color : '#64748b',
            cursor: 'pointer', transition: 'all .18s',
          }}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export default function Compare() {
  const [summary, setSummary] = useState(null)
  const [leftKey, setLeftKey]  = useState('DMK 2021')
  const [rightKey, setRightKey]= useState('AIADMK 2021')

  useEffect(() => {
    api.summary().then(setSummary).catch(console.error)
  }, [])

  if (!summary) {
    return (
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '80px 24px', textAlign: 'center', color: '#64748b' }}>
        Loading summary…
      </div>
    )
  }

  const left  = summary[leftKey]
  const right = summary[rightKey]

  const leftColor  = PARTY_OPTS.find(o => o.key === leftKey)?.color  ?? '#22d3ee'
  const rightColor = PARTY_OPTS.find(o => o.key === rightKey)?.color ?? '#f59e0b'

  // Build bar chart data from categories shared between both parties
  const allCats = new Set([
    ...Object.keys(left?.categories  ?? {}),
    ...Object.keys(right?.categories ?? {}),
  ])
  const barData = [...allCats].map(cat => ({
    category: cat.replace('women and youth', 'Women & Youth'),
    [leftKey]:  left?.categories?.[cat]?.score  ?? 0,
    [rightKey]: right?.categories?.[cat]?.score ?? 0,
  })).sort((a, b) => ((b[leftKey] + b[rightKey]) / 2) - ((a[leftKey] + a[rightKey]) / 2))

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>

      {/* Header */}
      <div className="fade-up" style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 28, fontWeight: 800, color: '#f1f5f9', marginBottom: 6 }}>
          Head-to-Head Comparison
        </h1>
        <p style={{ fontSize: 13, color: '#64748b' }}>Select two party–year combinations to compare performance.</p>
      </div>

      {/* Selectors */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 32 }}>
        <Panel>
          <p style={{ fontSize: 11, color: '#64748b', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.06em' }}>Left Panel</p>
          <Radio opts={PARTY_OPTS} value={leftKey} onChange={setLeftKey} />
        </Panel>
        <Panel>
          <p style={{ fontSize: 11, color: '#64748b', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.06em' }}>Right Panel</p>
          <Radio opts={PARTY_OPTS} value={rightKey} onChange={setRightKey} />
        </Panel>
      </div>

      {/* Score hero row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 20, alignItems: 'center', marginBottom: 32 }}>
        <ScoreHero data={left}  label={leftKey}  color={leftColor}  />
        <div style={{ textAlign: 'center', fontSize: 18, fontWeight: 700, color: '#334155' }}>vs</div>
        <ScoreHero data={right} label={rightKey} color={rightColor} />
      </div>

      {/* Bar chart */}
      <Panel style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 20 }}>Category Score Comparison</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="category" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              formatter={v => `${v.toFixed(1)}%`}
            />
            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
            <Bar dataKey={leftKey}  fill={leftColor}  radius={[4,4,0,0]} />
            <Bar dataKey={rightKey} fill={rightColor} radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>

      {/* Side-by-side category breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <Panel>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: leftColor, marginBottom: 16 }}>{leftKey} Breakdown</h3>
          {left?.categories ? <CategoryBar categories={left.categories} /> : <p style={{ color: '#475569' }}>No data</p>}
        </Panel>
        <Panel>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: rightColor, marginBottom: 16 }}>{rightKey} Breakdown</h3>
          {right?.categories ? <CategoryBar categories={right.categories} /> : <p style={{ color: '#475569' }}>No data</p>}
        </Panel>
      </div>
    </div>
  )
}

function ScoreHero({ data, label, color }) {
  const score     = data?.score     ?? 0
  const fulfilled = data?.fulfilled ?? 0
  const total     = data?.total     ?? 0
  const context   = data?.context   ?? ''

  return (
    <div className="glass" style={{ padding: 24, textAlign: 'center', borderTop: `3px solid ${color}` }}>
      <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>{label}</div>
      <div style={{
        fontSize: 48, fontWeight: 900, fontFamily: "'Space Grotesk',sans-serif",
        color, lineHeight: 1, marginBottom: 8,
      }}>
        {score.toFixed(1)}<span style={{ fontSize: 22, color: '#64748b' }}>%</span>
      </div>
      <div style={{ fontSize: 12, color: '#475569' }}>
        {fulfilled.toLocaleString()} / {total.toLocaleString()} · {context}
      </div>
    </div>
  )
}
