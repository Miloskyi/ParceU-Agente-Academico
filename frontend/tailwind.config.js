/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        udea: {
          petroleo:  '#006065',
          turquesa:  '#069A7E',
          verde:     '#C5E1A5',
          blanco:    '#FFFFFF',
          gris:      '#F4F8F7',
          gris2:     '#E0EDEB',
          oscuro:    '#004548',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
