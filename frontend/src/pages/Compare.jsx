import { useScore } from '../hooks/useScore'
import ScoreRing from '../components/ScoreRing'

const CATEGORIES = [
  { key: 'healthcare', label: 'Healthcare' },
  { key: 'education', label: 'Education' },
  { key: 'infrastructure', label: 'Infrastructure' },
  { key: 'agriculture', label: 'Agriculture' },
  { key: 'economy', label: 'Economy' },
  { key: 'employment', label: 'Employment' },
  { key: 'women and youth', label: 'Women & Youth' },
]

export default function Compare() {
  const { data: scores, isLoading } = useScore()

  if (isLoading) {
    return <div className="h-full w-full flex items-center justify-center p-20 text-gray-500 font-medium animate-pulse">Loading Head-to-Head Data...</div>
  }

  // Robustly extract latest DMK and ADMK score chunks
  const dmkKey = Object.keys(scores || {}).filter(k => k.startsWith('DMK')).sort().reverse()[0]
  const admkKey = Object.keys(scores || {}).filter(k => k.startsWith('AIADMK') || k.startsWith('ADMK')).sort().reverse()[0]

  const dmkData = (scores && dmkKey) ? scores[dmkKey] : {}
  const admkData = (scores && admkKey) ? scores[admkKey] : {}

  const dmkScore = dmkData.score || 0
  const admkScore = admkData.score || 0

  const winner = dmkScore >= admkScore ? 'DMK' : 'ADMK'
  const bannerBg = winner === 'DMK' ? 'bg-dmk-primary' : 'bg-admk-primary'
  
  const topScore = Math.max(dmkScore, admkScore).toFixed(1)
  const bottomScore = Math.min(dmkScore, admkScore).toFixed(1)
  const loserName = winner === 'DMK' ? 'ADMK' : 'DMK'

  return (
    <div className="w-full max-w-3xl mx-auto py-8 lg:py-12 flex flex-col md:px-0">
      
      {/* Heavy Header */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight uppercase">
          <span className="text-dmk-primary shadow-sm drop-shadow-md">DMK</span> 
          <span className="text-gray-500 italic lowercase mx-3 font-medium text-2xl">vs</span> 
          <span className="text-admk-primary shadow-sm drop-shadow-md">ADMK</span>
        </h1>
        <p className="text-xs sm:text-sm text-gray-400 mt-2 tracking-widest uppercase font-semibold">
          Promises Delivered Head-to-Head
        </p>
      </div>

      {/* Duel Rings */}
      <div className="flex justify-center items-center gap-2 sm:gap-10 mb-12">
        <div className="flex flex-col items-center">
          <h2 className="text-2xl font-black text-white mb-3 tracking-widest">DMK</h2>
          <ScoreRing score={dmkScore} color="#E63946" size={140} />
        </div>
        <div className="text-3xl font-black text-navy-light italic pb-8 mx-2 sm:mx-6">VS</div>
        <div className="flex flex-col items-center">
          <h2 className="text-2xl font-black text-white mb-3 tracking-widest">ADMK</h2>
          <ScoreRing score={admkScore} color="#2DC653" size={140} />
        </div>
      </div>

      {/* Category Breakdowns (Scrollable Container for Mobile Edge Cases) */}
      <div className="w-full overflow-x-auto pb-4 [&::-webkit-scrollbar]:hidden px-2 mb-6">
        <div className="min-w-[340px] flex flex-col gap-3">
          {CATEGORIES.map(cat => {
            const dmkCatScore = dmkData.categories?.[cat.key]?.score || 0
            const admkCatScore = admkData.categories?.[cat.key]?.score || 0
            
            // Winning side highlights brighter
            const dmkWins = dmkCatScore >= admkCatScore
            const admkWins = admkCatScore >= dmkCatScore

            return (
              <div key={cat.key} className="grid grid-cols-[1fr_minmax(85px,auto)_1fr] sm:grid-cols-[1fr_minmax(120px,auto)_1fr] gap-x-2 items-center">
                
                {/* DMK Bar (Left Column -> Pushes filling from Right edge) */}
                <div className="relative w-full h-8 sm:h-9 bg-navy-card/80 border border-navy-light rounded-sm overflow-hidden flex items-center justify-end">
                  <div 
                    className={`absolute inset-y-0 right-0 transition-all duration-1000 ease-out ${dmkWins ? 'bg-dmk-primary' : 'bg-dmk-dark/50'}`}
                    style={{ width: `${dmkCatScore}%` }}
                  />
                  {/* Floating Number Overlay locked tightly to axis */}
                  <span className="relative z-10 text-[11px] sm:text-xs font-black text-white mr-2.5 drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)] tabular-nums tracking-wider">
                    {dmkCatScore.toFixed(0)}%
                  </span>
                </div>

                {/* Shared Axis Marker */}
                <div className="text-[9px] sm:text-[11px] font-bold uppercase tracking-widest text-center text-gray-400 break-words leading-tight px-1 font-tamil">
                  {cat.label}
                </div>

                {/* ADMK Bar (Right Column -> Pushes filling from Left edge) */}
                <div className="relative w-full h-8 sm:h-9 bg-navy-card/80 border border-navy-light rounded-sm overflow-hidden flex items-center justify-start">
                  <div 
                    className={`absolute inset-y-0 left-0 transition-all duration-1000 ease-out ${admkWins ? 'bg-admk-primary' : 'bg-admk-dark/50'}`}
                    style={{ width: `${admkCatScore}%` }}
                  />
                  {/* Floating Number Overlay locked tightly to axis */}
                  <span className="relative z-10 text-[11px] sm:text-xs font-black text-white ml-2.5 drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)] tabular-nums tracking-wider">
                    {admkCatScore.toFixed(0)}%
                  </span>
                </div>

              </div>
            )
          })}
        </div>
      </div>

      {/* Winner Banner */}
      <div className={`mx-2 sm:mx-0 mt-6 px-6 py-5 rounded-2xl shadow-xl flex justify-center items-center transform transition-all ${bannerBg} group cursor-default hover:scale-[1.01]`}>
        <span className="text-sm sm:text-base font-extrabold text-white tracking-widest md:tracking-[0.1em] text-center drop-shadow-sm uppercase">
          Overall: {winner} leads with <span className="text-white/90 underline decoration-2 underline-offset-4">{topScore}%</span> vs {loserName} <span className="opacity-80">{bottomScore}%</span>
        </span>
      </div>

    </div>
  )
}
