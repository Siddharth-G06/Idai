import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, BarChart2, Info } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

export default function BottomNav() {
  const { t } = useLanguage();

  const navItems = [
    { path: '/', label: t('nav.home'), icon: Home },
    { path: '/compare', label: t('nav.compare'), icon: BarChart2 },
    { path: '/about', label: t('nav.about'), icon: Info },
  ];

  return (
    <nav className="fixed bottom-0 left-0 w-full z-[100] flex justify-around items-center h-20 px-4 bg-[#0D1B2A]/80 backdrop-blur-3xl rounded-t-[2.5rem] shadow-2xl safe-area-bottom">
      {navItems.map((item) => {
        const Icon = item.icon;

        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              flex flex-col items-center justify-center min-w-[80px] py-1.5 rounded-full transition-all duration-300 active:scale-90
              ${isActive 
                ? 'text-secondary bg-secondary/10' 
                : 'text-on-surface-variant/40 hover:text-on-surface hover:bg-white/5'}
            `}
          >
            <Icon 
              size={20} 
              className="mb-1"
            />
            <span className="font-headline uppercase tracking-widest text-[10px] font-bold">
              {item.label}
            </span>
          </NavLink>
        );
      })}
    </nav>
  );
}
