export interface CrawlerConfig {
  account: string;
  keywords: string[];
  scheduleEnabled: boolean;
  intervalMinutes: number;
  maxPosts: number;
}

export interface TutorialConfig {
  id: string;
  title: string;
  description: string;
  url: string;
}

export interface CommunityConfig {
  title: string;
  description: string;
  qrCode: string;
}

export interface ReminderConfig {
  enabled: boolean;
  appId: string;
  appSecret: string;
  templateId: string;
  page: string;
  statusKey: string;
  timeKey: string;
  remarkKey: string;
}

export interface CodexWatchConfig {
  crawler: CrawlerConfig;
  tutorials: TutorialConfig[];
  community: CommunityConfig | null;
  reminder: ReminderConfig;
  reminderSecretConfigured: boolean;
  updatedAt: string | null;
}

export interface AdminSession {
  accessToken: string;
  tokenType: "bearer";
  expiresIn: number;
  username: string;
}

export type DeploymentState = "idle" | "running" | "succeeded" | "failed" | "unavailable";

export interface DeploymentTarget {
  version: string | null;
  deployedAt: string | null;
}

export interface DeploymentStatus {
  status: DeploymentState;
  target?: "server" | "admin" | null;
  startedAt: string | null;
  finishedAt: string | null;
  log: string;
  targets?: Record<"server" | "admin", DeploymentTarget>;
}

export interface ReminderSubscription {
  id: string;
  openidMasked: string;
  templateId: string;
  subscribedAt: string;
  remainingDeliveries: number;
  lastSentEventId: string | null;
  isCurrentTemplate: boolean;
}

export interface ReminderTestResult {
  subscription: ReminderSubscription;
}

export interface RequestLogEntry {
  id: number;
  requestedAt: string;
  clientIp: string;
  method: string;
  path: string;
  statusCode: number;
  durationMs: number;
  userAgent: string;
}

export interface RequestLogPage {
  total: number;
  items: RequestLogEntry[];
}

export interface RequestLogQuery {
  limit?: number;
  offset?: number;
  status?: number;
  path?: string;
}
