import { computed, ref } from "vue";

const STORAGE_KEY = "supertools.hand-banner.settings";
const MAX_LENGTH = 80;
const DEFAULT_TEXT = "今天也要闪闪发光";

const message = ref(DEFAULT_TEXT);
const textColor = ref("#ffffff");
const fontScale = ref(1);

export const bannerColors = ["#ffffff", "#89ff3c", "#38bdf8", "#fbbf24", "#fb7185", "#c084fc"];
export const bannerSizes = [
  { label: "小", value: 0.72 },
  { label: "中", value: 1 },
  { label: "大", value: 1.3 },
];

export function sanitizeBannerText(value: string) {
  return value
    .replace(/[\r\n]+/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim()
    .slice(0, MAX_LENGTH);
}

function sanitizeColor(value: unknown) {
  return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value)
    ? value
    : "#ffffff";
}

function sanitizeScale(value: unknown) {
  return bannerSizes.some((size) => size.value === value) ? Number(value) : 1;
}

export function useHandBanner() {
  function restore() {
    const stored = uni.getStorageSync(STORAGE_KEY);
    if (!stored || typeof stored !== "object") return;

    const settings = stored as Record<string, unknown>;
    if (typeof settings.message === "string") {
      message.value = sanitizeBannerText(settings.message);
    }
    textColor.value = sanitizeColor(settings.textColor);
    fontScale.value = sanitizeScale(settings.fontScale);
  }

  function save(value = message.value) {
    const next = sanitizeBannerText(value);
    message.value = next;
    uni.setStorageSync(STORAGE_KEY, {
      message: next,
      textColor: sanitizeColor(textColor.value),
      fontScale: sanitizeScale(fontScale.value),
    });
    return next;
  }

  return {
    message,
    textColor,
    fontScale,
    colors: bannerColors,
    sizes: bannerSizes,
    maxLength: MAX_LENGTH,
    remaining: computed(() => MAX_LENGTH - message.value.length),
    restore,
    save,
  };
}
