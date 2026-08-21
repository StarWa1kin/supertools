import { computed, ref } from "vue";

import { getEnabledApps, type ToolApp } from "../config/apps";

const STORAGE_KEY = "supertools.primary-app";
const DEFAULT_PRIMARY_APP_ID = "codex-watch";

const primaryAppId = ref(DEFAULT_PRIMARY_APP_ID);

function findEnabledApp(appId: unknown): ToolApp | undefined {
  if (typeof appId !== "string") return undefined;
  return getEnabledApps().find((app) => app.id === appId);
}

export function refreshPrimaryApp() {
  const storedApp = findEnabledApp(uni.getStorageSync(STORAGE_KEY));
  primaryAppId.value = storedApp?.id ?? DEFAULT_PRIMARY_APP_ID;
  return primaryAppId.value;
}

export function setPrimaryApp(appId: string) {
  const app = findEnabledApp(appId);
  if (!app) return false;

  primaryAppId.value = app.id;
  uni.setStorageSync(STORAGE_KEY, app.id);
  return true;
}

export function usePrimaryApp() {
  const primaryApp = computed(
    () =>
      findEnabledApp(primaryAppId.value) ??
      findEnabledApp(DEFAULT_PRIMARY_APP_ID)!,
  );

  return {
    primaryApp,
    primaryAppId,
    refreshPrimaryApp,
    setPrimaryApp,
  };
}
