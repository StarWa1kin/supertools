<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { initializeTheme } from "./composables/useTheme";

onLaunch(() => {
  initializeTheme();
});
onShow(() => {
  initializeTheme();

  // #ifdef MP-WEIXIN
  uni.showShareMenu({
    withShareTicket: true,
    menus: ["shareAppMessage", "shareTimeline"],
  });
  // #endif
});
onHide(() => undefined);
</script>
<style>
page {
  --color-page: #f4f1e8;
  --color-surface: #f4f1e8;
  --color-panel: rgba(255, 255, 255, 0.42);
  --color-subtle: #e7e3d8;
  --color-ink: #171915;
  --color-fog: #ddd8ca;
  --color-acid: #d8ff47;
  --color-signal: #ff5a36;
  --color-moss: #2d5a42;
  --color-border: #171915;
  --color-soft-border: rgba(23, 25, 21, 0.28);
  --color-placeholder: rgba(23, 25, 21, 0.35);
  --color-shadow: #171915;
  --color-shadow-soft: rgba(23, 25, 21, 0.13);
  min-height: 100%;
  background: var(--color-page);
  color: var(--color-ink);
  font-family: "MiSans", "HarmonyOS Sans SC", "PingFang SC", sans-serif;
}

.theme-classic,
.theme-blue,
.theme-dark {
  min-height: 100vh;
  background-color: var(--color-page);
  color: var(--color-ink);
  transition: background-color 180ms ease, color 180ms ease;
}

.theme-blue {
  --color-page: #edf4ff;
  --color-surface: #ffffff;
  --color-panel: rgba(255, 255, 255, 0.72);
  --color-subtle: #dce9fb;
  --color-ink: #102a43;
  --color-fog: #c8d9ef;
  --color-acid: #ffd166;
  --color-signal: #e34d59;
  --color-moss: #087e8b;
  --color-border: #173f68;
  --color-soft-border: rgba(23, 63, 104, 0.24);
  --color-placeholder: rgba(16, 42, 67, 0.42);
  --color-shadow: #1d4ed8;
  --color-shadow-soft: rgba(37, 99, 235, 0.15);
}

.theme-dark {
  --color-page: #101418;
  --color-surface: #171d23;
  --color-panel: rgba(31, 39, 47, 0.84);
  --color-subtle: #222b34;
  --color-ink: #f2f5f7;
  --color-fog: #2c3742;
  --color-acid: #d6ff4b;
  --color-signal: #ff6b57;
  --color-moss: #63d2b0;
  --color-border: #9eabb7;
  --color-soft-border: rgba(210, 221, 230, 0.24);
  --color-placeholder: rgba(242, 245, 247, 0.38);
  --color-shadow: #58a6ff;
  --color-shadow-soft: rgba(0, 0, 0, 0.34);
}

button::after {
  border: 0;
}

text,
view,
button,
input,
textarea {
  box-sizing: border-box;
}

@media (prefers-reduced-motion: reduce) {
  .theme-classic,
  .theme-blue,
  .theme-dark {
    transition: none;
  }
}
</style>
