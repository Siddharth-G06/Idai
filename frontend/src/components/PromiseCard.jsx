import { useState, useRef, useEffect } from 'react'

const CAT_COLORS = {
  healthcare: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  education: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  infrastructure: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  agriculture: 'bg-green-500/10 text-green-400 border-green-500/20',
  economy: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  employment: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  'women and youth': 'bg-pink-500/10 text-pink-400 border-pink-500/20',
}

const STATUS_BADGES = {
  fulfilled: { label: 'Addressed ✓', style: 'bg-green-500/10 text-green-400 border-green-500/20' },
  unfulfilled: { label: 'Not addressed ✗', style: 'bg-red-500/10 text-red-500 border-red-500/20' },
  pending: { label: 'Pending', style: 'bg-gray-500/10 text-gray-400 border-gray-500/20' }
}

export default function PromiseCard({ promise }) {
  const [expanded, setExpanded] = useState(false)
  const [isClamped, setIsClamped] = useState(false)
  const textRef = useRef(null)

  useEffect(() => {
    if (textRef.current) {
      // Check if text is naturally taller than its CSS-clamped box container
      if (textRef.current.scrollHeight > textRef.current.clientHeight + 2) {
        setIsClamped(true)
      }
    }
  }, [])

  // 1) Category mapping
  const catKey = (promise.category || '').toLowerCase()
  const catStyle = CAT_COLORS[catKey] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'

  // 2) Status mapping
  const statKey = (promise.status || '').toLowerCase()
  // Often data has "fulfilled" and "unfulfilled". Map appropriately, fallback to pending.
  const badgeObj = STATUS_BADGES[statKey] || STATUS_BADGES.pending

  // 3) Party detection for left border color
  const ident = (promise.party || promise.id || '').toLowerCase()
  // "aiadmk" or "admk" goes to ADMK (green). "dmk" alone goes to DMK (red).
  let borderClass = 'border-navy-light'
  if (ident.includes('admk') || ident.includes('aiadmk')) {
    borderClass = 'border-admk-primary'
  } else if (ident.includes('dmk')) {
    borderClass = 'border-dmk-primary'
  }

  // 4) Promise data extraction
  const text = promise.translated || promise.promise || 'No promise text provided.'
  const matchScore = ((promise.similarity_score || 0) * 100).toFixed(0)
  const hasMatchedURL = promise.matched_url && promise.matched_url.trim().length > 0
  const hasHeadline = promise.matched_headline && promise.matched_headline.trim().length > 0

  return (
    <div className={`w-full bg-navy-card rounded-lg border-l-4 ${borderClass} p-4 flex flex-col gap-3 shadow-sm`}>
      
      {/* Top row */}
      <div className="flex justify-between items-start gap-2">
        <span className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.06em] rounded-full border ${catStyle}`}>
          {promise.category || 'Uncategorized'}
        </span>
        <span className={`px-2.5 py-1 text-[11px] font-bold rounded-full border ${badgeObj.style}`}>
          {badgeObj.label}
        </span>
      </div>

      {/* Middle row: Promise Statement */}
      <div className="flex flex-col gap-1 w-full">
        <p 
          ref={textRef}
          onClick={() => { if (isClamped) setExpanded(!expanded) }}
          className={`text-sm text-gray-200 leading-relaxed font-tamil cursor-pointer transition-all ${expanded ? '' : 'line-clamp-3'}`}
          title={isClamped && !expanded ? "Tap to expand" : ""}
          style={{
             display: expanded ? 'block' : '-webkit-box',
             WebkitLineClamp: expanded ? 'unset' : 3,
             WebkitBoxOrient: 'vertical',
             overflow: 'hidden'
          }}
        >
          {text}
        </p>
        
        {/* Toggle Button */}
        {(isClamped || expanded) && (
          <button 
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-blue-400 hover:text-blue-300 self-start mt-0.5 font-medium transition-colors"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Bottom row: Matching details */}
      <div className="mt-1 pt-3 border-t border-navy-light/60 flex flex-col gap-2">
        
        {/* Score indicator bar */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold font-tamil text-gray-400 whitespace-nowrap">
            Match: {matchScore}%
          </span>
          <div className="flex-1 h-1.5 bg-navy-light rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${matchScore}%` }}
            />
          </div>
        </div>

        {/* Source citation */}
        {hasHeadline && (
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-baseline gap-1.5 mt-0.5">
             <span className="text-xs text-gray-400 italic truncate flex-1 block font-tamil">
               {promise.matched_headline}
             </span>
             {hasMatchedURL && (
               <a 
                 href={promise.matched_url} 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="text-[11px] font-bold uppercase tracking-wider text-dmk-light hover:text-dmk-primary shrink-0 transition-colors inline-flex items-center gap-1"
               >
                 Read article →
               </a>
             )}
          </div>
        )}

      </div>
    </div>
  )
}
