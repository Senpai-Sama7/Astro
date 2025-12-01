import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brutalist monochrome palette
        brutal: {
          black: "#0a0a0a",
          charcoal: "#1a1a1a",
          graphite: "#2a2a2a",
          slate: "#3a3a3a",
          gray: "#6a6a6a",
          silver: "#9a9a9a",
          light: "#e8e8e8",
          white: "#fafafa",
        },
        // Accent colors (Swiss-inspired)
        accent: {
          red: "#ff2d2d",
          blue: "#0066ff",
          green: "#00d26a",
          yellow: "#ffd700",
          cyan: "#00e5ff",
          purple: "#a855f7",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["var(--font-mono)", "SF Mono", "Monaco", "monospace"],
        display: ["var(--font-inter)", "Helvetica", "sans-serif"],
      },
      fontSize: {
        "display-xl": ["6rem", { lineHeight: "1", letterSpacing: "-0.04em" }],
        "display-lg": ["4rem", { lineHeight: "1.1", letterSpacing: "-0.03em" }],
        "display-md": ["3rem", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        "display-sm": ["2rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
      },
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
      },
      borderWidth: {
        "3": "3px",
      },
      boxShadow: {
        brutal: "4px 4px 0px 0px rgba(10, 10, 10, 1)",
        "brutal-sm": "2px 2px 0px 0px rgba(10, 10, 10, 1)",
        "brutal-lg": "8px 8px 0px 0px rgba(10, 10, 10, 1)",
        "brutal-white": "4px 4px 0px 0px rgba(255, 255, 255, 0.2)",
        glow: "0 0 20px rgba(0, 102, 255, 0.3)",
        "glow-red": "0 0 20px rgba(255, 45, 45, 0.3)",
        "glow-green": "0 0 20px rgba(0, 210, 106, 0.3)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-up": "slideUp 0.5s ease-out forwards",
        "slide-down": "slideDown 0.3s ease-out forwards",
        "slide-in-right": "slideInRight 0.4s ease-out forwards",
        "scale-in": "scaleIn 0.3s ease-out forwards",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
        bounce: "bounce 1s infinite",
        shimmer: "shimmer 2s linear infinite",
        float: "float 3s ease-in-out infinite",
        "grid-flow": "gridFlow 20s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        gridFlow: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
        "in-expo": "cubic-bezier(0.7, 0, 0.84, 0)",
      },
    },
  },
  plugins: [],
};

export default config;
