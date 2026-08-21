import { defineConfig } from "vite";
import uniPackage from "@dcloudio/vite-plugin-uni";
import UnoCSS from "unocss/vite";

const uni = typeof uniPackage === "function"
  ? uniPackage
  : (uniPackage as unknown as { default: typeof uniPackage }).default;

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [uni(), UnoCSS()],
});
