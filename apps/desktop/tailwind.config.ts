import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        kairon: {
          bg: "#0b0d0e",
          panel: "#121516",
          surface: "#191d1e",
          line: "#2d3234",
          cyan: "#79d6c8",
          amber: "#e4b866",
          red: "#ef8585",
          text: "#f1efe9",
          soft: "#c6cbc8",
          muted: "#969c9e",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
