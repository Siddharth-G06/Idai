import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../i18n/LanguageContext';
import { COLORS } from '../styles/design-system';
import { Languages } from 'lucide-react';

export default function Navbar() {
  const { lang, setLang, t } = useLanguage();

  const toggleLanguage = () => {
    setLang(lang === 'en' ? 'ta' : 'en');
  };

  return (
    <header className="fixed top-0 w-full bg-[#061423]/80 backdrop-blur-xl flex justify-between items-center px-6 h-16 z-50 shadow-[0_40px_80px_-15px_rgba(2,15,30,0.1)]">
      <Link to="/" className="text-xl font-bold tracking-tighter text-white hover:opacity-80 transition-opacity">{t('appName')}</Link>
      
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
  );
}
