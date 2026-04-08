import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { COLORS } from '../styles/design-system';

export default function ScoreRing({ score = 0, color = '#E63946', size = 140, label = 'addressed', hideLabel = false }) {
  const [offset, setOffset] = useState(0);
  
  const strokeWidth = hideLabel ? size * 0.12 : size * 0.08;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;

  useEffect(() => {
    // Initial paint: 0, then after mount: actual value
    const timeout = setTimeout(() => {
      const progress = (score / 100) * circumference;
      setOffset(circumference - progress);
    }, 100);
    return () => clearTimeout(timeout);
  }, [score, circumference]);

  return (
    <div 
      className="relative flex items-center justify-center rounded-full"
      style={{ 
        width: size, 
        height: size,
        boxShadow: hideLabel ? 'none' : `0 0 30px ${color}15`
      }}
    >
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
        />
        {/* Progress Arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset || circumference}
          strokeLinecap="round"
          style={{
            transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
        />
      </svg>
      
      {/* Center Labeling */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="flex items-baseline mb-[-2px]">
          <span className={`${hideLabel ? 'text-lg' : 'text-3xl'} font-black text-white leading-none`}>
            {Math.round(score)}
          </span>
          <span className={`${hideLabel ? 'text-[10px]' : 'text-sm'} font-bold text-white/60 ml-0.5`}>
            %
          </span>
        </div>
        {!hideLabel && (
          <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
