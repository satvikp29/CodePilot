/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      colors: {
        ink: {
          DEFAULT: '#0d0d0d',
          soft: '#1a1a1a',
          muted: '#2a2a2a',
          border: '#333333',
          faint: '#444444',
        },
        paper: {
          DEFAULT: '#fafaf8',
          warm: '#f4f3ef',
          muted: '#e8e6e0',
          border: '#d4d1c8',
        },
        severity: {
          high: '#c0392b',
          medium: '#b7860b',
          low: '#2d7a4f',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.35s ease-out',
        'slide-up': 'slideUp 0.35s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      }
    },
  },
  plugins: [],
}
