import { Link } from 'react-router-dom'
import { useScore } from '../hooks/useScore'
import ScoreRing from '../components/ScoreRing'

/**
 * Home page — shows DMK 2021 (ruling) and AIADMK 2016 (ruling) score rings.
 *
 * Key fix: `.find()` returns the FIRST matching key. scores.json insertion order
 * is AIADMK-2016 → AIADMK-2021 → DMK-2016 → DMK-2021, so naïve `.find()` on
 * 'DMK' picks "DMK 2016" instead of "DMK 2021". We now filter by year explicitly.
 */
export default function Home() {
  const { data: scores, isLoading, error } = useScore()

  // Prefer the "ruling" entry (context === 'ruling'), falling back to highest year
  function getBestKey(prefix) {
    if (!scores) return null
    const matches = Object.keys(scores).filter(k => k.startsWith(prefix))
    // First try to find ruling context
    const ruling = matches.find(k => scores[k]?.context === 'ruling')
    if (ruling) return ruling
    // Fallback: highest year
    return matches.sort().reverse()[0] ?? null
  }

  const dmkKey  = getBestKey('DMK')
  const admkKey = getBestKey('AIADMK')

  const dmkData  = dmkKey  ? scores?.[dmkKey]  : null
  const admkData = admkKey ? scores?.[admkKey] : null

  const dmkYear  = dmkKey?.split(' ')[1]  ?? '2021'
  const admkYear = admkKey?.split(' ')[1] ?? '2016'

  return (
    <div className="max-w-4xl mx-auto py-10 flex flex-col items-center selection:bg-dmk-primary/30">
      <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-dmk-primary to-admk-primary mb-4 text-center font-tamil tracking-tight">
        வாக்காளிபீர்
      </h1>
      <p className="text-gray-400 mb-12 text-center max-w-md font-medium leading-relaxed">
        Hold Tamil Nadu political parties accountable to their election manifestos with data-driven promise tracking.
      </p>

      {/* Error banner — shown when backend is unreachable */}
      {error && (
        <div className="mb-8 p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg max-w-lg text-center text-sm">
          ⚠️ Could not connect to the backend API. Make sure FastAPI is running on{' '}
          <code className="font-mono bg-red-900/30 px-1 rounded">localhost:8000</code>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-3xl px-4">

        {/* DMK Card */}
        <Link
          to="/party/dmk"
          className="bg-navy-card hover:bg-navy-light/80 transition-all rounded-2xl p-8 border-b-4 border-dmk-primary border-t border-t-white/5 flex flex-col items-center shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-dmk-primary/10 group"
        >
          <h2 className="text-4xl font-black text-white mb-1 group-hover:text-dmk-light transition-colors">DMK</h2>
          <span className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.15em] mb-8">
            Manifesto {dmkYear}
          </span>

          {isLoading ? (
            <div className="w-[140px] h-[140px] rounded-full bg-navy-light animate-pulse" />
          ) : (
            <ScoreRing score={dmkData?.score ?? 0} color="#E63946" size={140} />
          )}

          <div className="mt-8 px-4 py-2 rounded-full bg-dmk-primary/10 text-dmk-primary text-xs font-bold transition-all group-hover:bg-dmk-primary group-hover:text-white">
            Explore {dmkYear} Promises →
          </div>
        </Link>

        {/* ADMK Card */}
        <Link
          to="/party/admk"
          className="bg-navy-card hover:bg-navy-light/80 transition-all rounded-2xl p-8 border-b-4 border-admk-primary border-t border-t-white/5 flex flex-col items-center shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-admk-primary/10 group"
        >
          <h2 className="text-4xl font-black text-white mb-1 group-hover:text-admk-light transition-colors">ADMK</h2>
          <span className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.15em] mb-8">
            Manifesto {admkYear}
          </span>

          {isLoading ? (
            <div className="w-[140px] h-[140px] rounded-full bg-navy-light animate-pulse" />
          ) : (
            <ScoreRing score={admkData?.score ?? 0} color="#2DC653" size={140} />
          )}

          <div className="mt-8 px-4 py-2 rounded-full bg-admk-primary/10 text-admk-primary text-xs font-bold transition-all group-hover:bg-admk-primary group-hover:text-white">
            Explore {admkYear} Promises →
          </div>
        </Link>

      </div>
    </div>
  )
}
