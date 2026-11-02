import { ref } from "vue";

import {
  apiEnvPresets,
  getApiBaseUrl,
  getApiEnvOverride,
  isApiEnvSwitchable,
  setApiEnvOverride,
} from "../api/apiEnv";
import { describeApiBaseUrl } from "../config/apiEnv";

/** 开发版/体验版的 API 环境切换入口；正式版不显示也不生效。 */
export function useApiEnvSwitch() {
  const switchable = isApiEnvSwitchable();
  const apiEnvLabel = ref(switchable ? describeApiBaseUrl(getApiBaseUrl()) : "");

  function applyChoice(id: Parameters<typeof setApiEnvOverride>[0]) {
    if (!setApiEnvOverride(id)) return;
    apiEnvLabel.value = describeApiBaseUrl(getApiBaseUrl());
    uni.showToast({ title: `API：${apiEnvLabel.value}`, icon: "none" });
    // 重启页面栈，让已加载的数据和资源地址都使用新环境。
    setTimeout(() => uni.reLaunch({ url: "/pages/index/index" }), 600);
  }

  function openApiEnvSwitcher() {
    if (!switchable) return;

    const current = getApiEnvOverride();
    const itemList = [
      ...apiEnvPresets.map(
        (preset) =>
          `${preset.id === current ? "✓ " : ""}${preset.label}  ${preset.baseUrl}`,
      ),
      `${current ? "" : "✓ "}恢复构建默认`,
    ];

    uni.showActionSheet({
      itemList,
      success: ({ tapIndex }) => {
        applyChoice(apiEnvPresets[tapIndex]?.id ?? null);
      },
    });
  }

  return { apiEnvSwitchable: switchable, apiEnvLabel, openApiEnvSwitcher };
}
