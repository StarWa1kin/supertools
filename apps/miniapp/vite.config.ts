import { fileURLToPath } from "node:url";

import { defineConfig, loadEnv } from "vite";
import uniPackage from "@dcloudio/vite-plugin-uni";
import UnoCSS from "unocss/vite";

const uni = typeof uniPackage === "function"
  ? uniPackage
  : (uniPackage as unknown as { default: typeof uniPackage }).default;

const envDir = fileURLToPath(new URL(".", import.meta.url));

// 正式构建缺少地址或不是 HTTPS 时直接失败，避免正式版请求到本地地址。
function assertProductionApiBaseUrl(mode: string) {
  const { VITE_API_BASE_URL: baseUrl = "" } = loadEnv(mode, envDir, "VITE_");
  if (!/^https:\/\/[^/\s]+/i.test(baseUrl.trim())) {
    throw new Error(
      `[supertools] 生产构建的 VITE_API_BASE_URL 必须是 HTTPS 地址，当前为「${baseUrl || "空"}」，请检查 .env.production。`,
    );
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  if (command === "build" && mode === "production") {
    assertProductionApiBaseUrl(mode);
  }

  return {
    plugins: [uni(), UnoCSS()],
  };
});
