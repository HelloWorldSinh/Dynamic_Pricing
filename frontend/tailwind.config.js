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
          fpt: '#EA580C',
          'fpt-dark': '#C2410C',
          'fpt-light': '#FFF7ED',
          'fpt-border': '#FED7AA'
        },
        status: {
          danger: '#DC2626',
          warning: '#D97706',
          success: '#059669',
          info: '#2563EB',
          floor: '#DB2777'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '0.875rem', letterSpacing: '0.01em' }], // 11px
        'xs': ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.005em' }],        // 12px
        'sm': ['0.8125rem', { lineHeight: '1.125rem' }],                           // 13px
        'base': ['0.875rem', { lineHeight: '1.25rem' }],                            // 14px (Standard Body Text)
        'md': ['0.9375rem', { lineHeight: '1.375rem' }],                           // 15px
        'lg': ['1.125rem', { lineHeight: '1.5rem', letterSpacing: '-0.01em' }],     // 18px
        'xl': ['1.25rem', { lineHeight: '1.75rem', letterSpacing: '-0.02em' }],     // 20px
        '2xl': ['1.5rem', { lineHeight: '2rem', letterSpacing: '-0.02em' }],        // 24px
        '3xl': ['1.875rem', { lineHeight: '2.25rem', letterSpacing: '-0.02em' }],   // 30px
        '4xl': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.03em' }],     // 36px
      }
    },
  },
  plugins: [],
}
