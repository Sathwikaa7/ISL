/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0B1220',
          900: '#0F1729',
          800: '#161F35',
          700: '#202B47'
        },
        paper: '#F6F4EE',
        amber: {
          400: '#F6B93B',
          500: '#F5A623'
        },
        teal: {
          400: '#2DD4BF',
          500: '#14B8A6'
        },
        coral: '#FB7185',
        slate: {
          300: '#C7CEDA',
          400: '#94A3B8',
          500: '#6B7A94'
        }
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace']
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 20px 40px -20px rgba(0,0,0,0.6)'
      },
      keyframes: {
        pulseRing: {
          '0%': { boxShadow: '0 0 0 0 rgba(245,166,35,0.55)' },
          '100%': { boxShadow: '0 0 0 14px rgba(245,166,35,0)' }
        },
        rise: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      },
      animation: {
        pulseRing: 'pulseRing 1.6s cubic-bezier(0.4,0,0.6,1) infinite',
        rise: 'rise 0.25s ease-out'
      }
    }
  },
  plugins: []
}
