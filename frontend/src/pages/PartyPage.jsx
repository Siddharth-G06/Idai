import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { usePromises } from '../hooks/usePromises'
import { useScore } from '../hooks/useScore'
import PromiseCard from '../components/PromiseCard'

const CATEGORIES = [
  'All', 'Healthcare', 'Education', 'Infrastructure', 
  'Agriculture', 'Economy', 'Employment', 'Women & Youth'
]

const STATUSES = ['All', 'Addressed', 'Not addressed']

const SkeletonCard = () => (
  <div className="w-full bg-navy-card rounded-lg p-4 flex flex-col gap-4 animate-pulse shadow-sm min-h-[140px]">
    <div className="flex justify-between items-start">
      <div className="h-5 w-24 bg-gray-600/50 rounded-full"></div>
      <div className="h-5 w-28 bg-gray-600/50 rounded-full"></div>
    </div>
    <div className="h-4 w-full bg-gray-600/50 rounded-full mt-2"></div>
    <div className="h-4 w-[85%] bg-gray-600/50 rounded-full"></div>
    <div className="h-1.5 w-full bg-navy-light rounded-full mt-auto"></div>
  </div>
)

export default function PartyPage({ party }) {
  // Standardize 'ADMK' router string to 'AIADMK' for backend exact-matching
  const queryParty = party === 'ADMK' ? 'AIADMK' : party
  const { data: promisesData, isLoading: isLoadingPromises } = usePromises({ party: queryParty })
  const { data: scoresData } = useScore()

  const [selectedCat, setSelectedCat] = useState('All')
  const [selectedStatus, setSelectedStatus] = useState('All')

  const isDMK = party === 'DMK'
  
  // Hardcoded string literals guarantee Tailwind scanner binds the generated colors
  const pBg = isDMK ? 'bg-dmk-primary' : 'bg-admk-primary'
  const pText = isDMK ? 'text-dmk-primary' : 'text-admk-primary'
  const pBorder = isDMK ? 'border-dmk-primary' : 'border-admk-primary'
  const pBgHover = isDMK ? 'hover:bg-dmk-primary/20' : 'hover:bg-admk-primary/20'

  // Standardize party prefix for traversing scores.json map since ADMK keys might be 'AIADMK'
  const scorePrefix = isDMK ? 'DMK' : 'AIADMK'
  
  let partyScore = 0
  let partyYear = ''
  let categoriesData = {}

  if (scoresData) {
    // Find all matching keys (e.g. DMK 2021, DMK 2016), sort reverse to grab the most recent year
    const relevantKeys = Object.keys(scoresData).filter(k => k.startsWith(scorePrefix)).sort().reverse()
    const latestKey = relevantKeys[0]

    if (latestKey) {
      partyScore = scoresData[latestKey].score || 0
      partyYear = latestKey.split(' ')[1] || ''
      categoriesData = scoresData[latestKey].categories || {}
    }
  }

  const rawPromises = promisesData?.promises || []

  // Client-side filtering applies immediately
  const filteredPromises = rawPromises.filter(p => {
    // Category match
    if (selectedCat !== 'All') {
      const matchCat = selectedCat === 'Women & Youth' ? 'women and youth' : selectedCat.toLowerCase()
      if ((p.category || '').toLowerCase() !== matchCat) return false
    }

    // Status match
    if (selectedStatus === 'Addressed' && (p.status || '').toLowerCase() !== 'fulfilled') return false
    if (selectedStatus === 'Not addressed' && (p.status || '').toLowerCase() !== 'unfulfilled') return false

    return true
  })

  return (
    <div className="min-h-screen bg-navy text-gray-200">
      
      {/* 1) Party Header Bar */}
      <div className={`w-full ${pBg} text-white px-4 py-8 shadow-lg sticky top-0 z-10`}>
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <Link to="/" className="p-2 -ml-2 rounded-full hover:bg-black/20 transition-colors">
            <ArrowLeft size={24} />
          </Link>
          <div className="flex-1 flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{party}</h1>
            {partyYear && <span className="text-lg font-bold text-white/80">{partyYear} Manifesto</span>}
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-widest text-white/80">
              Overall Score
            </span>
            <span className="text-3xl sm:text-4xl font-black tabular-nums">{partyScore.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        
        {/* 2) Category Filter Chips (Horizontal Map) */}
        <div className="flex gap-2 overflow-x-auto pb-4 [&::-webkit-scrollbar]:hidden">
          {CATEGORIES.map(cat => {
            const active = selectedCat === cat
            return (
              <button
                key={cat}
                onClick={() => setSelectedCat(cat)}
                className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-semibold border-2 transition-all duration-200 shadow-sm ${
                  active 
                    ? `${pBg} text-white border-transparent` 
                    : `bg-transparent ${pText} ${pBorder} ${pBgHover}`
                }`}
              >
                {cat}
              </button>
            )
          })}
        </div>
        
        {/* 3) Status Filter Toggles */}
        <div className="flex gap-2 overflow-x-auto mt-2 pb-6 border-b border-navy-light [&::-webkit-scrollbar]:hidden mt-2">
          {STATUSES.map(stat => {
            const active = selectedStatus === stat
            return (
              <button
                key={stat}
                onClick={() => setSelectedStatus(stat)}
                className={`shrink-0 px-4 py-1.5 rounded-md text-sm font-bold border transition-all shadow-sm ${
                  active
                    ? `${pBg} text-white border-transparent`
                    : `bg-navy-card text-gray-400 border-gray-600 hover:bg-gray-700/50`
                }`}
              >
                {stat}
              </button>
            )
          })}
        </div>

        {/* 4) Category Score Summary Bars (Visible globally across all promises) */}
        {Object.keys(categoriesData).length > 0 && selectedCat === 'All' && (
          <div className="my-6 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 p-4 bg-navy-card rounded-xl border border-navy-light shadow-sm">
            {Object.entries(categoriesData)
              .sort((a, b) => b[1].score - a[1].score)
              .map(([cName, cData]) => (
                <div key={cName}>
                  <div className="flex justify-between text-xs mb-1.5 font-bold text-gray-300 uppercase tracking-wide">
                    <span>{cName === 'women and youth' ? 'Women & Youth' : cName}</span>
                    <span className={pText}>{cData.score.toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-navy-light/60 rounded-full overflow-hidden shadow-inner flex">
                    <div 
                      className={`h-full ${pBg} transition-all duration-1000 ease-out`} 
                      style={{ width: `${cData.score}%` }} 
                    />
                  </div>
                </div>
            ))}
          </div>
        )}

        {/* 5) Results Count Header */}
        <div className="mt-8 mb-4 flex justify-between items-end">
          <span className="text-sm text-gray-400 font-medium">
            Showing <strong className="text-gray-200">{filteredPromises.length}</strong> of {rawPromises.length} promises
          </span>
        </div>

        {/* 6) Promise List Feed */}
        <div className="flex flex-col gap-4 pb-12">
          {isLoadingPromises ? (
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          ) : filteredPromises.length === 0 ? (
            <div className="text-center py-16 bg-navy-card/50 text-gray-400 border-2 border-dashed border-gray-700 rounded-xl">
              <span className="text-lg font-medium">No promises found.</span>
              <p className="text-sm mt-1 opacity-70">Adjust your category or status filters.</p>
            </div>
          ) : (
            filteredPromises.map(p => <PromiseCard key={p.id} promise={p} />)
          )}
        </div>

      </div>
    </div>
  )
}
