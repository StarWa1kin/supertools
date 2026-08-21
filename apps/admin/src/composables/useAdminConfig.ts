import { computed, ref } from "vue";
import { ElMessage } from "element-plus";

import { ApiError, getConfig, login, saveConfig } from "../api";
import type { CodexWatchConfig, TutorialConfig } from "../types";

const sessionKey = "supertools.admin.token";
const usernameKey = "supertools.admin.username";

function emptyConfig(): CodexWatchConfig {
  return {
    crawler: {
      account: "tibo",
      keywords: ["codex", "quota", "limit", "reset"],
      scheduleEnabled: true,
      intervalMinutes: 30,
      maxPosts: 20,
    },
    tutorials: [],
    community: null,
    reminder: {
      enabled: false,
      appId: "",
      appSecret: "",
      templateId: "",
      page: "pages/codex-watch/index",
      statusKey: "thing1",
      timeKey: "time3",
      remarkKey: "thing5",
    },
    updatedAt: null,
  };
}

export function useAdminConfig() {
  const token = ref(localStorage.getItem(sessionKey) || "");
  const username = ref(localStorage.getItem(usernameKey) || "admin");
  const config = ref<CodexWatchConfig>(emptyConfig());
  const loading = ref(false);
  const saving = ref(false);
  const authenticated = computed(() => Boolean(token.value));

  function clearSession() {
    token.value = "";
    localStorage.removeItem(sessionKey);
    localStorage.removeItem(usernameKey);
  }

  async function signIn(account: string, password: string) {
    loading.value = true;
    try {
      const session = await login(account, password);
      token.value = session.accessToken;
      username.value = session.username;
      localStorage.setItem(sessionKey, session.accessToken);
      localStorage.setItem(usernameKey, session.username);
      await load();
    } finally {
      loading.value = false;
    }
  }

  async function load() {
    if (!token.value) return;
    loading.value = true;
    try {
      config.value = await getConfig(token.value);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) clearSession();
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function save() {
    saving.value = true;
    try {
      config.value = await saveConfig(token.value, config.value);
      ElMessage.success("配置已保存并生效");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) clearSession();
      throw error;
    } finally {
      saving.value = false;
    }
  }

  function addTutorial() {
    const tutorial: TutorialConfig = {
      id: crypto.randomUUID(),
      title: "",
      description: "",
      url: "",
    };
    config.value.tutorials.push(tutorial);
  }

  function removeTutorial(index: number) {
    config.value.tutorials.splice(index, 1);
  }

  function moveTutorial(index: number, offset: -1 | 1) {
    const next = index + offset;
    if (next < 0 || next >= config.value.tutorials.length) return;
    const [item] = config.value.tutorials.splice(index, 1);
    config.value.tutorials.splice(next, 0, item);
  }

  function enableCommunity() {
    config.value.community = {
      title: "AI 技术交流群",
      description: "交流 Codex、AI 编程与自动化实践",
      qrCode: "",
    };
  }

  function disableCommunity() {
    config.value.community = null;
  }

  return {
    token,
    authenticated,
    username,
    config,
    loading,
    saving,
    signIn,
    load,
    save,
    clearSession,
    addTutorial,
    removeTutorial,
    moveTutorial,
    enableCommunity,
    disableCommunity,
  };
}
