export interface ToolApp {
  id: string;
  name: string;
  description: string;
  icon: string;
  route: string;
  enabled: boolean;
  featured: boolean;
  order: number;
  releaseStage: "released" | "internal";
  status: string;
  statusClass: string;
}

export const toolApps: ToolApp[] = [
  {
    id: "codex-watch",
    name: "Codex 情报",
    description: "追踪指定公开账号，提取额度调整与重置信号。",
    icon: "/static/apps/codex-watch.svg",
    route: "/pages/codex-watch/index",
    enabled: true,
    featured: true,
    order: 10,
    releaseStage: "released",
    status: "待接入数据源",
    statusClass: "bg-acid",
  },
  {
    id: "video-parser",
    name: "视频解析",
    description: "下载无水印的视频",
    icon: "/static/apps/video-parser.svg",
    route: "/pages/video-parser/index",
    enabled: true,
    featured: true,
    order: 20,
    releaseStage: "released",
    status: "三平台可用",
    statusClass: "bg-acid",
  },
  {
    id: "hand-banner",
    name: "手持弹幕",
    description: "输入一句话，横屏循环滚动播放。",
    icon: "/static/apps/hand-banner.svg",
    route: "/pages/hand-banner/index",
    enabled: true,
    featured: true,
    order: 30,
    releaseStage: "released",
    status: "随时开播",
    statusClass: "bg-acid",
  },
  {
    id: "border-watermark",
    name: "边框水印",
    description: "给照片添加高级边框、品牌标识和拍摄参数。",
    icon: "/static/apps/border-watermark.svg",
    route: "/pages/border-watermark/index",
    enabled: true,
    featured: true,
    order: 40,
    releaseStage: "internal",
    status: "开发中",
    statusClass: "bg-acid",
  },
];

export function getEnabledApps(apps: ToolApp[] = toolApps) {
  return apps
    .filter((app) => app.enabled)
    .sort((left, right) => left.order - right.order);
}

export function getFeaturedApps(apps: ToolApp[] = toolApps) {
  return getEnabledApps(apps).filter((app) => app.featured);
}

export function isAppAvailable(
  app: ToolApp,
  production = import.meta.env.PROD,
) {
  return app.enabled && (!production || app.releaseStage === "released");
}
