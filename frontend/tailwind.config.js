/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          fpt: '#F26F21',
          'fpt-dark': '#D9580F',
          'fpt-light': '#FFF5EE'
        },
        status: {
          danger: '#EF4444',
          warning: '#F59E0B',
          success: '#10B981',
          info: '#3B82F6',
          floor: '#EC4899'
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
