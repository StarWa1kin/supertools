import { computed, readonly, ref } from "vue";

export type ThemeName = "classic" | "blue" | "dark";

export interface ThemeOption {
  name: ThemeName;
  label: string;
  swatch: string;
  navigationBackground: string;
  navigationForeground: "#000000" | "#ffffff";
  tabColor: string;
  tabSelectedColor: string;
  borderStyle: "black" | "white";
}

const STORAGE_KEY = "supertools-theme";

export const themeOptions: ThemeOption[] = [
  {
    name: "classic",
    label: "暖白",
    swatch: "#f4f1e8",
    navigationBackground: "#f4f1e8",
    navigationForeground: "#000000",
    tabColor: "#7a7d76",
    tabSelectedColor: "#171915",
    borderStyle: "black",
  },
  {
    name: "blue",
    label: "蓝色",
    swatch: "#2563eb",
    navigationBackground: "#edf4ff",
    navigationForeground: "#000000",
    tabColor: "#64748b",
    tabSelectedColor: "#1d4ed8",
    borderStyle: "black",
  },
  {
    name: "dark",
    label: "暗黑",
    swatch: "#101418",
    navigationBackground: "#101418",
    navigationForeground: "#ffffff",
    tabColor: "#8d9aa7",
    tabSelectedColor: "#58a6ff",
    borderStyle: "white",
  },
];

const activeTheme = ref<ThemeName>("classic");
let initialized = false;

export function resolveThemeName(value: unknown): ThemeName {
  return themeOptions.some((option) => option.name === value)
    ? (value as ThemeName)
    : "classic";
}

function updateNativeChrome(name: ThemeName) {
  if (typeof uni === "undefined") return;

  const option = themeOptions.find((item) => item.name === name) ?? themeOptions[0];
  const ignoreFailure = () => undefined;

  if (typeof uni.setNavigationBarColor === "function") {
    uni.setNavigationBarColor({
      frontColor: option.navigationForeground,
      backgroundColor: option.navigationBackground,
      animation: { duration: 180, timingFunc: "easeIn" },
      fail: ignoreFailure,
    });
  }
  if (typeof uni.setTabBarStyle === "function") {
    uni.setTabBarStyle({
      color: option.tabColor,
      selectedColor: option.tabSelectedColor,
      backgroundColor: option.navigationBackground,
      borderStyle: option.borderStyle,
      fail: ignoreFailure,
    });
  }
  if (typeof uni.setBackgroundColor === "function") {
    uni.setBackgroundColor({
      backgroundColor: option.navigationBackground,
      backgroundColorTop: option.navigationBackground,
      backgroundColorBottom: option.navigationBackground,
      fail: ignoreFailure,
    });
  }
}

export function initializeTheme() {
  if (!initialized && typeof uni !== "undefined") {
    activeTheme.value = resolveThemeName(uni.getStorageSync(STORAGE_KEY));
    initialized = true;
  }
  updateNativeChrome(activeTheme.value);
}

export function setTheme(name: ThemeName) {
  activeTheme.value = resolveThemeName(name);
  initialized = true;
  if (typeof uni !== "undefined") {
    uni.setStorageSync(STORAGE_KEY, activeTheme.value);
  }
  updateNativeChrome(activeTheme.value);
}

export function useTheme() {
  initializeTheme();

  return {
    theme: readonly(activeTheme),
    themeClass: computed(() => `theme-${activeTheme.value}`),
    options: themeOptions,
    setTheme,
  };
}
