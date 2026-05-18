/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172126",
        surface: "#f6f7f7",
        line: "#d8dedc",
        accent: "#197278",
        coral: "#c44536",
        gold: "#d99b28"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(23, 33, 38, 0.08)"
      }
    }
  },
  plugins: []
};
