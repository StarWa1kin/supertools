export type BrandLogoId = "apple" | "canon" | "sony" | "custom";

export interface BrandLogoPack {
  id: BrandLogoId;
  name: string;
  shortName: string;
  asset?: string;
  color: string;
  note: string;
}

export interface FramePreset {
  id: "gallery" | "noir" | "paper" | "mono";
  name: string;
  subtitle: string;
  background: string;
  foreground: string;
  muted: string;
  defaultFrame: number;
}

export const brandLogoPacks: BrandLogoPack[] = [
  {
    id: "apple",
    name: "Apple",
    shortName: "APPLE",
    asset: "/static/brand-logos/apple.svg",
    color: "#111111",
    note: "适合 iPhone 拍摄参数",
  },
  {
    id: "canon",
    name: "Canon",
    shortName: "Canon",
    asset: "/static/brand-logos/canon.jpg",
    color: "#e60012",
    note: "适合 Canon 相机参数",
  },
  {
    id: "sony",
    name: "Sony",
    shortName: "SONY",
    asset: "/static/brand-logos/sony.svg",
    color: "#111111",
    note: "适合 Sony 相机参数",
  },
  {
    id: "custom",
    name: "纯文字",
    shortName: "STUDIO",
    color: "#111111",
    note: "使用自己的署名",
  },
];

export const framePresets: FramePreset[] = [
  {
    id: "gallery",
    name: "画廊白",
    subtitle: "干净留白",
    background: "#f7f5ef",
    foreground: "#171713",
    muted: "#77746c",
    defaultFrame: 8,
  },
  {
    id: "noir",
    name: "暗房黑",
    subtitle: "电影质感",
    background: "#111111",
    foreground: "#f5f2e9",
    muted: "#8e8b84",
    defaultFrame: 7,
  },
  {
    id: "paper",
    name: "暖相纸",
    subtitle: "温润纸色",
    background: "#e9deca",
    foreground: "#2c261e",
    muted: "#857968",
    defaultFrame: 10,
  },
  {
    id: "mono",
    name: "银盐灰",
    subtitle: "克制冷灰",
    background: "#d7d8d5",
    foreground: "#20211f",
    muted: "#6d706b",
    defaultFrame: 6,
  },
];

export function getBrandLogo(id: BrandLogoId) {
  return brandLogoPacks.find((brand) => brand.id === id) ?? brandLogoPacks[0];
}

export function getFramePreset(id: FramePreset["id"]) {
  return framePresets.find((preset) => preset.id === id) ?? framePresets[0];
}
