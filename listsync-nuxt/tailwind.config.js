/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './components/**/*.{js,vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.{js,ts}',
    './app.vue',
    './error.vue',
  ],
  theme: {
    extend: {
      scale: {
        '98': '0.98',
      },
      colors: {
        // ListSync purple theme
        purple: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#bd73e8', // Light purple
          500: '#9d34da', // Main purple
          600: '#8b2db8', // Dark purple
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },
      },
      fontFamily: {
        sans: ['"Titillium Web"', 'sans-serif'],
      },
      backgroundColor: {
        'dark': '#000000',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}

