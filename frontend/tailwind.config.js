/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "surface-container-highest": "#283646",
        "surface-container-high": "#1e2b3b",
        "surface-container-low": "#0f1c2c",
        "surface-container-lowest": "#020f1e",
        "surface-container": "#132030",
        "background": "#061423",
        "surface": "#061423",
        "on-surface": "#d6e4f9",
        "on-surface-variant": "#c4c6cc",
        "primary": "#ffb3b1",
        "secondary": "#4fe16a",
        "error": "#ffb4ab",
        "outline": "#8e9196",
        "outline-variant": "#44474c",
        "on-primary": "#680011",
        "on-secondary": "#003910",
        "on-primary-container": "#ef404c",
        "primary-container": "#3e0006",
        "secondary-container": "#01b343",
        "on-secondary-container": "#003c11",
        dmk:  { primary:"#E63946", light:"#FF6B6B", dark:"#C1121F" },
        admk: { primary:"#2DC653", light:"#52D680", dark:"#1A7A32" },
      },
      fontFamily: {
        headline: ["Manrope", "sans-serif"],
        body: ["Inter", "sans-serif"],
        tamil: ["Noto Sans Tamil", "sans-serif"]
      },
      borderRadius: {
        "DEFAULT": "1rem",
        "lg": "2rem",
        "xl": "3rem",
        "full": "9999px"
      }
    },
  },
  plugins: [],
}
