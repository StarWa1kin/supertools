import { defineConfig, presetWind3 } from "unocss";

export default defineConfig({
  presets: [presetWind3()],
  theme: {
    colors: {
      ink: "#171916",
      paper: "#f4f5ef",
      acid: "#176bff",
      signal: "#ff5b45",
      line: "#d9dbd2",
      mute: "#72776d",
    },
  },
  shortcuts: {
    "section-title": "m-0 text-[26px] font-700 text-ink leading-tight",
    "section-copy": "m-0 mt-2 text-[14px] text-mute leading-6",
    "panel-surface": "bg-white border border-line rounded-[8px]",
  },
});
