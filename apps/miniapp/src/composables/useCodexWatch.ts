import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import {
  getCodexWatchConfig,
  getCodexWatchPosts,
  subscribeCodexReset,
  type AiCommunity,
  type AiTutorial,
  type ResetForecast,
  type WatchPost,
} from "../api/codexWatch";

export type WatchConclusionKind = "clear" | "signal" | "confirmed" | "offline";

export interface WatchConclusion {
  kind: WatchConclusionKind;
  answer: string;
  headline: string;
  detail: string;
}

export interface ReminderState {
  available: boolean;
  title: string;
  caption: string;
}

export const confidenceMeta: Record<WatchPost["confidence"], { label: string; className: string }> = {
  official: { label: "官方确认", className: "confidence-official" },
  third_party: { label: "第三方消息", className: "confidence-third-party" },
  inferred: { label: "程序推测", className: "confidence-inferred" },
};

function isSameUtcDay(value: string, now: Date) {
  const date = new Date(value);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === now.toISOString().slice(0, 10);
}

export function buildWatchConclusion(
  posts: WatchPost[],
  error = "",
  forecast: ResetForecast | null = null,
  now = new Date(),
): WatchConclusion {
  if (error) {
    return {
      kind: "offline",
      answer: "未知",
      headline: "本次扫描未完成",
      detail: "服务暂时不可用，当前结果不能作为判断依据。",
    };
  }

  const confirmedToday = forecast?.lastResetAt
    ? isSameUtcDay(forecast.lastResetAt, now)
    : posts.some((post) => post.confidence === "official");

  if (confirmedToday) {
    return {
      kind: "confirmed",
      answer: "已确认",
      headline: "发现官方重置信号",
      detail: "监测到官方来源，请查看下方原文并核对适用范围。",
    };
  }

  if (posts.length > 0) {
    return {
      kind: "signal",
      answer: "有信号",
      headline: "发现待核实消息",
      detail: "当前仅有第三方消息或程序推测，尚不代表官方确认。",
    };
  }

  return {
    kind: "clear",
    answer: "暂未",
    headline: "今日暂未监测到重置",
    detail: "没有发现匹配公开信息，后续扫描结果可能发生变化。",
  };
}

function pad(value: number) {
  return String(value).padStart(2, "0");
}

export function formatBriefDate(date = new Date()) {
  return `${date.getFullYear()}.${pad(date.getMonth() + 1)}.${pad(date.getDate())}`;
}

export function formatScanTime(date = new Date()) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function formatPostDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${pad(date.getMonth() + 1)}.${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function selectLatestPosts(posts: WatchPost[], limit = 3) {
  return [...posts]
    .sort((left, right) => (
      new Date(right.publishedAt).getTime() - new Date(left.publishedAt).getTime()
    ))
    .slice(0, limit);
}

export function buildReminderState(
  serviceEnabled: boolean,
  templateId: string,
): ReminderState {
  if (!serviceEnabled || !templateId) {
    return {
      available: false,
      title: "重置提醒暂不可用",
      caption: "提醒服务暂未启用",
    };
  }

  return {
    available: true,
    title: "订阅重置提醒",
    caption: "确认重置后通过微信服务通知提醒",
  };
}

function requestResetSubscription(templateId: string) {
  return new Promise<Record<string, string>>((resolve, reject) => {
    uni.requestSubscribeMessage({
      tmplIds: [templateId],
      success(result) {
        resolve(result as unknown as Record<string, string>);
      },
      fail: reject,
    });
  });
}

function showSubscriptionSettingsGuide() {
  uni.showModal({
    title: "提醒暂未开启",
    content: "可再次点击订阅按钮重新选择。若此前勾选过“总是保持以上选择”，请点右上角「…」→「设置」→「订阅消息」，开启本小程序的提醒后再回来订阅。",
    showCancel: false,
    confirmText: "我知道了",
  });
}

export function useCodexWatch() {
  const posts = ref<WatchPost[]>([]);
  const forecast = ref<ResetForecast | null>(null);
  const sourceUrl = ref("");
  const aiTutorials = ref<AiTutorial[]>([]);
  const aiCommunity = ref<AiCommunity | null>(null);
  const reminderEnabled = ref(false);
  const reminderTemplateId = ref("");
  const subscribing = ref(false);
  const monitoredAccount = ref("Tibo");
  const loading = ref(false);
  const error = ref("");
  const configError = ref("");
  const lastScannedAt = ref<Date | null>(null);

  const conclusion = computed(() => buildWatchConclusion(posts.value, error.value, forecast.value));
  const latestPosts = computed(() => selectLatestPosts(posts.value));
  const dateLabel = computed(() => formatBriefDate(lastScannedAt.value ?? new Date()));
  const scanTimeLabel = computed(() => (
    lastScannedAt.value ? formatScanTime(lastScannedAt.value) : "--:--"
  ));
  const reminderState = computed(() => buildReminderState(
    reminderEnabled.value,
    reminderTemplateId.value,
  ));

  async function loadPosts() {
    try {
      const postResult = await getCodexWatchPosts();
      posts.value = postResult.items;
      forecast.value = postResult.forecast;
      sourceUrl.value = postResult.sourceUrl || "";
      monitoredAccount.value = postResult.monitoredAccount || monitoredAccount.value;
      if (postResult.sourceError) error.value = "第三方情报源暂时不可用";
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : "暂时无法连接服务";
      posts.value = [];
      forecast.value = null;
    }
  }

  async function loadConfig() {
    try {
      const configResult = await getCodexWatchConfig();
      aiTutorials.value = Array.isArray(configResult.tutorials)
        ? configResult.tutorials.filter(
            (tutorial) =>
              Boolean(tutorial?.title?.trim()) &&
              /^https?:\/\//i.test(tutorial?.url ?? ""),
          )
        : [];
      aiCommunity.value = configResult.community;
      reminderEnabled.value = configResult.reminderEnabled === true;
      reminderTemplateId.value = configResult.reminderTemplateId || "";
    } catch (reason) {
      configError.value = reason instanceof Error ? reason.message : "暂时无法加载页面配置";
      aiTutorials.value = [];
      aiCommunity.value = null;
      reminderEnabled.value = false;
      reminderTemplateId.value = "";
    }
  }

  async function refresh() {
    if (loading.value) return;
    loading.value = true;
    error.value = "";
    configError.value = "";
    try {
      await Promise.all([loadPosts(), loadConfig()]);
    } finally {
      lastScannedAt.value = new Date();
      loading.value = false;
    }
  }

  async function retryConfig() {
    configError.value = "";
    await loadConfig();
  }

  function openTutorial(url: string) {
    if (!url) {
      uni.showToast({ title: "公众号链接待配置", icon: "none" });
      return;
    }

    // #ifdef H5
    if (typeof window !== "undefined") {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    // #endif

    uni.navigateTo({
      url: `/pages/web-view/index?url=${encodeURIComponent(url)}`,
    });
  }

  async function subscribeResetReminder() {
    if (subscribing.value) return;
    if (!reminderState.value.available) {
      uni.showToast({ title: reminderState.value.caption, icon: "none" });
      return;
    }

    // #ifdef MP-WEIXIN
    subscribing.value = true;
    try {
      const templateId = reminderTemplateId.value;
      const permission = await requestResetSubscription(templateId);
      if (permission[templateId] !== "accept") {
        showSubscriptionSettingsGuide();
        return;
      }
      const login = await uni.login({ provider: "weixin" });
      if (!login.code) throw new Error("微信登录未返回授权码");
      const result = await subscribeCodexReset(login.code, templateId);
      uni.showToast({
        title: result.subscribed ? "订阅成功" : "订阅失败",
        icon: result.subscribed ? "success" : "none",
      });
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "订阅失败，请稍后重试";
      uni.showToast({ title: message, icon: "none" });
    } finally {
      subscribing.value = false;
    }
    // #endif

    // #ifndef MP-WEIXIN
    uni.showModal({
      title: "请在微信小程序中订阅",
      content: "H5 调试环境不支持微信订阅消息授权。",
      showCancel: false,
    });
    // #endif
  }

  onShow(refresh);

  return {
    posts,
    forecast,
    sourceUrl,
    aiTutorials,
    aiCommunity,
    reminderEnabled,
    reminderState,
    subscribing,
    monitoredAccount,
    loading,
    error,
    configError,
    conclusion,
    latestPosts,
    dateLabel,
    scanTimeLabel,
    refresh,
    retryConfig,
    openTutorial,
    subscribeResetReminder,
  };
}
