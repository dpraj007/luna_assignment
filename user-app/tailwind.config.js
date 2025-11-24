/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#7C3AED',
          dark: '#5B21B6',
          light: '#A78BFA',
        },
        accent: {
          DEFAULT: '#FB923C',
          dark: '#EA580C',
          light: '#FDBA74',
        },
      },
    },
  },
  plugins: [],
}

