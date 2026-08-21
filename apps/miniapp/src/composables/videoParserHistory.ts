import type { VideoPlatform } from "../api/videoParser";

const HISTORY_STORAGE_KEY = "supertools:video-parser:history:v1";
const PREFILL_STORAGE_KEY = "supertools:video-parser:prefill:v1";
const MAX_HISTORY_ITEMS = 50;

export type VideoParserHistoryStatus = "pending" | "success" | "failed";

export interface VideoParserHistoryItem {
  id: string;
  createdAt: number;
  input: string;
  url: string;
  platform: VideoPlatform;
  status: VideoParserHistoryStatus;
  title?: string;
  error?: string;
}

function isHistoryItem(value: unknown): value is VideoParserHistoryItem {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<VideoParserHistoryItem>;
  return (
    typeof item.id === "string" &&
    typeof item.createdAt === "number" &&
    typeof item.input === "string" &&
    typeof item.url === "string" &&
    ["douyin", "kuaishou", "xiaohongshu"].includes(item.platform || "") &&
    ["pending", "success", "failed"].includes(item.status || "")
  );
}

export function getVideoParserHistory(): VideoParserHistoryItem[] {
  try {
    const stored = uni.getStorageSync(HISTORY_STORAGE_KEY);
    return Array.isArray(stored) ? stored.filter(isHistoryItem) : [];
  } catch {
    return [];
  }
}

function saveHistory(items: VideoParserHistoryItem[]) {
  uni.setStorageSync(HISTORY_STORAGE_KEY, items.slice(0, MAX_HISTORY_ITEMS));
}

export function addVideoParserHistory(
  input: string,
  url: string,
  platform: VideoPlatform,
) {
  const item: VideoParserHistoryItem = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: Date.now(),
    input: input.trim(),
    url,
    platform,
    status: "pending",
  };
  try {
    saveHistory([item, ...getVideoParserHistory()]);
  } catch {
    // Local history must never block parsing.
  }
  return item.id;
}

export function updateVideoParserHistory(
  id: string,
  patch: Partial<Pick<VideoParserHistoryItem, "status" | "title" | "error">>,
) {
  try {
    saveHistory(
      getVideoParserHistory().map((item) =>
        item.id === id ? { ...item, ...patch } : item,
      ),
    );
  } catch {
    // Local history must never block parsing.
  }
}

export function removeVideoParserHistory(id: string) {
  saveHistory(getVideoParserHistory().filter((item) => item.id !== id));
}

export function clearVideoParserHistory() {
  uni.removeStorageSync(HISTORY_STORAGE_KEY);
}

export function setVideoParserPrefill(input: string) {
  uni.setStorageSync(PREFILL_STORAGE_KEY, input);
}

export function consumeVideoParserPrefill() {
  const input = uni.getStorageSync(PREFILL_STORAGE_KEY);
  if (typeof input !== "string" || !input) return "";
  uni.removeStorageSync(PREFILL_STORAGE_KEY);
  return input;
}
