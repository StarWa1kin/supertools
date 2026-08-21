import { request } from "./client";

export interface WatchPost {
  id: string;
  text: string;
  translatedText?: string;
  url: string;
  publishedAt: string;
  confidence: "official" | "third_party" | "inferred";
  matchedKeywords: string[];
  eventType?: string;
  verificationStatus?: string | null;
  sourceLabel?: string | null;
  officialWindowEndAt?: string | null;
  isReply?: boolean;
}

export interface ResetForecast {
  updatedAt: string;
  lastResetAt: string | null;
  probability24h: number;
  probability48h: number;
  confidence: "low" | "medium" | "high";
  commonWindow: string | null;
  recentMedianDays: number | null;
  weightedMeanDays: number | null;
  accelerating: boolean;
  ageDays: number | null;
  recentSample: number | null;
  verifiedResetCount: number;
  allTimeMedianDays: number | null;
  recent30dMedianDays: number | null;
  longestWaitDays: number | null;
  modelVersion: string | null;
}

interface WatchPostList {
  items: WatchPost[];
  monitoredAccount: string;
  forecast: ResetForecast | null;
  sourceUrl: string | null;
  sourceUpdatedAt: string | null;
  sourceError: boolean;
}

export interface AiTutorial {
  id: string;
  title: string;
  description: string;
  url: string;
}

export interface AiCommunity {
  title: string;
  description: string;
  qrCode: string;
}

export interface CodexWatchPublicConfig {
  tutorials: AiTutorial[];
  community: AiCommunity | null;
  reminderEnabled: boolean;
  reminderTemplateId: string | null;
}

export function getCodexWatchPosts() {
  return request<WatchPostList>({
    url: "/api/v1/codex-watch/posts",
    method: "GET",
  });
}

export function getCodexWatchConfig() {
  return request<CodexWatchPublicConfig>({
    url: "/api/v1/codex-watch/config",
    method: "GET",
  });
}

export function subscribeCodexReset(code: string, templateId: string) {
  return request<{ subscribed: boolean; remainingDeliveries: number }>({
    url: "/api/v1/codex-watch/subscriptions",
    method: "POST",
    data: { code, templateId },
  });
}
