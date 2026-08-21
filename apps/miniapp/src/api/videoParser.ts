import { request } from "./client";

export type VideoPlatform = "douyin" | "kuaishou" | "xiaohongshu";
export type MediaKind = "video" | "image";

export interface VideoAuthor {
  name: string;
  avatarUrl?: string;
}

export interface VideoAsset {
  kind: MediaKind;
  sourceUrl: string;
  previewPath: string;
  downloadPath: string;
}

export interface VideoResolveResult {
  platform: VideoPlatform;
  mediaType: "video" | "images";
  canonicalUrl: string;
  title: string;
  author: VideoAuthor;
  durationMs?: number;
  coverUrl?: string;
  assets: VideoAsset[];
}

export function resolveVideo(url: string) {
  return request<VideoResolveResult>({
    url: "/api/v1/video-parser/resolve",
    method: "POST",
    data: { url },
  });
}
