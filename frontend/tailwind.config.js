/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dmk:  { primary:"#E63946", light:"#FF6B6B", dark:"#C1121F" },
        admk: { primary:"#2DC653", light:"#52D680", dark:"#1A7A32" },
        navy: { DEFAULT:"#0D1B2A", light:"#1B2E45", card:"#162236" }
      },
      fontFamily: {
        tamil: ["Noto Sans Tamil", "sans-serif"]
      }
    },
  },
  plugins: [],
}
