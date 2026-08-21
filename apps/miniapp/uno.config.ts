import { presetUni } from "@uni-helper/unocss-preset-uni";
import { defineConfig } from "unocss";

export default defineConfig({
  presets: [presetUni({ attributify: false })],
  preflights: [],
  theme: {
    colors: {
      ink: "var(--color-ink)",
      paper: "var(--color-page)",
      surface: "var(--color-surface)",
      fog: "var(--color-fog)",
      acid: "var(--color-acid)",
      signal: "var(--color-signal)",
      moss: "var(--color-moss)",
    },
  },
  shortcuts: {
    "page-shell": "min-h-screen bg-paper text-ink px-5 pb-10",
    "eyebrow": "text-xs tracking-widest uppercase font-600 opacity-60",
    "tool-card": "block border border-ink rounded-5 p-5 bg-surface shadow-[4px_4px_0_var(--color-shadow)]",
    "action-button": "flex items-center justify-center min-h-12 rounded-4 bg-ink text-paper font-700",
    "field-shell": "w-full box-border border border-ink rounded-4 bg-transparent p-4 text-base",
    "status-chip": "inline-flex items-center rounded-full border border-ink px-3 py-1 text-xs font-700",
  },
});
