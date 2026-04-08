import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Power, Loader2, AlertCircle } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

const HealthBanner = () => {
  const [isAwake, setIsAwake] = useState(true);
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const { t } = useLanguage();

  useEffect(() => {
    let interval;
    
    const checkHealth = async () => {
      try {
        await api.getHealth();
        setIsAwake(true);
        setIsWakingUp(false);
        setRetryCount(0);
        if (interval) clearInterval(interval);
      } catch (err) {
        setIsAwake(false);
        setIsWakingUp(true);
        if (retryCount < 10) {
          setRetryCount(prev => prev + 1);
        }
      }
    };

    // Initial check
    checkHealth();

    // If not awake, check every 5 seconds
    interval = setInterval(() => {
      if (!isAwake) {
        checkHealth();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isAwake, retryCount]);

  if (isAwake) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-blue-600 px-6 py-2.5 flex items-center justify-between gap-4 animate-in slide-in-from-top duration-500 shadow-2xl">
      <div className="flex items-center gap-3">
        {retryCount < 10 ? (
          <Loader2 className="w-4 h-4 animate-spin text-white" />
        ) : (
          <AlertCircle className="w-4 h-4 text-white" />
        )}
        <p className="text-xs font-bold uppercase tracking-widest text-white">
          {retryCount < 10 
            ? "Waking up decentralized intelligence server... Please wait." 
            : "Server is taking longer than expected. Please refresh."}
        </p>
      </div>
      <div className="hidden md:flex items-center gap-2 bg-white/10 px-3 py-1 rounded-full text-[9px] font-black uppercase text-white/80">
        <Power className="w-3 h-3" />
        Cold Start in progress
      </div>
      
      {/* Progress Bar */}
      <div className="absolute bottom-0 left-0 h-0.5 bg-white/30 transition-all duration-300" style={{ width: `${Math.min(retryCount * 10, 100)}%` }} />
    </div>
  );
};

export default HealthBanner;
