import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { COLORS } from '../styles/design-system';

export default function CategoryBar({ category, dmkScore = 0, admkScore = 0 }) {
  const { t } = useLanguage();
  
  const dmkWinner = dmkScore > admkScore;
  const admkWinner = admkScore > dmkScore;

  return (
    <div className="relative py-4 group w-full">
      {/* Hover background */}
      <div className="absolute inset-x-0 -top-1 -bottom-1 bg-white/[0.03] rounded-md scale-y-0 group-hover:scale-y-100 transition-transform duration-300" />
      
      <div className="relative flex flex-col gap-3">
        {/* Label */}
        <div className="flex justify-center">
          <span className="font-headline font-semibold text-base tracking-tight text-white/80">
            {t(`filters.${category.toLowerCase().replace(' & ', 'and')}`) || category}
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
          <div className={`w-10 text-center font-headline font-bold text-sm ${admkWinner ? 'text-secondary' : 'text-white/30'}`}>
            {Math.round(admkScore)}
          </div>

          {/* AIADMK Bar */}
          <div className="flex-1">
            <div 
              className={`h-2.5 rounded-full transition-all duration-1000 ${
                admkWinner 
                  ? 'bg-gradient-to-r from-secondary to-secondary/40 shadow-lg shadow-secondary/20 border border-secondary/20 h-3' 
                  : 'bg-secondary/20'
              }`}
              style={{ width: `${admkScore}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
