/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        cream: "#FAF6EE",
        espresso: "#2E1F14",
        saffron: {
          DEFAULT: "#C79A2C",
          dark: "#A8821F",
        },
        pistachio: {
          DEFAULT: "#7A8B3D",
          dark: "#4A7C3C",
        },
        pomegranate: {
          DEFAULT: "#9C2B3B",
          dark: "#8E2430",
        },
        sand: "#F0E6D2",
        "soft-gold": "#E8D4A2",
        success: "#4A7C3C",
        warning: "#D68A1A",
        error: "#8E2430",
        info: "#5A6F3A",
      },
      fontFamily: {
        sans: ["'Vazirmatn Variable'", "Vazirmatn", "system-ui", "sans-serif"],
        display: ["Lalezar", "'Vazirmatn Variable'", "Vazirmatn", "serif"],
      },
      fontSize: {
        tiny: ["12px", { lineHeight: "1.5", fontWeight: "500" }],
        "body-sm": ["14px", { lineHeight: "1.6" }],
        body: ["16px", { lineHeight: "1.7" }],
        "body-lg": ["18px", { lineHeight: "1.7", fontWeight: "500" }],
        h3: ["20px", { lineHeight: "1.4", fontWeight: "600" }],
        h2: ["28px", { lineHeight: "1.3", fontWeight: "700" }],
        h1: ["40px", { lineHeight: "1.2", fontWeight: "700" }],
        display: [
          "56px",
          { lineHeight: "1.1", fontWeight: "800", letterSpacing: "-0.01em" },
        ],
      },
      borderRadius: {
        sm: "6px",
        md: "12px",
        lg: "16px",
        xl: "24px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(46,31,20,.05)",
        md: "0 4px 12px rgba(46,31,20,.08)",
        lg: "0 12px 32px rgba(46,31,20,.10)",
        focus: "0 0 0 3px rgba(199,154,44,.35)",
      },
      aspectRatio: {
        product: "4 / 5",
      },
      spacing: {
        "section-mobile": "48px",
        "section-desktop": "80px",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")({ strategy: "class" })],
};
