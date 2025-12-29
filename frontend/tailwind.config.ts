import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Design tokens from UI prototype
      colors: {
        primary: {
          DEFAULT: '#19b345',
          50: '#e8f9ed',
          100: '#c5f0d2',
          200: '#9ee6b4',
          300: '#6fdb93',
          400: '#44d177',
          500: '#19b345',
          600: '#149a3b',
          700: '#0f7a2f',
          800: '#0a5a22',
          900: '#053a15',
        },
        sand: {
          DEFAULT: '#f3f0e6',
          50: '#faf9f5',
          100: '#f3f0e6',
          200: '#e8e3d4',
          300: '#d9d2be',
          400: '#c7bda3',
          500: '#b5a888',
        },
        surface: {
          light: '#ffffff',
          dark: '#1a1a1a',
        },
        text: {
          main: '#2d312f',
          muted: '#6b7280',
          light: '#9ca3af',
        },
      },
      fontFamily: {
        sans: ['Spline Sans', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'glass': '0 4px 16px rgba(0, 0, 0, 0.1)',
      },
      backdropBlur: {
        'glass': '12px',
      },
    },
  },
  plugins: [],
};

export default config;
