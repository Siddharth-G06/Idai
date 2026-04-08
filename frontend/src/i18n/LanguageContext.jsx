import React, { createContext, useContext, useState, useEffect } from 'react';
import en from './translations/en';
import ta from './translations/ta';

const LanguageContext = createContext();

const translations = { en, ta };

export const LanguageProvider = ({ children }) => {
  const [lang, setLangInternal] = useState(localStorage.getItem('idai_lang') || 'en');

  const setLang = (newLang) => {
    setLangInternal(newLang);
    localStorage.setItem('idai_lang', newLang);
  };

  useEffect(() => {
    // Sync attributes for SEO and Accessibility
    document.documentElement.lang = lang;
    
    // Dynamic Document Title
    const titles = {
      en: "IDAI — Closing the gap between promises and proof",
      ta: "இடை — வாக்குறுதிகளுக்கும் செயல்களுக்கும் இடையிலான இடைவெளி"
    };
    document.title = titles[lang] || titles.en;
  }, [lang]);

  const t = (path) => {
    const keys = path.split('.');
    let value = translations[lang];
    for (const key of keys) {
      if (value && value[key]) {
        value = value[key];
      } else {
        return path;
      }
    }
    return value;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
