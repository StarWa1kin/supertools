import type {
  AdminSession,
  CodexWatchConfig,
  DeploymentStatus,
  ReminderSubscription,
  ReminderTestResult,
  RequestLogPage,
  RequestLogQuery,
} from "./types";

const baseUrl = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body === "object" && "detail" in body
      ? (body as { detail?: unknown }).detail
      : null;
    const message = typeof detail === "string"
      ? detail
      : `请求失败（${response.status}）`;
    throw new ApiError(message, response.status);
  }
  return body as T;
}

export function login(username: string, password: string) {
  return request<AdminSession>("/api/v1/admin/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function getConfig(token: string) {
  return request<CodexWatchConfig>("/api/v1/admin/codex-watch/config", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function saveConfig(token: string, config: CodexWatchConfig) {
  return request<CodexWatchConfig>("/api/v1/admin/codex-watch/config", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(config),
  });
}

export function getDeploymentStatus(token: string) {
  return request<DeploymentStatus>("/api/v1/admin/deployment/status", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function startDeployment(token: string, target: "server" | "admin") {
  return request<DeploymentStatus>(`/api/v1/admin/deployment/${target}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getReminderSubscriptions(token: string) {
  return request<ReminderSubscription[]>("/api/v1/admin/codex-watch/reminder-subscriptions", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function sendReminderTest(token: string, subscriptionId: string) {
  return request<ReminderTestResult>(
    `/api/v1/admin/codex-watch/reminder-subscriptions/${subscriptionId}/test`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } },
  );
}

export function getRequestLogs(token: string, query: RequestLogQuery = {}) {
  const params = new URLSearchParams();
  if (query.limit) params.set("limit", String(query.limit));
  if (query.offset) params.set("offset", String(query.offset));
  if (query.status) params.set("status", String(query.status));
  if (query.path?.trim()) params.set("path", query.path.trim());
  const suffix = params.size ? `?${params}` : "";
  return request<RequestLogPage>(`/api/v1/admin/request-logs${suffix}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
