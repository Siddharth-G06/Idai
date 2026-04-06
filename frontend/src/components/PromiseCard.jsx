import { ExternalLink } from 'lucide-react'

export default function PromiseCard({ promise }) {
  const {
    translated, promise: original, category, status,
    similarity_score, matched_headline, matched_url, matched_date,
    llm_verdict, llm_reason,
  } = promise

  const fulfilled = status === 'fulfilled'
  const score     = ((similarity_score ?? 0) * 100).toFixed(0)

  return (
    <div className="glass fade-up" style={{
      padding: '18px 20px',
      borderLeft: `3px solid ${fulfilled ? '#10b981' : '#ef4444'}`,
      transition: 'transform .18s, box-shadow .18s',
    }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
    >
      {/* Top row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 8 }}>
        <p style={{ fontSize: 13.5, fontWeight: 500, color: '#e2e8f0', lineHeight: 1.5, flex: 1 }}>
          {translated || original}
        </p>
        <span className={`pill ${fulfilled ? 'pill-fulfilled' : 'pill-unfulfilled'}`} style={{ flexShrink: 0 }}>
          {fulfilled ? '✓ Done' : '✗ Pending'}
        </span>
      </div>

      {/* Category + score */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: matched_headline ? 12 : 0 }}>
        <Tag label={category} />
        <span style={{ fontSize: 11, color: '#64748b' }}>Score: <b style={{ color: '#94a3b8' }}>{score}%</b></span>
        {llm_verdict && (
          <span style={{ fontSize: 11, color: llm_verdict === 'yes' ? '#10b981' : '#64748b' }}>
            LLM: {llm_verdict}
          </span>
        )}
      </div>

      {/* Matched article */}
      {matched_headline && (
        <div style={{
          background: 'rgba(255,255,255,0.04)',
          borderRadius: 8,
          padding: '8px 12px',
          fontSize: 12,
          color: '#64748b',
        }}>
          <span style={{ color: '#475569' }}>Matched: </span>
          {matched_url ? (
            <a href={matched_url} target="_blank" rel="noopener noreferrer"
               style={{ color: '#7dd3fc', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
              {matched_headline.slice(0, 90)}{matched_headline.length > 90 ? '…' : ''}
              <ExternalLink size={10} />
            </a>
          ) : (
            <span>{matched_headline.slice(0, 90)}</span>
          )}
        </div>
      )}

      {/* LLM reason */}
      {llm_reason && !llm_reason.startsWith('Error code') && (
        <p style={{ fontSize: 11, color: '#475569', marginTop: 6, fontStyle: 'italic' }}>
          "{llm_reason.slice(0, 120)}{llm_reason.length > 120 ? '…' : ''}"
        </p>
      )}
    </div>
  )
}

function Tag({ label }) {
  const COLORS = {
    infrastructure: '#6366f1', employment: '#22d3ee', economy: '#f59e0b',
    healthcare: '#ec4899', education: '#10b981', agriculture: '#84cc16',
    'women and youth': '#a78bfa',
  }
  const c = COLORS[label] || '#64748b'
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 999,
      background: `${c}22`, color: c, textTransform: 'capitalize',
    }}>
      {label}
    </span>
  )
}
