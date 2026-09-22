/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1220",
        panel: "#121a2b",
        line: "#243049",
        accent: "#3ee0c0",
        accent2: "#7aa2ff",
      },
      fontFamily: {
        sans: ["Source Sans 3", "Segoe UI", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
