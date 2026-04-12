import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { COLORS } from '../styles/design-system';

export default function CategoryBar({ category, dmkScore = 0, aiadmkScore = 0 }) {
  const { t } = useLanguage();
  
  const dmkWinner = dmkScore > aiadmkScore;
  const aiadmkWinner = aiadmkScore > dmkScore;

  // Clean key for translation: "women and youth" -> "womenandyouth"
  const translationKey = category.toLowerCase().replace(/\s+/g, '');

  return (
    <div className="relative py-4 group w-full">
      {/* Label */}
      <div className="flex justify-center mb-3">
        <span className="font-headline font-semibold text-base tracking-tight text-white/80">
          {t(`filters.${translationKey}`) || category}
        </span>
      </div>

      {/* Bars and Scores */}
      <div className="flex items-center gap-4">
        {/* DMK Bar */}
        <div className="flex-1 flex justify-end">
          <div 
            className={`h-2.5 rounded-full transition-all duration-1000 ${
              dmkWinner 
                ? 'bg-gradient-to-l from-error to-error/40 shadow-lg shadow-error/20 border border-error/20 h-3' 
                : 'bg-error/20'
            }`}
            style={{ width: `${dmkScore}%` }}
          />
        </div>

        {/* DMK Score */}
        <div className={`w-10 text-center font-headline font-bold text-sm ${dmkWinner ? 'text-error' : 'text-white/30'}`}>
          {Math.round(dmkScore)}
        </div>

        {/* AIADMK Score */}
        <div className={`w-10 text-center font-headline font-bold text-sm ${aiadmkWinner ? 'text-secondary' : 'text-white/30'}`}>
          {Math.round(aiadmkScore)}
        </div>

        {/* AIADMK Bar */}
        <div className="flex-1">
          <div 
            className={`h-2.5 rounded-full transition-all duration-1000 ${
              aiadmkWinner 
                ? 'bg-gradient-to-r from-secondary to-secondary/40 shadow-lg shadow-secondary/20 border border-secondary/20 h-3' 
                : 'bg-secondary/20'
            }`}
            style={{ width: `${aiadmkScore}%` }}
          />
        </div>
      </div>
    </div>
  );
}
