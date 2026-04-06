import { useEffect, useState } from 'react'

export default function ScoreRing({ score = 0, color = "#10b981", size = 120 }) {
  const strokeWidth = Math.max(size * 0.08, 4) // adjust track thickness dynamically
  const center = size / 2
  const radius = center - strokeWidth
  const circumference = 2 * Math.PI * radius
  
  // Start fully offset (empty ring) to trigger transition on mount
  const [offset, setOffset] = useState(circumference)

  useEffect(() => {
    // Small timeout ensures the DOM has rendered the empty ring before transitioning
    const t = setTimeout(() => {
      const finalOffset = circumference - (Math.max(0, Math.min(100, score)) / 100) * circumference
      setOffset(finalOffset)
    }, 50)
    return () => clearTimeout(t)
  }, [score, circumference])

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Background Track */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke="rgba(255, 255, 255, 0.08)"
        strokeWidth={strokeWidth}
      />
      {/* Animated Foreground Ring */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{
          transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: 'rotate(-90deg)',
          transformOrigin: '50% 50%'
        }}
      />
      {/* Text Group */}
      <text x="50%" y="45%" textAnchor="middle" dominantBaseline="central">
        <tspan 
          fill="#f1f5f9" 
          fontSize={size * 0.26} 
          fontWeight="800" 
          fontFamily="'Space Grotesk', system-ui, sans-serif"
        >
          {Number(score).toFixed(0)}
        </tspan>
        <tspan 
          fill="#94a3b8" 
          fontSize={size * 0.14} 
          fontWeight="600" 
          dx="2"
        >
          %
        </tspan>
      </text>
      <text 
        x="50%" 
        y="68%" 
        textAnchor="middle" 
        dominantBaseline="central"
        fill="#64748b"
        fontSize={size * 0.1}
        fontWeight="600"
        letterSpacing="0.04em"
        style={{ textTransform: 'uppercase' }}
      >
        addressed
      </text>
    </svg>
  )
}
