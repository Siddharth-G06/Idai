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

/**
 * PartyPage — shows all promises for a given party, with category + status filters.
 *
 * Props:
 *   party: 'DMK' | 'ADMK'
 *
 * Key fixes:
 * 1. Uses context='ruling' to select the right score entry (DMK 2021, AIADMK 2016)
 * 2. Passes both party + year to the API so only relevant promises load
 * 3. promisesData.promises (not .promises[]) — backend returns {count, promises:[]}
 */
export default function PartyPage({ party }) {
  // Backend filter: 'ADMK' → 'AIADMK'
  const queryParty = party === 'ADMK' ? 'AIADMK' : party

  // --- Score / category data from scores.json ---
  const { data: scoresData } = useScore()

  const scorePrefix = party === 'ADMK' ? 'AIADMK' : party
  let partyScore    = 0
  let partyYear     = ''
  let categoriesData = {}
  let queryYear      = undefined   // will be set once we know the ruling year

  if (scoresData) {
    const relevantKeys = Object.keys(scoresData).filter(k => k.startsWith(scorePrefix))
    // Prefer ruling context; fallback to highest year
    const rulingKey = relevantKeys.find(k => scoresData[k]?.context === 'ruling')
    const latestKey = rulingKey ?? relevantKeys.sort().reverse()[0]

    if (latestKey) {
      partyScore     = scoresData[latestKey]?.score      ?? 0
      partyYear      = latestKey.split(' ')[1]            ?? ''
      categoriesData = scoresData[latestKey]?.categories  ?? {}
      queryYear      = partyYear ? parseInt(partyYear, 10) : undefined
    }
  }

  // --- Promises: only fetch after we know the target year ---
  const { data: promisesData, isLoading: isLoadingPromises } = usePromises(
    queryYear
      ? { party: queryParty, year: queryYear }
      : { party: queryParty }
  )

  // Backend returns { count: N, promises: [...] }
  const rawPromises = promisesData?.promises ?? []

  // --- UI filter state ---
  const [selectedCat, setSelectedCat]       = useState('All')
  const [selectedStatus, setSelectedStatus] = useState('All')

  const isDMK    = party === 'DMK'
  const pBg      = isDMK ? 'bg-dmk-primary'         : 'bg-admk-primary'
  const pText    = isDMK ? 'text-dmk-primary'        : 'text-admk-primary'
  const pBorder  = isDMK ? 'border-dmk-primary'      : 'border-admk-primary'
  const pBgHover = isDMK ? 'hover:bg-dmk-primary/20' : 'hover:bg-admk-primary/20'

  // Client-side filtering (instant, no extra API call)
  const filteredPromises = rawPromises.filter(p => {
    if (selectedCat !== 'All') {
      const matchCat = selectedCat === 'Women & Youth' ? 'women and youth' : selectedCat.toLowerCase()
      if ((p.category ?? '').toLowerCase() !== matchCat) return false
    }
    if (selectedStatus === 'Addressed'     && (p.status ?? '').toLowerCase() !== 'fulfilled')   return false
    if (selectedStatus === 'Not addressed' && (p.status ?? '').toLowerCase() !== 'unfulfilled') return false
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
            {partyYear && (
              <span className="text-lg font-bold text-white/80">{partyYear} Manifesto</span>
            )}
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-widest text-white/80">
              Overall Score
            </span>
            <span className="text-3xl sm:text-4xl font-black tabular-nums">
              {partyScore.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* 2) Category Filter Chips */}
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
        <div className="flex gap-2 overflow-x-auto mt-2 pb-6 border-b border-navy-light [&::-webkit-scrollbar]:hidden">
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

        {/* 4) Category Score Summary Bars */}
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
