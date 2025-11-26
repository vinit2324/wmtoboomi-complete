/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'jade-blue': '#003B5C',
        'jade-blue-dark': '#002840',
        'jade-blue-light': '#004D75',
        'jade-gold': '#FDB913',
        'jade-gold-dark': '#E5A511',
        'jade-gray': '#F5F5F5',
      },
    },
  },
  plugins: [],
}
