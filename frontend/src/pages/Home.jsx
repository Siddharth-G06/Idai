import React, { useState } from 'react';
import { useSummary } from '../hooks/useSummary';
import { useHealth } from '../hooks/useHealth';
import { useLanguage } from '../i18n/LanguageContext';
import ScoreRing from '../components/ScoreRing';
import Navbar from '../components/Navbar';
import BottomNav from '../components/BottomNav';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { COLORS } from '../styles/design-system';
import { Link } from 'react-router-dom';

export default function Home() {
  const { t } = useLanguage();
  const { data: scores, isLoading, isError, refetch } = useSummary();
  const { data: health } = useHealth();

  // Group scores by party
  const groupedScores = scores ? Object.values(scores).reduce((acc, curr) => {
    const partyName = curr.party;
    if (!acc[partyName]) acc[partyName] = [];
    acc[partyName].push(curr);
    return acc;
  }, {}) : {};

  // Track selected year for each party (default to latest)
  const [selectedYears, setSelectedYears] = useState({});

  const parties = Object.keys(groupedScores).sort();

  if (isError) return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <ErrorState 
        message="Unable to load the accountability summary. Please check your internet connection." 
        onRetry={refetch} 
      />
    </div>
  );

  if (isLoading) return (
    <div className="min-h-screen bg-background p-6 pt-24 space-y-8 max-w-md mx-auto">
      <div className="h-20 glass rounded-2xl animate-pulse" />
      {[1, 2].map(i => (
        <div key={i} className="h-64 glass rounded-3xl animate-pulse" />
      ))}
    </div>
  );

  return (
    <div className="min-h-screen pb-32 bg-background">
      <Navbar />

      <main className="pt-24 px-6 max-w-md mx-auto">
        {/* Hero Section */}
        <section className="mb-12 animate-in text-center">
          <h1 className="font-headline font-extrabold text-4xl leading-tight tracking-tight mb-4 text-on-surface">
            {t('home.heroHeadingLine1')}{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-br from-error via-white to-secondary">
              {t('home.heroHeadingLine2')}
            </span>
          </h1>
          <p className="text-on-surface-variant font-light leading-relaxed">
            {t('home.heroSub')}
          </p>
        </section>

        {/* Party Cards */}
        <div className="space-y-8 mb-12">
          {parties.length > 0 ? parties.map((partyName, idx) => {
            const history = groupedScores[partyName].sort((a, b) => (b.year || 0) - (a.year || 0));
            const selectedYear = selectedYears[partyName] || history[0].year;
            const entry = history.find(h => h.year === selectedYear) || history[0];
            
            const partyId = partyName.toLowerCase();
            const partyColor = partyId.includes('dmk') && !partyId.includes('aiadmk') ? '#E63946' : '#2DC653';
            const isRuling = entry.context === 'ruling';
            
            return (
              <div 
                key={partyName}
                className="glass-card rounded-lg p-6 border border-white/5 relative overflow-hidden animate-in" 
                style={{ animationDelay: `${0.1 + idx * 0.1}s` }}
              >
                <div 
                  className="absolute top-0 left-0 w-1.5 h-full" 
                  style={{ backgroundColor: partyColor }}
                />
                
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-headline font-bold text-2xl text-white">{partyName}</h2>
                      <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-widest ${
                        isRuling ? 'bg-secondary/20 text-secondary' : 'bg-white/10 text-white/40'
                      }`}>
                        {isRuling ? 'Ruling' : 'Opposition'}
                      </span>
                    </div>
                    <p className="text-[10px] tracking-widest text-on-surface-variant uppercase mt-1">
                      {entry.period} {t('party.manifesto')}
                    </p>
                  </div>
                  <div className="relative flex items-center justify-center w-16 h-16">
                    <ScoreRing score={entry.score} color={partyColor} size={64} hideLabel />
                  </div>
                </div>

                {/* Year Switcher */}
                <div className="flex bg-white/5 p-1 rounded-md mb-8 w-fit">
                  {history.map(h => (
                    <button
                      key={h.year}
                      onClick={() => setSelectedYears(prev => ({ ...prev, [partyName]: h.year }))}
                      className={`px-3 py-1 text-[10px] font-bold rounded transition-all ${
                        selectedYear === h.year 
                          ? 'bg-white/10 text-white shadow-sm' 
                          : 'text-white/40 hover:text-white/60'
                      }`}
                    >
                      {h.year}
                    </button>
                  ))}
                </div>
                
                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="bg-surface-container-lowest/50 p-3 rounded-md border border-white/5">
                    <span className="block text-[10px] text-on-surface-variant font-headline tracking-wider uppercase mb-1">Total</span>
                    <span className="text-lg font-headline font-bold text-white">{Math.round(entry.total)}</span>
                  </div>
                  <div className="bg-surface-container-lowest/50 p-3 rounded-md border border-white/5">
                    <span className="block text-[10px] text-on-surface-variant font-headline tracking-wider uppercase mb-1">Fulfilled</span>
                    <span className="text-lg font-headline font-bold text-white">{Math.round(entry.fulfilled)}</span>
                  </div>
                  <div className="bg-surface-container-lowest/50 p-3 rounded-md border border-white/5 text-ellipsis overflow-hidden">
                    <span className="block text-[10px] text-on-surface-variant font-headline tracking-wider uppercase mb-1">Top Cat.</span>
                    <span className="text-xs font-headline font-bold leading-tight text-white capitalize">
                      {entry.top_category?.split(' ')[0] || '—'}
                    </span>
                  </div>
                </div>
                
                <Link 
                  to={`/parties/${partyId}?year=${selectedYear}`}
                  className="block w-full text-center py-4 text-white font-headline font-bold rounded-full transition-all active:scale-95 shadow-lg"
                  style={{ 
                    background: `linear-gradient(135deg, ${partyColor} 0%, ${partyName.toLowerCase().includes('dmk') && !partyName.toLowerCase().includes('aiadmk') ? '#3e0006' : '#003910'} 100%)`,
                    boxShadow: `0 10px 20px -5px ${partyColor}40`
                  }}
                >
                  {t('home.viewDetails')}
                </Link>
              </div>
            );
          }) : (
            <EmptyState message="No party data available at the moment." />
          )}
        </div>

        {/* Status Indicator */}
        <div className="flex flex-col items-center justify-center gap-2 mb-12 animate-in" style={{ animationDelay: '0.4s' }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-secondary animate-pulse shadow-[0_0_8px_rgba(79,225,106,0.8)]"></div>
            <span className="text-xs font-headline tracking-[0.2em] text-secondary font-semibold uppercase">
              ● {t('home.statusLive')}
            </span>
          </div>
          <span className="text-xs text-on-surface-variant/60 font-light">
            {t('home.lastUpdated')} {health?.last_updated_hours ?? '--'} {t('home.hrsAgo')}
          </span>
        </div>

        {/* Footer */}
        <footer className="text-center pb-12 border-t border-white/5 pt-8 animate-in" style={{ animationDelay: '0.5s' }}>
          <p className="text-[10px] text-on-surface-variant/40 leading-relaxed px-8 mb-4">
            {t('disclaimer')}
          </p>
          <p className="text-xs font-headline font-semibold text-on-surface-variant/80 tracking-widest uppercase">
            {t('footer.createdBy')}
          </p>
        </footer>
      </main>

      <BottomNav />
    </div>
  );
}
