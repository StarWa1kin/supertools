/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 构建时默认的 API 地址，由 .env.[mode] 提供。 */
  readonly VITE_API_BASE_URL?: string;
  /** 开发版/体验版环境切换菜单中的预设地址。 */
  readonly VITE_API_LOCAL_URL?: string;
  readonly VITE_API_LAN_URL?: string;
  readonly VITE_API_REMOTE_URL?: string;
}

declare module '*.vue' {
  import { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}
