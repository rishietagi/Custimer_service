/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          red: "#a50034",      // LG Signature Red
          redHover: "#800028",
          charcoal: "#1e1e1e",  // Deep Charcoal
          cardBg: "#2d2d2d",    // Slate Charcoal for cards
          lightBg: "#f8f9fa",
          border: "#e0e0e0",
          success: "#2e7d32",
          warning: "#f9a825",
          info: "#1565c0"
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'premium': '0 4px 20px -2px rgba(165, 0, 52, 0.12)',
        'premium-hover': '0 8px 30px -4px rgba(165, 0, 52, 0.2)',
      }
    },
  },
  plugins: [],
}
