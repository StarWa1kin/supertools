export type ApiEnvId = "local" | "lan" | "remote";

export interface ApiEnvPreset {
  id: ApiEnvId;
  label: string;
  baseUrl: string;
}

type PublicEnv = Partial<Record<string, string | boolean | undefined>>;

export function normalizeBaseUrl(value: unknown) {
  if (typeof value !== "string") return "";
  const trimmed = value.trim().replace(/\/+$/, "");
  return /^https?:\/\/[^/\s]+/i.test(trimmed) ? trimmed : "";
}

/** 预设地址来自 .env 配置；未配置的预设不会出现在切换菜单中。 */
export function createApiEnvPresets(env: PublicEnv): ApiEnvPreset[] {
  const candidates: ApiEnvPreset[] = [
    { id: "local", label: "本地", baseUrl: String(env.VITE_API_LOCAL_URL ?? "") },
    { id: "lan", label: "局域网", baseUrl: String(env.VITE_API_LAN_URL ?? "") },
    { id: "remote", label: "线上", baseUrl: String(env.VITE_API_REMOTE_URL ?? "") },
  ];

  return candidates
    .map((preset) => ({ ...preset, baseUrl: normalizeBaseUrl(preset.baseUrl) }))
    .filter((preset) => preset.baseUrl);
}

export const apiEnvPresets = createApiEnvPresets(import.meta.env);
export const buildApiBaseUrl = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL,
);

export function findApiEnvPreset(
  id: unknown,
  presets: ApiEnvPreset[] = apiEnvPresets,
) {
  if (typeof id !== "string") return undefined;
  return presets.find((preset) => preset.id === id);
}

interface ResolveApiBaseUrlOptions {
  buildBaseUrl: string;
  overrideId?: unknown;
  switchable: boolean;
  presets?: ApiEnvPreset[];
}

/** 只有可切换的版本（开发版、体验版）才读取手动选择，正式版始终使用构建地址。 */
export function resolveApiBaseUrl({
  buildBaseUrl,
  overrideId,
  switchable,
  presets = apiEnvPresets,
}: ResolveApiBaseUrlOptions) {
  if (switchable) {
    const preset = findApiEnvPreset(overrideId, presets);
    if (preset) return preset.baseUrl;
  }
  return buildBaseUrl;
}

export function describeApiBaseUrl(
  baseUrl: string,
  presets: ApiEnvPreset[] = apiEnvPresets,
) {
  const preset = presets.find((item) => item.baseUrl === baseUrl);
  const host = baseUrl.replace(/^https?:\/\//i, "");
  return preset ? `${preset.label} ${host}` : host || "未配置";
}
