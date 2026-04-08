import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { usePromises } from '../hooks/usePromises';
import { useScore } from '../hooks/useScore';
import { useLanguage } from '../i18n/LanguageContext';
import { COLORS } from '../styles/design-system';
import PromiseCard from '../components/PromiseCard';
import Navbar from '../components/Navbar';
import BottomNav from '../components/BottomNav';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { ArrowLeft, CheckCircle, XCircle, Clock, Languages, Loader2 } from 'lucide-react';

const CATEGORIES = [
  'All', 'Healthcare', 'Education', 'Infrastructure', 'Agriculture', 'Economy', 'Employment', 'Women & Youth'
];

export default function PartyPage() {
  const { partyId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const yearParam = queryParams.get('year');

  const { lang, setLang, t } = useLanguage();

  const toggleLanguage = () => {
    setLang(lang === 'en' ? 'ta' : 'en');
  };

  const [activeCategory, setActiveCategory] = useState('All');
  const [activeStatus, setActiveStatus] = useState('All');

  // Intelligent Prefetching
  const queryClient = useQueryClient();
  useEffect(() => {
    const otherParty = partyId.toLowerCase().includes('dmk') && !partyId.toLowerCase().includes('aiadmk') ? 'AIADMK' : 'DMK';
    queryClient.prefetchQuery({
      queryKey: ['promises', { party: otherParty }],
      queryFn: () => api.getPromises({ party: otherParty })
    });
  }, [partyId, queryClient]);

  const { 
    data, 
    fetchNextPage, 
    hasNextPage, 
    isFetchingNextPage, 
    isLoading: promisesLoading,
    isError: promisesError,
    refetch: refetchPromises
  } = usePromises({ 
    party: partyId,
    year: yearParam ? parseInt(yearParam) : undefined,
    category: activeCategory === 'All' ? undefined : activeCategory,
    status: activeStatus === 'All' ? undefined : (activeStatus === 'Addressed' ? 'fulfilled' : 'unfulfilled')
  });

  // Flatten promises from all pages
  const allPromises = useMemo(() => 
    data?.pages.flatMap(page => page.data) || [], 
  [data]);
  
  const { data: scores, isLoading: scoresLoading, isError: scoresError, refetch: refetchScores } = useScore();

  const partyKey = Object.keys(scores || {}).find(k => {
    const p = k.toLowerCase();
    const matchesParty = p.startsWith(partyId.toLowerCase()) || p.includes(partyId.toLowerCase());
    const matchesYear = yearParam ? k.includes(yearParam) : true;
    return matchesParty && matchesYear;
  });
  
  const partyData = scores?.[partyKey];
  const partyColor = partyId.toLowerCase().includes('dmk') && !partyId.toLowerCase().includes('aiadmk') ? '#ef404c' : '#2DC653';
  const isRuling = partyData?.context === 'ruling';

  // Infinite Scroll Trigger
  const loadMoreRef = useRef(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 1.0 }
    );
    if (loadMoreRef.current) observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [hasNextPage, fetchNextPage]);

  if (promisesLoading || scoresLoading) return (
    <div className="min-h-screen bg-[#061423] flex items-center justify-center p-6">
      <div className="w-full max-w-2xl space-y-8">
        <div className="h-48 glass rounded-3xl animate-pulse" />
        <div className="space-y-4">
          <div className="h-24 glass rounded-2xl animate-pulse" />
          <div className="h-24 glass rounded-2xl animate-pulse" />
          <div className="h-24 glass rounded-2xl animate-pulse" />
        </div>
      </div>
    </div>
  );

  if (promisesError || scoresError) return (
    <div className="min-h-screen bg-[#061423] flex items-center justify-center p-6">
      <ErrorState 
        message="We encountered an issue connecting to our servers. Please check your connection and try again."
        onRetry={() => { refetchPromises(); refetchScores(); }} 
      />
    </div>
  );

  return (
    <div className="min-h-screen pb-32 bg-background font-body text-on-surface selection:bg-primary/30">
      {/* Top AppBar */}
      <header className="fixed top-0 w-full z-50 bg-[#061423] flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/')}
            className="p-2 rounded-full hover:bg-slate-800/50 transition-colors active:scale-90"
          >
            <ArrowLeft className="text-secondary" size={24} />
          </button>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-widest text-slate-100 font-headline">IDAI</h1>
            <div className="flex items-center gap-2">
              <p className="text-[10px] uppercase tracking-widest text-on-surface-variant/60 font-label">
                {partyId.toUpperCase()} {partyData?.year || yearParam}
              </p>
              <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-bold uppercase tracking-widest ${
                isRuling ? 'bg-secondary/20 text-secondary' : 'bg-white/10 text-white/40'
              }`}>
                {isRuling ? 'Ruling' : 'Opposition'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={toggleLanguage}
            className="bg-[#1e2b3b] rounded-full px-4 py-1.5 flex items-center gap-2 border border-white/10 active:scale-95 transition-transform"
          >
            <span className="text-[10px] font-bold tracking-widest text-[#c4c6cc] uppercase">
              {lang === 'en' ? 'EN | தமிழ்' : 'தமிழ் | EN'}
            </span>
            <Languages size={14} className="text-secondary" />
          </button>
        </div>
      </header>

      <main className="pt-24 px-6 max-w-5xl mx-auto">
        {/* Hero Section */}
        <section className="mb-10 animate-in">
          <div 
            className="rounded-lg p-8 relative overflow-hidden shadow-2xl transition-all duration-700"
            style={{ 
              background: `linear-gradient(135deg, ${partyColor} 0%, ${partyId.toLowerCase().includes('dmk') && !partyId.toLowerCase().includes('aiadmk') ? '#92001c' : '#003c11'} 100%)` 
            }}
          >
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="text-5xl font-extrabold text-white font-headline tracking-tighter">
                      {partyId.toUpperCase()}
                    </h2>
                    <span className="text-white/60 text-xl font-light font-headline">{partyData?.year || yearParam}</span>
                  </div>
                  <p className="text-white/80 font-medium tracking-tight text-lg">
                    {partyData?.period} {t('party.manifesto')} · {Math.round(partyData?.score || 0)}% {t('party.addressed')}
                  </p>
                </div>
                <div className="flex flex-col items-end w-full md:w-48">
                  <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden mb-2">
                    <div 
                      className="bg-white h-full rounded-full transition-all duration-1000" 
                      style={{ width: `${partyData?.score || 0}%` }}
                    />
                  </div>
                  <span className="text-white/60 text-[9px] font-label uppercase tracking-widest">
                    {isRuling ? 'Governance Score' : 'Proposed Impact Score'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Navigation Filters */}
        <nav className="mb-8 flex gap-3 overflow-x-auto no-scrollbar pb-2 animate-in" style={{ animationDelay: '0.1s' }}>
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-6 py-2.5 rounded-full text-sm font-semibold whitespace-nowrap transition-all shadow-lg ${
                activeCategory === cat 
                  ? 'bg-on-primary-container text-white shadow-on-primary-container/20' 
                  : 'border border-white/10 text-on-surface-variant hover:bg-white/5'
              }`}
            >
              {t(`filters.${cat.toLowerCase().replace(' & ', 'and')}`) || cat}
            </button>
          ))}
        </nav>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-center mb-10 gap-4 animate-in" style={{ animationDelay: '0.2s' }}>
          <div className="bg-[#0f1c2c] p-1.5 rounded-full flex gap-1 border border-white/5">
            {['All', 'Addressed', 'Not Addressed'].map(status => (
              <button
                key={status}
                onClick={() => setActiveStatus(status)}
                className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
                  activeStatus === status 
                    ? 'text-on-surface bg-on-surface/10' 
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {t(`filters.${status === 'All' ? 'statusAll' : status === 'Addressed' ? 'fulfilled' : 'unfulfilled'}`) || status}
                {status === 'Addressed' && <CheckCircle size={14} className="text-secondary" />}
                {status === 'Not Addressed' && <XCircle size={14} className="text-error" />}
              </button>
            ))}
          </div>
          <div className="text-on-surface-variant/70 text-xs font-label uppercase tracking-widest">
            {t('party.showing')} <span className="text-on-surface font-bold">{allPromises.length}</span> {t('party.of')} {data?.pages[0]?.pagination?.total || 0} {t('party.promises')}
          </div>
        </div>

        {/* Promise Cards List */}
        <div className="space-y-6 mb-12">
          {allPromises.length > 0 ? (
            allPromises.map((p, idx) => (
              <div key={p.id} className="animate-in" style={{ animationDelay: `${0.1 + (idx % 20) * 0.05}s` }}>
                <PromiseCard promise={p} partyColor={partyColor} />
              </div>
            ))
          ) : (
            <EmptyState message={t('party.noResults') || "No promises found matching your current filters."} />
          )}

          {/* Load More / Loading State */}
          <div ref={loadMoreRef} className="pt-10 flex flex-col items-center">
            {isFetchingNextPage ? (
              <div className="flex items-center gap-3 text-secondary animate-pulse py-4">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-[10px] font-bold uppercase tracking-widest">Loading more...</span>
              </div>
            ) : hasNextPage ? (
              <button 
                onClick={() => fetchNextPage()}
                className="px-8 py-3 rounded-full bg-white/5 border border-white/10 text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:bg-white/10 transition-colors"
              >
                {t('common.loadMore') || 'Load More'}
              </button>
            ) : allPromises.length > 0 && (
              <p className="text-[10px] text-white/20 uppercase tracking-widest">
                No more promises to show
              </p>
            )}
          </div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
