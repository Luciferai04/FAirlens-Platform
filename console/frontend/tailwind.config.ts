import type { Config } from "tailwindcss";

/**
 * Tailwind config for FairLens Console — Stitch v2
 *
 * Color utility names are FLAT and match the Stitch HTML stubs directly:
 *   bg-surface, text-on-surface, border-outline-variant, etc.
 * This ensures class names from stubs can be copy-pasted with minimal edits.
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // --- Core Palette ---
        primary: "#61dbb4",
        "primary-container": "#12a480",
        "primary-fixed": "#7ff8cf",
        "primary-fixed-dim": "#61dbb4",
        "on-primary": "#00382a",
        "on-primary-container": "#003024",
        "on-primary-fixed": "#002117",
        "on-primary-fixed-variant": "#00513d",
        "inverse-primary": "#006c52",

        secondary: "#c6c6c6",
        "secondary-container": "#454747",
        "secondary-fixed": "#e2e2e2",
        "secondary-fixed-dim": "#c6c6c6",
        "on-secondary": "#2f3131",
        "on-secondary-container": "#b4b5b5",
        "on-secondary-fixed": "#1a1c1c",
        "on-secondary-fixed-variant": "#454747",

        tertiary: "#c8c6c5",
        "tertiary-container": "#929090",
        "tertiary-fixed": "#e5e2e1",
        "tertiary-fixed-dim": "#c8c6c5",
        "on-tertiary": "#303030",
        "on-tertiary-container": "#2a2a2a",
        "on-tertiary-fixed": "#1b1c1c",
        "on-tertiary-fixed-variant": "#474746",

        // --- Surfaces ---
        background: "#131313",
        "on-background": "#e5e2e1",
        surface: "#131313",
        "surface-dim": "#131313",
        "surface-bright": "#3a3939",
        "surface-variant": "#353534",
        "surface-tint": "#61dbb4",
        "surface-container-lowest": "#0e0e0e",
        "surface-container-low": "#1c1b1b",
        "surface-container": "#201f1f",
        "surface-container-high": "#2a2a2a",
        "surface-container-highest": "#353534",
        "on-surface": "#e5e2e1",
        "on-surface-variant": "#bccac2",
        "inverse-surface": "#e5e2e1",
        "inverse-on-surface": "#313030",

        // --- Outline ---
        outline: "#86948d",
        "outline-variant": "#3d4a44",

        // --- Error ---
        error: "#ffb4ab",
        "error-container": "#93000a",
        "on-error": "#690005",
        "on-error-container": "#ffdad6",

        // --- Brand (deeper green for primary action buttons) ---
        brand: "#10a37f",
        "brand-hover": "#0e906f",
      },
      borderRadius: {
        DEFAULT: "2px",
        lg: "4px",
        xl: "8px",
        full: "9999px",
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "40px",
        unit: "4px",
        gutter: "24px",
        "container-max": "1200px",
      },
      fontFamily: {
        h1: ["Inter"],
        h2: ["Inter"],
        h3: ["Inter"],
        "body-lg": ["Inter"],
        "body-md": ["Inter"],
        "label-sm": ["Inter"],
        code: ["Inter"],
        sans: ["Inter", "sans-serif"],
      },
      fontSize: {
        h1: ["32px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }],
        h2: ["24px", { lineHeight: "1.3", letterSpacing: "-0.01em", fontWeight: "600" }],
        h3: ["20px", { lineHeight: "1.4", letterSpacing: "-0.01em", fontWeight: "500" }],
        "body-lg": ["16px", { lineHeight: "1.6", letterSpacing: "0em", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "1.5", letterSpacing: "0em", fontWeight: "400" }],
        "label-sm": ["12px", { lineHeight: "1", letterSpacing: "0.02em", fontWeight: "500" }],
        code: ["14px", { lineHeight: "1.6", letterSpacing: "0em", fontWeight: "400" }],
      },
    },
  },
  plugins: [],
};

export default config;
