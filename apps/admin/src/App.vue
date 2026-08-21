<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import AdminDashboard from "./components/AdminDashboard.vue";
import LoginView from "./components/LoginView.vue";
import { useAdminConfig } from "./composables/useAdminConfig";
import { useDeployment } from "./composables/useDeployment";
import { useRequestLogs } from "./composables/useRequestLogs";
import { getReminderSubscriptions, sendReminderTest } from "./api";
import type { ReminderSubscription, RequestLogQuery } from "./types";

const admin = useAdminConfig();
const route = useRoute();
const router = useRouter();
const deployment = useDeployment(() => admin.token.value, admin.clearSession);
const requestLogs = useRequestLogs(() => admin.token.value, admin.clearSession);
const reminderSubscriptions = ref<ReminderSubscription[]>([]);
const reminderLoading = ref(false);
const reminderError = ref("");
const testingSubscriptionId = ref("");

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "操作未完成，请稍后重试";
}

async function handleLogin(payload: { username: string; password: string }) {
  try {
    await admin.signIn(payload.username, payload.password);
    const tasks = [
      admin.load(),
      deployment.loadDeployment(),
      requestLogs.load(),
    ];
    if (route.name === "reminders") tasks.push(loadReminderSubscriptions());
    await Promise.all(tasks);
    if (route.name === "login") await router.replace("/codex-watch/crawler");
    ElMessage.success("欢迎回来");
  } catch (error) {
    ElMessage.error(messageOf(error));
  }
}

async function loadRequestLogs(query?: RequestLogQuery) {
  try {
    await requestLogs.load(query);
  } catch (error) {
    ElMessage.error(messageOf(error));
  }
}

async function handleSave() {
  try {
    await admin.save();
  } catch (error) {
    ElMessage.error(messageOf(error));
  }
}

async function handleDeploy(target: "server" | "admin") {
  try {
    await deployment.deploy(target);
    ElMessage.success(`${target === "admin" ? "管理端" : "API 服务"}部署任务已启动`);
  } catch (error) {
    ElMessage.error(messageOf(error));
  }
}

async function loadReminderSubscriptions() {
  if (!admin.token.value || reminderLoading.value) return;
  reminderLoading.value = true;
  reminderError.value = "";
  try {
    reminderSubscriptions.value = await getReminderSubscriptions(admin.token.value);
  } catch (error) {
    reminderSubscriptions.value = [];
    reminderError.value = messageOf(error);
    throw error;
  } finally {
    reminderLoading.value = false;
  }
}

async function handleRefreshReminders() {
  try {
    await loadReminderSubscriptions();
  } catch (error) {
    ElMessage.error(messageOf(error));
  }
}

async function handleReminderTest(subscriptionId: string) {
  if (testingSubscriptionId.value) return;
  testingSubscriptionId.value = subscriptionId;
  try {
    const result = await sendReminderTest(admin.token.value, subscriptionId);
    reminderSubscriptions.value = reminderSubscriptions.value.map((item) => (
      item.id === subscriptionId ? result.subscription : item
    ));
    ElMessage.success("测试消息发送成功，已消耗 1 次订阅授权");
  } catch (error) {
    ElMessage.error(messageOf(error));
  } finally {
    testingSubscriptionId.value = "";
  }
}

onMounted(async () => {
  if (!admin.authenticated.value) return;
  try {
    await admin.load();
    await deployment.loadDeployment();
    if (route.name === "reminders") await loadReminderSubscriptions();
    await requestLogs.load();
  } catch (error) {
    ElMessage.error(messageOf(error));
  }
});

watch(
  () => route.name,
  async (name, previous) => {
    if (name !== "reminders" || previous === undefined || !admin.authenticated.value) return;
    await handleRefreshReminders();
  },
);
</script>

<template>
  <LoginView
    v-if="!admin.authenticated.value"
    :loading="admin.loading.value"
    @submit="handleLogin"
  />
  <AdminDashboard
    v-else
    :config="admin.config.value"
    :username="admin.username.value"
    :loading="admin.loading.value"
    :saving="admin.saving.value"
    :deployment="deployment.deployment.value"
    :deploying="deployment.loadingDeployment.value"
    :reminder-subscriptions="reminderSubscriptions"
    :reminder-loading="reminderLoading"
    :reminder-error="reminderError"
    :testing-subscription-id="testingSubscriptionId"
    :request-logs="requestLogs.logs.value"
    :request-logs-loading="requestLogs.loading.value"
    @save="handleSave"
    @logout="admin.clearSession"
    @add-tutorial="admin.addTutorial"
    @remove-tutorial="admin.removeTutorial"
    @move-tutorial="admin.moveTutorial"
    @enable-community="admin.enableCommunity"
    @disable-community="admin.disableCommunity"
    @deploy="handleDeploy"
    @refresh-deployment="deployment.loadDeployment"
    @refresh-reminders="handleRefreshReminders"
    @test-reminder="handleReminderTest"
    @refresh-request-logs="loadRequestLogs"
  />
</template>
