/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      colors: {
        ink: {
          950: "#071114",
          900: "#0d1b1f",
          800: "#10272c",
          700: "#19353a",
        },
        signal: {
          cyan: "#40e0d0",
          amber: "#ffbe0b",
          red: "#ff5a5f",
          mint: "#8ce99a",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(64, 224, 208, 0.35), 0 18px 40px -22px rgba(64, 224, 208, 0.55)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        rise: "rise 480ms ease-out both",
      },
    },
  },
  plugins: [],
};
