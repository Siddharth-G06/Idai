import React from 'react';
import { Link } from 'react-router-dom';
import { useQueries } from '@tanstack/react-query';
import { api } from '../api/client';
import { useLanguage } from '../i18n/LanguageContext';
import CategoryBar from '../components/CategoryBar';
import ScoreRing from '../components/ScoreRing';
import Navbar from '../components/Navbar';
import BottomNav from '../components/BottomNav';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { COLORS } from '../styles/design-system';

export default function Compare() {
  const { t } = useLanguage();
  
  const results = useQueries({
    queries: [
      { queryKey: ['score'], queryFn: () => api.getScore() },
      { queryKey: ['summary'], queryFn: () => api.getSummary() },
    ]
  });

  const isLoading = results.some(r => r.isLoading);
  const isError = results.some(r => r.isError);
  const data = results[0].data; // Scores data
  const refetch = () => results.forEach(r => r.refetch());

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 pt-32 space-y-12">
          <div className="h-24 glass rounded-3xl animate-pulse w-3/4 mx-auto" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="h-64 glass rounded-3xl animate-pulse" />
            <div className="h-64 glass rounded-3xl animate-pulse" />
          </div>
        </main>
        <BottomNav />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <ErrorState 
          message="We couldn't generate the comparison report. Please try again later." 
          onRetry={refetch} 
        />
      </div>
    );
  }

  const getBestKey = (prefix) => {
    const keys = Object.keys(data);
    return keys.find(k => k.startsWith(prefix) && data[k].context === 'ruling') || 
           keys.find(k => k.startsWith(prefix));
  };

  const dmkKey = getBestKey('DMK');
  const aiadmkKey = getBestKey('AIADMK');

  const dmkData = dmkKey ? data[dmkKey] : null;
  const aiadmkData = aiadmkKey ? data[aiadmkKey] : null;

  if (!dmkData || !aiadmkData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <EmptyState message={t('compare.insufficientData') || "Comparison data is currently incomplete. We're updating our records."} />
        <BottomNav />
      </div>
    );
  }

  const categories = Object.keys(dmkData.categories || {});

  const winner = dmkData.score > aiadmkData.score ? 'DMK' : 'AIADMK';
  const winnerScore = Math.round(dmkData.score > aiadmkData.score ? dmkData.score : aiadmkData.score);
  const loserScore = Math.round(dmkData.score > aiadmkData.score ? aiadmkData.score : dmkData.score);
  const winnerColor = dmkData.score > aiadmkData.score ? (COLORS?.dmk?.primary || '#E63946') : (COLORS?.aiadmk?.primary || '#2DC653');
  const secondaryColor = dmkData.score > aiadmkData.score ? COLORS.dmk.light : COLORS.aiadmk.light;

  return (
    <div className="min-h-screen pb-32 bg-background">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 pt-32 pb-24">
        {/* Header */}
        <header className="text-center mb-16 animate-in">
          <div className="inline-flex items-center gap-6 md:gap-12">
            <h1 className="text-5xl md:text-7xl font-headline font-extrabold tracking-tighter text-error">{t('parties.dmk')}</h1>
            <div className="h-12 w-px bg-white/10 rotate-12"></div>
            <span className="text-2xl md:text-3xl font-headline font-light tracking-[0.2em] text-white/30 truncate">{t('compare.vs')}</span>
            <div className="h-12 w-px bg-white/10 rotate-12"></div>
            <h1 className="text-5xl md:text-7xl font-headline font-extrabold tracking-tighter text-secondary">{t('parties.aiadmk')}</h1>
          </div>
          <p className="mt-4 text-on-surface-variant font-label tracking-widest text-xs uppercase">
            {t('compare.matrixTitle') || 'Party Accountability Comparison Matrix'}
          </p>
        </header>

        {/* Top Section: Score Rings */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
          <div className="surface-container-low rounded-lg p-10 flex flex-col items-center relative overflow-hidden group animate-in" style={{ animationDelay: '0.1s' }}>
            <div className="absolute inset-0 bg-gradient-to-br from-error/5 to-transparent"></div>
            <ScoreRing score={dmkData.score} color={COLORS.dmk.primary} size={192} label={t('party.governanceScore')} />
            <h3 className="mt-8 font-headline text-xl text-error font-bold tracking-tight">{t('parties.dmk')} {t('compare.performance')}</h3>
            <p className="text-on-surface-variant text-sm mt-2 text-center max-w-[240px]">
              {t('compare.dmkSummary')}
            </p>
          </div>

          <div className="surface-container-low rounded-lg p-10 flex flex-col items-center relative overflow-hidden group animate-in" style={{ animationDelay: '0.2s' }}>
            <div className="absolute inset-0 bg-gradient-to-br from-secondary/5 to-transparent"></div>
            <ScoreRing score={aiadmkData.score} color={COLORS.aiadmk.primary} size={192} label={t('party.impactScore')} />
            <h3 className="mt-8 font-headline text-xl text-secondary font-bold tracking-tight">{t('parties.aiadmk')} {t('compare.performance')}</h3>
            <p className="text-on-surface-variant text-sm mt-2 text-center max-w-[240px]">
              {t('compare.aiadmkSummary')}
            </p>
          </div>
        </section>

        {/* Categories Matrix */}
        <section className="animate-in" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center justify-between mb-10 border-b border-white/5 pb-6">
            <h2 className="text-2xl font-headline font-bold text-white/90">
              {dmkData.score > aiadmkData.score ? t('compare.dmkLeads') : t('compare.aiadmkLeads')}
            </h2>
          <div className="flex justify-between items-end mt-12 mb-4 px-2 opacity-50 font-label text-[9px] uppercase tracking-widest text-on-surface-variant">
            <div className="w-1/2 text-left">{t('parties.dmk')} {t('party.scoreLabel')}</div>
            <div className="w-1/2 text-right">{t('parties.aiadmk')} {t('party.scoreLabel')}</div>
          </div>
          
          <div className="flex flex-col gap-4">
            {categories.map((cat, idx) => (
              <CategoryBar 
                key={cat}
                category={cat} 
                dmkScore={dmkData.categories?.[cat]?.score || 0} 
                aiadmkScore={aiadmkData.categories?.[cat]?.score || 0} 
              />
            ))}
          </div>
        </section>
      </main>

      {/* Winner Banner */}
      <footer className="fixed bottom-24 left-0 right-0 z-50 px-4 animate-in" style={{ animationDelay: '0.8s' }}>
        <div className="max-w-xl mx-auto glass-blur bg-[#132030]/80 rounded-full py-4 px-8 flex justify-between items-center shadow-2xl border border-white/5 overflow-hidden relative">
          <div 
            className="absolute inset-0 opacity-20 pointer-events-none"
            style={{ background: `linear-gradient(to right, ${winnerColor}, transparent, ${winnerColor})` }}
          />
          <div className="flex items-center gap-3 relative z-10">
            <span className="text-white font-headline font-bold text-lg tracking-tight">
              {t(`parties.${winner.toLowerCase()}`)} {t('compare.leadsOverall') || 'leads overall'}
            </span>
          </div>
          <div className="text-white/80 font-label font-medium tracking-wider relative z-10">
            {winnerScore}% vs {loserScore}%
          </div>
          <Link 
            to={`/parties/${winner.toLowerCase()}`}
            className="bg-white/10 hover:bg-white/20 text-white px-5 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all relative z-10"
          >
            {t('home.viewDetails')}
          </Link>
        </div>
      </footer>

      <BottomNav />
    </div>
  );
}
