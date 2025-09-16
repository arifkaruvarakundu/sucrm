module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // <-- add this
  theme: {
    extend: {
      colors: {
        blackPrimary: '#121212', // or your preferred value
      },
    },
  },
  plugins: [],
};
