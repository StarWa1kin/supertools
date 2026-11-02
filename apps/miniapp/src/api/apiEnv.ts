import {
  apiEnvPresets,
  buildApiBaseUrl,
  findApiEnvPreset,
  resolveApiBaseUrl,
  type ApiEnvId,
} from "../config/apiEnv";

const STORAGE_KEY = "supertools.api-env";

let cachedBaseUrl: string | undefined;

/** 开发版、体验版可切换；正式版（release）不可切换。H5 仅在开发构建中可切换。 */
export function isApiEnvSwitchable() {
  let switchable: boolean = import.meta.env.DEV;
  // #ifdef MP-WEIXIN
  try {
    switchable = uni.getAccountInfoSync().miniProgram.envVersion !== "release";
  } catch {
    switchable = false;
  }
  // #endif
  return switchable;
}

export function getApiEnvOverride(): ApiEnvId | undefined {
  if (!isApiEnvSwitchable()) return undefined;
  return findApiEnvPreset(uni.getStorageSync(STORAGE_KEY))?.id;
}

export function getApiBaseUrl() {
  if (cachedBaseUrl === undefined) {
    const switchable = isApiEnvSwitchable();
    cachedBaseUrl = resolveApiBaseUrl({
      buildBaseUrl:
        buildApiBaseUrl ||
        (import.meta.env.DEV ? (findApiEnvPreset("local")?.baseUrl ?? "") : ""),
      overrideId: switchable ? uni.getStorageSync(STORAGE_KEY) : undefined,
      switchable,
    });
  }
  return cachedBaseUrl;
}

/** 传入 null 恢复为构建时的默认地址。 */
export function setApiEnvOverride(id: ApiEnvId | null) {
  if (!isApiEnvSwitchable()) return false;

  if (id === null) {
    uni.removeStorageSync(STORAGE_KEY);
  } else if (findApiEnvPreset(id)) {
    uni.setStorageSync(STORAGE_KEY, id);
  } else {
    return false;
  }

  cachedBaseUrl = undefined;
  return true;
}

export { apiEnvPresets };
