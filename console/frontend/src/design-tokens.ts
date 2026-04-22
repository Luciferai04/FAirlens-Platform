/**
 * FairLens Design Tokens — Stitch v2 (Green/Grey Material Design 3)
 * Source: stitch_assets/*_v2.html tailwind.config blocks
 *
 * These tokens are the single source of truth for all colors, typography,
 * spacing, and shape values used across the console frontend.
 */

export const DESIGN_TOKENS = {
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

    // --- Hard-coded nav/chrome colors from stubs ---
    sidebarBg: "#171717",
    topbarBg: "#0d0d0d",
    borderHard: "#2f2f2f",
    navActive: "#10a37f",
    navActiveBg: "#212121",
    textMuted: "#b4b4b4",
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

  borderRadius: {
    DEFAULT: "0.125rem",
    lg: "0.25rem",
    xl: "0.5rem",
    full: "0.75rem",
  },

  typography: {
    fontFamily: {
      h1: ["Inter"],
      h2: ["Inter"],
      h3: ["Inter"],
      "body-lg": ["Inter"],
      "body-md": ["Inter"],
      "label-sm": ["Inter"],
      code: ["Inter"],
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
} as const;
