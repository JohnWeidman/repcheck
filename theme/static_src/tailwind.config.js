/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "../templates/**/*.{html,js}",
    "../../templates/**/*.{html,js}",
    "../../congress/templates/**/*.{html,js}",
    "../../**/templates/**/*.{html,js}",
  ],
  safelist: [
    "sm:card-side",
    "card-side",
    "card",
    "card-body",
    "card-title",
    "card-actions",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [
    /**
     * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
     * for forms. If you don't like it or have own styling for forms,
     * comment the line below to disable '@tailwindcss/forms'.
     */
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("daisyui"),
  ],
  daisyui: {
    themes: [
      {
        WMATA: {
          primary: "#009CDE",
          secondary: "#ED8B00",
          accent: "#BF0D3E",
          neutral: "#FFD100",
          "base-100": "#919D9D",
          info: "#4A412A",
        },
      },
      "retro",
    ],
  },
};
