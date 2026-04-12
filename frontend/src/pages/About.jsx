import React from 'react';
import Navbar from '../components/Navbar';
import BottomNav from '../components/BottomNav';
import { useLanguage } from '../i18n/LanguageContext';
import { COLORS } from '../styles/design-system';

export default function About() {
  const { t } = useLanguage();

  const sources = [
    "The Hindu Tamil Nadu",
    "NDTV South India",
    "Times of India",
    "PRS India",
    "NewsAPI"
  ];

  return (
    <div className="min-h-screen pb-24">
      <Navbar />

      <main className="max-w-2xl mx-auto px-6 py-10 flex flex-col gap-6">
        {/* Section 1: About IDAI */}
        <section className="glass-card p-6 animate-in">
          <h2 className="text-xl font-black text-white mb-3">
            {t('about.title')}
          </h2>
          <p className="text-sm leading-relaxed text-white/70">
            {t('about.desc')}
          </p>
        </section>

        {/* Section 2: How it works */}
        <section className="glass-card p-6 animate-in" style={{ animationDelay: '0.1s' }}>
          <h2 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-4">
            {t('about.howTitle')}
          </h2>
          <ol className="flex flex-col gap-4">
            {[1, 2, 3, 4].map(num => (
              <li key={num} className="flex gap-4 items-start">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-white/5 flex items-center justify-center text-[10px] font-bold text-white/40">
                  {num}
                </span>
                <p className="text-sm text-white/70 leading-snug">
                  {t(`about.step${num}`)}
                </p>
              </li>
            ))}
          </ol>
        </section>

        {/* Section 3: Disclaimer */}
        <section className="glass-card p-6 animate-in" style={{ animationDelay: '0.2s' }}>
          <h2 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-3">
             {t('nav.about')}
          </h2>
          <p className="text-[11px] leading-relaxed text-white/50">
            {t('disclaimer')}
          </p>
        </section>

        {/* Section 4: Sources */}
        <section className="glass-card p-6 animate-in" style={{ animationDelay: '0.3s' }}>
          <h2 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-4">
            {t('about.sourcesTitle')}
          </h2>
          <div className="flex flex-wrap gap-2">
            {sources.map(source => (
              <span key={source} className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-white/60">
                {source}
              </span>
            ))}
          </div>
        </section>

        {/* Section 5: Methodology Note */}
        <section className="p-6 border border-white/5 rounded-2xl animate-in" style={{ animationDelay: '0.4s', background: 'rgba(255,255,255,0.02)' }}>
          <h2 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-3">
            {t('about.methodTitle')}
          </h2>
          <p className="text-[11px] leading-relaxed text-white/60 italic">
            {t('about.methodDesc')}
          </p>
        </section>

        {/* Footer */}
        <footer className="mt-6 flex flex-col items-center gap-2 animate-in" style={{ animationDelay: '0.5s' }}>
           <span className="text-[10px] font-black tracking-widest text-white/20">
             {t('footer.createdBy')} · IDAI
           </span>
        </footer>
      </main>

      <BottomNav />
    </div>
  );
}
