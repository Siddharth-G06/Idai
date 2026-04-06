const CATEGORY_COLORS = {
  infrastructure:   '#6366f1',
  employment:       '#22d3ee',
  economy:          '#f59e0b',
  healthcare:       '#ec4899',
  education:        '#10b981',
  agriculture:      '#84cc16',
  'women and youth':'#a78bfa',
}

export default function CategoryBar({ categories = {} }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {Object.entries(categories)
        .sort((a, b) => b[1].score - a[1].score)
        .map(([cat, { score, fulfilled, total }]) => {
          const color = CATEGORY_COLORS[cat] || '#64748b'
          return (
            <div key={cat}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                <span style={{ fontSize: 12, fontWeight: 500, color: '#cbd5e1', textTransform: 'capitalize' }}>{cat}</span>
                <span style={{ fontSize: 11, color: '#64748b' }}>{fulfilled}/{total} · <span style={{ color }}>{score.toFixed(0)}%</span></span>
              </div>
              <div className="progress-track" style={{ height: 6 }}>
                <div
                  className="progress-fill"
                  style={{ width: `${score}%`, background: color, transition: 'width 1s ease' }}
                />
              </div>
            </div>
          )
        })}
    </div>
  )
}
