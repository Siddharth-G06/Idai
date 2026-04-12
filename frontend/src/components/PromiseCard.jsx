import React, { useState } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { CheckCircle, XCircle, ArrowRight, Clock, RefreshCw, AlertCircle, Search } from 'lucide-react';
import { COLORS } from '../styles/design-system';

export default function PromiseCard({ promise, partyColor }) {
  const { t, lang } = useLanguage();
  const [isExpanded, setIsExpanded] = useState(false);
  const [linkStatus, setLinkStatus] = useState('checking'); // checking, ok, dead

  const status = promise.status || 'unfulfilled';
  
  // Link Health Check Logic
  React.useEffect(() => {
    const url = promise.matched_url;
    if (!url || !url.startsWith('http') || url.includes('example.com')) {
      setLinkStatus('dead');
      return;
    }

    const cached = sessionStorage.getItem(`link_state_${url}`);
    if (cached) {
      setLinkStatus(cached);
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);

    fetch(url, { method: 'HEAD', mode: 'no-cors', signal: controller.signal })
      .then(() => {
        sessionStorage.setItem(`link_state_${url}`, 'ok');
        setLinkStatus('ok');
      })
      .catch(() => {
        sessionStorage.setItem(`link_state_${url}`, 'dead');
        setLinkStatus('dead');
      })
      .finally(() => clearTimeout(timeout));
  }, [promise.matched_url]);

  const getDomain = (url) => {
    try { return new URL(url).hostname; } catch { return ""; }
  };
  
  const getStatusConfig = () => {
    switch(status) {
      case 'fulfilled':
        return {
          color: 'text-secondary',
          icon: <CheckCircle size={16} fill="currentColor" fillOpacity={0.2} />,
          label: t('filters.fulfilled') || 'Kept'
        };
      case 'fulfilled_by_other':
        return {
          color: 'text-primary',
          icon: <RefreshCw size={16} />,
          label: `${t('status.completedBy') || 'Completed by'} ${promise.credit_party}`
        };
      case 'unverified':
        return {
          color: 'text-white/20',
          icon: <Clock size={16} strokeDasharray="4 4" />,
          label: t('status.unverified') || 'Unverified'
        };
      case 'pending':
        return {
          color: 'text-white/40',
          icon: <Clock size={16} />,
          label: t('status.pending') || 'Ongoing'
        };
      default:
        return {
          color: 'text-error',
          icon: <XCircle size={16} fill="currentColor" fillOpacity={0.2} />,
          label: t('filters.unfulfilled') || 'Not Addressed'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const isFulfilled = status === 'fulfilled' || status === 'fulfilled_by_other';

  return (
    <div className="glass-card rounded-lg p-6 border-l-4 relative overflow-hidden transition-all duration-300 hover:scale-[1.01] hover:bg-white/[0.07]"
         style={{ borderLeftColor: partyColor }}>
      
      {/* Top badges */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex flex-wrap gap-2">
          {(promise.categories || [promise.category]).map(cat => (
            <span key={cat} className="px-3 py-1 bg-surface-container-highest text-[10px] font-bold uppercase tracking-widest text-on-surface-variant rounded-md flex items-center gap-1.5 group cursor-help">
              {t(`filters.${cat.toLowerCase().replace(' & ', 'and')}`) || cat}
              {promise.classification_confidence === 'low' && (
                <span className="text-on-surface-variant/40 hover:text-white transition-colors">
                  ⓘ
                  <div className="absolute top-full left-0 mt-2 p-2 bg-black text-[8px] normal-case font-normal rounded shadow-xl hidden group-hover:block z-50 w-32 border border-white/10">
                    Category auto-detected · may not be exact
                  </div>
                </span>
              )}
            </span>
          ))}
        </div>
        
        <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-tighter ${
              promise.specificity === 'high' ? 'bg-secondary/10 text-secondary' : 
              promise.specificity === 'low' ? 'bg-error/10 text-error' : 'bg-white/5 text-white/40'
            }`}>
              {t(`specificity.${promise.specificity || 'medium'}`)} {t('party.specificity')}
            </span>
            {promise.match_valid === false && (
              <span className="px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-tighter bg-error/10 text-error animate-pulse">
                {t('party.invalidDate')}
              </span>
            )}
           <span className={`flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider ${statusConfig.color}`}>
             {statusConfig.icon}
             {statusConfig.label}
           </span>
        </div>
      </div>

      {/* Headline Text */}
      <h3 className={`text-xl font-headline font-light leading-relaxed mb-6 text-on-surface transition-all ${!isExpanded ? 'line-clamp-2' : ''}`}
          onClick={() => setIsExpanded(!isExpanded)}>
        {lang === 'ta' ? (promise.promise || promise.translated) : (promise.translated || promise.promise)}
      </h3>

      {/* Attribution info for fulfilled_by_other */}
      {status === 'fulfilled_by_other' && (
        <div className="mb-6 p-3 bg-white/5 rounded-md border border-white/5 flex items-center gap-3">
          <div className="flex -space-x-2">
            <div className="w-6 h-6 rounded-full border border-background" style={{ backgroundColor: promise.promising_party === 'DMK' ? '#E63946' : '#2DC653' }} />
            <div className="w-6 h-6 rounded-full border border-background flex items-center justify-center bg-white/10">
              <RefreshCw size={10} className="text-white" />
            </div>
            <div className="w-6 h-6 rounded-full border border-background" style={{ backgroundColor: promise.credit_party === 'DMK' ? '#E63946' : '#2DC653' }} />
          </div>
          <p className="text-[10px] text-on-surface-variant leading-tight">
            Promised by <span className="text-white font-bold">{promise.promising_party}</span> in {promise.year || '2016'}
            <br />
            Completed under <span className="text-white font-bold">{promise.credit_party}</span> in {new Date(promise.matched_date).getFullYear() || '2023'}
          </p>
        </div>
      )}

      {/* Evidence and Link */}
      <div className="flex flex-col md:flex-row items-center justify-between pt-6 border-t border-white/5 gap-4">
        <div className="w-full md:w-1/3">
          <div className="flex justify-between text-[10px] font-label text-on-surface-variant/60 uppercase tracking-widest mb-1.5">
            <span>{t('party.matchScore')}</span>
            <span>{Math.round((promise.similarity || promise.similarity_score || 0) * 100)}%</span>
          </div>
          <div className="h-1 bg-surface-container-highest rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-1000" 
              style={{ 
                width: `${(promise.similarity || promise.similarity_score || 0) * 100}%`,
                backgroundColor: isFulfilled ? '#4fe16a' : '#ffb4ab'
              }}
            />
          </div>
        </div>

        {promise.matched_url && linkStatus !== 'dead' ? (
          <a 
            href={promise.matched_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-on-surface-variant hover:text-primary transition-colors text-xs font-bold uppercase tracking-widest flex items-center gap-2 group"
          >
            {getDomain(promise.matched_url) && (
              <img 
                src={`https://www.google.com/s2/favicons?domain=${getDomain(promise.matched_url)}&sz=32`} 
                width="14" 
                height="14" 
                className="rounded-sm opacity-60 group-hover:opacity-100 transition-opacity"
                alt=""
              />
            )}
            {t('party.readArticle')}
            <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
          </a>
        ) : (
          <a 
            href={`https://news.google.com/search?q=${encodeURIComponent(lang === 'ta' ? (promise.promise || promise.translated) : (promise.translated || promise.promise))}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-on-surface-variant/40 hover:text-white transition-colors text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 group italic"
          >
            <Search size={14} />
            {promise.matched_url ? (
              <span className="flex items-center gap-1">
                Link potentially dead <span className="mx-1">·</span> Search Topic
              </span>
            ) : "Search Topic"}
            <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
          </a>
        )}
      </div>
    </div>
  );
}
