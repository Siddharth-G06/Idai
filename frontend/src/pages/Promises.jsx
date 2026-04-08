import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'
import PromiseCard from '../components/PromiseCard'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import { Search, Filter, Loader2 } from 'lucide-react'

const PARTIES    = ['DMK', 'AIADMK']
const YEARS      = [2016, 2021]
const CATEGORIES = ['', 'infrastructure', 'employment', 'economy', 'healthcare', 'education', 'agriculture', 'women and youth']
const STATUSES   = ['', 'fulfilled', 'unfulfilled']

function Select({ label, value, onChange, options }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.06em' }}>{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{
          background: '#1e293b', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 8, color: '#e2e8f0', padding: '8px 12px', fontSize: 13,
          cursor: 'pointer', outline: 'none',
        }}
      >
        {options.map(o => (
          <option key={o} value={o}>{o || `All ${label}s`}</option>
        ))}
      </select>
    </div>
  )
}

export default function Promises() {
  const [promises, setPromises] = useState([])
  const [total,    setTotal]    = useState(0)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  const [search,   setSearch]   = useState('')
  const [party,    setParty]    = useState('DMK')
  const [year,     setYear]     = useState('2021')
  const [category, setCategory] = useState('')
  const [status,   setStatus]   = useState('')
  const [page,     setPage]     = useState(0)

  const PAGE_SIZE = 30

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api.promises({ party, year: year || undefined, category: category || undefined, status: status || undefined })
      .then(res => {
        setTotal(res.count)
        setPromises(res.promises)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
    setPage(0)
  }, [party, year, category, status])

  useEffect(() => { load() }, [load])

  // Client-side search filter + pagination
  const filtered = promises.filter(p => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      (p.translated || '').toLowerCase().includes(q) ||
      (p.promise    || '').toLowerCase().includes(q) ||
      (p.category   || '').toLowerCase().includes(q)
    )
  })

  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px' }}>

      {/* Header */}
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <h1 style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 28, fontWeight: 800, color: '#f1f5f9', marginBottom: 6 }}>
          Promise Explorer
        </h1>
        <p style={{ fontSize: 13, color: '#64748b' }}>Filter and search {total.toLocaleString()} manifesto promises.</p>
      </div>

      {/* Filters */}
      <div className="glass" style={{ padding: '20px 24px', marginBottom: 24, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <Select label="Party"    value={party}    onChange={v => { setParty(v); setPage(0) }}    options={PARTIES} />
        <Select label="Year"     value={year}     onChange={v => { setYear(v); setPage(0) }}     options={['', ...YEARS.map(String)]} />
        <Select label="Category" value={category} onChange={v => { setCategory(v); setPage(0) }} options={CATEGORIES} />
        <Select label="Status"   value={status}   onChange={v => { setStatus(v); setPage(0) }}   options={STATUSES} />

        {/* Search */}
        <div style={{ flex: 1, minWidth: 200, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.06em' }}>Search</label>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#475569' }} />
            <input
              type="text"
              placeholder="Filter by keyword…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(0) }}
              style={{
                width: '100%', background: '#1e293b',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8, color: '#e2e8f0',
                padding: '8px 12px 8px 32px', fontSize: 13, outline: 'none',
              }}
            />
          </div>
        </div>
      </div>

      {/* Results info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 13, color: '#64748b' }}>
          {loading ? 'Loading…' : `${filtered.length.toLocaleString()} promises`}
          {search ? ` matching "${search}"` : ''}
        </span>
        {!loading && (
          <span style={{ fontSize: 12, color: '#334155' }}>
            Page {page + 1} / {totalPages || 1}
          </span>
        )}
      </div>

      {error && (
        <ErrorState 
          message={`We couldn't load the promises: ${error}`} 
          onRetry={load} 
        />
      )}

      {/* Promise list */}
      {loading
        ? <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[...Array(8)].map((_, i) => (
              <div key={i} className="skeleton h-24 rounded-2xl opacity-10" />
            ))}
          </div>
        : !error && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {paginated.length === 0
                ? <EmptyState message="No promises match your filters." />
                : paginated.map(p => <PromiseCard key={p.id} promise={p} />)
              }
            </div>
          )
      }

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 32 }}>
          <PageBtn disabled={page === 0}              onClick={() => setPage(p => p - 1)} label="← Prev" />
          {[...Array(Math.min(totalPages, 7))].map((_, i) => {
            const pg = totalPages <= 7 ? i : i + Math.max(0, page - 3)
            if (pg >= totalPages) return null
            return (
              <PageBtn key={pg} active={pg === page} onClick={() => setPage(pg)} label={pg + 1} />
            )
          })}
          <PageBtn disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} label="Next →" />
        </div>
      )}
    </div>
  )
}

function PageBtn({ label, onClick, disabled, active }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '6px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500,
        border: active ? '1px solid #22d3ee' : '1px solid rgba(255,255,255,0.08)',
        background: active ? 'rgba(34,211,238,.12)' : '#1e293b',
        color: disabled ? '#334155' : active ? '#22d3ee' : '#94a3b8',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all .18s',
      }}
    >
      {label}
    </button>
  )
}
