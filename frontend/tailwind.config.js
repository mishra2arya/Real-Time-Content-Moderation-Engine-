/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          bg: "#111014",
          surface: "#151419",
          elevated: "#1D1B22",
          card: "#242128",
          cardHover: "#2A2730",
          border: "#37333D",
          borderStrong: "#433E48",
          primary: "#A78BFA",
          secondary: "#D946EF",
          positive: "#34D399",
          warning: "#FBBF24",
          danger: "#FB7185",
          text: "#F5F3F7",
          textMuted: "#A8A3AF",
          textDim: "#716C7A",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
