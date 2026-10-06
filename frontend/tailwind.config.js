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
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],        // 12px
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],     // 14px
        'base': ['1.25rem', { lineHeight: '1.75rem' }],    // 20px (scaled up from 16px)
        'lg': ['1.375rem', { lineHeight: '2rem' }],        // 22px (scaled up from 18px)
        'xl': ['1.5625rem', { lineHeight: '2.125rem' }],   // 25px (scaled up from 20px)
        '2xl': ['1.875rem', { lineHeight: '2.375rem' }],   // 30px (scaled up from 24px)
        '3xl': ['2.375rem', { lineHeight: '2.75rem' }],    // 38px (scaled up from 30px)
        '4xl': ['2.8125rem', { lineHeight: '3.25rem' }],   // 45px (scaled up from 36px)
      }
    },
  },
  plugins: [],
}
