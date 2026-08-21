<script setup lang="ts">
import { computed, ref } from "vue";
import type { UploadFile } from "element-plus";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowDown,
  ArrowUp,
  ChatLineRound,
  Check,
  Delete,
  DataAnalysis,
  Document,
  Link,
  Lock,
  Plus,
  Reading,
  Setting,
  SwitchButton,
  Upload,
  Promotion,
  Refresh,
  CircleCheck,
  Warning,
  Bell,
  Operation,
} from "@element-plus/icons-vue";

import type {
  CodexWatchConfig,
  DeploymentStatus,
  ReminderSubscription,
  RequestLogPage,
  RequestLogQuery,
} from "../types";

const props = defineProps<{
  config: CodexWatchConfig;
  username: string;
  loading: boolean;
  saving: boolean;
  deployment: DeploymentStatus;
  deploying: boolean;
  reminderSubscriptions: ReminderSubscription[];
  reminderLoading: boolean;
  testingSubscriptionId: string;
  requestLogs: RequestLogPage;
  requestLogsLoading: boolean;
}>();

const emit = defineEmits<{
  save: [];
  logout: [];
  addTutorial: [];
  removeTutorial: [index: number];
  moveTutorial: [index: number, offset: -1 | 1];
  enableCommunity: [];
  disableCommunity: [];
  deploy: [target: "server" | "admin"];
  refreshDeployment: [];
  refreshReminders: [];
  testReminder: [subscriptionId: string];
  refreshRequestLogs: [query?: RequestLogQuery];
}>();

type SectionId = "crawler" | "tutorials" | "community" | "reminders" | "deployment" | "logs";
const route = useRoute();
const router = useRouter();
const keywordInput = ref("");
const logStatus = ref<number | undefined>();
const logPath = ref("");
const logOffset = ref(0);
const logLimit = 50;

const intelligenceSections = [
  { id: "crawler" as const, label: "采集策略", caption: "Crawler", icon: Setting },
  { id: "tutorials" as const, label: "AI 教程", caption: "Tutorials", icon: Reading },
  { id: "community" as const, label: "交流群", caption: "Community", icon: ChatLineRound },
];
const operationsSections = [
  { id: "reminders" as const, label: "推送测试", caption: "Reminders", icon: Bell },
  { id: "logs" as const, label: "请求日志", caption: "Request logs", icon: Document },
  { id: "deployment" as const, label: "一键部署", caption: "Deployment", icon: Promotion },
];
const sections = [...intelligenceSections, ...operationsSections];

const activeSection = computed<SectionId>(() => (route.meta.section as SectionId | undefined) ?? "crawler");
const current = computed(() => sections.find((item) => item.id === activeSection.value)!);
const communityVisible = computed(() => Boolean(props.config.community?.qrCode));
const isOperations = computed(() => operationsSections.some((item) => item.id === activeSection.value));

function selectSection(section: SectionId) {
  router.push(section === "crawler" ? "/codex-watch/crawler" : section === "tutorials" ? "/codex-watch/tutorials" : section === "community" ? "/codex-watch/community" : section === "reminders" ? "/ops/reminders" : section === "logs" ? "/ops/request-logs" : "/ops/deployment");
  if (section === "logs") refreshRequestLogs();
}

function refreshRequestLogs(offset = 0) {
  logOffset.value = offset;
  emit("refreshRequestLogs", {
    limit: logLimit,
    offset,
    status: logStatus.value,
    path: logPath.value,
  });
}

function formatLogTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function addKeyword() {
  const value = keywordInput.value.trim().toLowerCase();
  if (!value || props.config.crawler.keywords.includes(value)) return;
  if (props.config.crawler.keywords.length >= 30) {
    ElMessage.warning("最多配置 30 个关键词");
    return;
  }
  props.config.crawler.keywords.push(value);
  keywordInput.value = "";
}

function removeKeyword(keyword: string) {
  if (props.config.crawler.keywords.length === 1) {
    ElMessage.warning("至少保留一个关键词");
    return;
  }
  props.config.crawler.keywords = props.config.crawler.keywords.filter((item) => item !== keyword);
}

function updateCommunity(enabled: boolean) {
  if (enabled) emit("enableCommunity");
  else emit("disableCommunity");
}

function readQr(file: UploadFile) {
  if (!file.raw) return;
  if (!file.raw.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }
  if (file.raw.size > 2 * 1024 * 1024) {
    ElMessage.error("二维码图片不能超过 2MB");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    if (props.config.community && typeof reader.result === "string") {
      props.config.community.qrCode = reader.result;
    }
  };
  reader.readAsDataURL(file.raw);
}

async function removeTutorial(index: number) {
  try {
    await ElMessageBox.confirm("删除这条教程配置？保存后小程序将不再展示。", "删除教程", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    emit("removeTutorial", index);
  } catch {
    // User cancelled the confirmation.
  }
}

function submit() {
  if (!props.config.crawler.account.trim()) {
    router.push("/codex-watch/crawler");
    ElMessage.error("请填写监控账号");
    return;
  }
  const invalidTutorial = props.config.tutorials.find((item) => !item.title.trim() || !/^https?:\/\//i.test(item.url));
  if (invalidTutorial) {
    router.push("/codex-watch/tutorials");
    ElMessage.error("请补全教程标题和有效的 http(s) 链接");
    return;
  }
  emit("save");
}

function formatUpdatedAt(value: string | null) {
  if (!value) return "尚未保存";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

const deploymentLabel = computed(() => ({
  idle: "尚未部署",
  running: "部署进行中",
  succeeded: "部署成功",
  failed: "部署失败",
  unavailable: "服务未配置",
}[props.deployment.status]));

const deploymentTargetLabel = computed(() => (
  props.deployment.target === "admin" ? "管理端" : props.deployment.target === "server" ? "API 服务" : "服务"
));

function deployedVersion(target: "server" | "admin") {
  return props.deployment.targets?.[target]?.version || "未识别";
}

function deployedAt(target: "server" | "admin") {
  const value = props.deployment.targets?.[target]?.deployedAt;
  return value ? formatUpdatedAt(value) : "尚无发布记录";
}

async function confirmDeploy(target: "server" | "admin") {
  const targetLabel = target === "admin" ? "管理端" : "API 服务";
  const buildTarget = target === "admin" ? "admin" : "server";
  try {
    await ElMessageBox.confirm(
      `将拉取远程仓库最新提交，仅重新构建并启动${targetLabel}（${buildTarget}）。部署期间该服务可能短暂重连。`,
      `确认部署${targetLabel}`,
      { confirmButtonText: "开始部署", cancelButtonText: "取消", type: "warning" },
    );
    emit("deploy", target);
  } catch {
    // User cancelled the confirmation.
  }
}

async function confirmReminderTest(subscription: ReminderSubscription) {
  try {
    await ElMessageBox.confirm(
      "这会向该用户发送一条真实的微信订阅消息，并消耗其 1 次可用推送授权。",
      "确认发送测试推送",
      { confirmButtonText: "发送并消耗次数", cancelButtonText: "取消", type: "warning" },
    );
    emit("testReminder", subscription.id);
  } catch {
    // User cancelled the confirmation.
  }
}
</script>

<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="sidebar-product-icon"><el-icon><DataAnalysis /></el-icon></span>
        <div><strong>SUPERTOOLS</strong><small>INTELLIGENCE OPS</small></div>
      </div>

      <nav class="side-nav" aria-label="后台导航">
        <div class="nav-parent">
          <span class="nav-parent-icon"><el-icon><DataAnalysis /></el-icon></span>
          <span><b>Codex 情报</b><small>CODEX WATCH</small></span>
          <el-icon class="nav-parent-chevron"><ArrowDown /></el-icon>
        </div>
        <div class="subnav">
          <button
            v-for="(section, index) in intelligenceSections"
            :key="section.id"
            :class="['nav-item', { 'nav-item--active': activeSection === section.id }]"
            @click="selectSection(section.id)"
          >
            <span class="nav-index">0{{ index + 1 }}</span>
            <el-icon><component :is="section.icon" /></el-icon>
            <span class="nav-copy"><b>{{ section.label }}</b><small>{{ section.caption }}</small></span>
            <span class="nav-marker" />
          </button>
        </div>
        <div class="nav-parent nav-parent--operations">
          <span class="nav-parent-icon"><el-icon><Operation /></el-icon></span>
          <span><b>运维中心</b><small>OPERATIONS</small></span>
          <el-icon class="nav-parent-chevron"><ArrowDown /></el-icon>
        </div>
        <div class="subnav subnav--operations">
          <button
            v-for="(section, index) in operationsSections"
            :key="section.id"
            :class="['nav-item', { 'nav-item--active': activeSection === section.id }]"
            @click="selectSection(section.id)"
          >
            <span class="nav-index">0{{ index + 4 }}</span>
            <el-icon><component :is="section.icon" /></el-icon>
            <span class="nav-copy"><b>{{ section.label }}</b><small>{{ section.caption }}</small></span>
            <span class="nav-marker" />
          </button>
        </div>
      </nav>

      <div class="sidebar-foot">
        <div class="operator-chip">
          <span>{{ username.slice(0, 1).toUpperCase() }}</span>
          <div><b>{{ username }}</b><small>管理员</small></div>
        </div>
        <el-tooltip content="退出登录" placement="top">
          <button class="icon-action" aria-label="退出登录" @click="emit('logout')">
            <el-icon><SwitchButton /></el-icon>
          </button>
        </el-tooltip>
      </div>
    </aside>

    <header class="mobile-header">
      <div class="sidebar-brand">
        <span class="sidebar-product-icon"><el-icon><DataAnalysis /></el-icon></span>
        <div><strong>SUPERTOOLS</strong><small>CODEX OPS</small></div>
      </div>
      <button class="icon-action" aria-label="退出登录" @click="emit('logout')">
        <el-icon><SwitchButton /></el-icon>
      </button>
    </header>

    <div class="mobile-context">
      <span><el-icon><component :is="isOperations ? Operation : DataAnalysis" /></el-icon></span>
      <div><b>{{ isOperations ? "运维中心" : "Codex 情报" }}</b><small>{{ isOperations ? "OPERATIONS" : "CODEX WATCH" }}</small></div>
    </div>

    <div class="mobile-tabs">
      <button
        v-for="section in sections"
        :key="section.id"
        :class="{ active: activeSection === section.id }"
        @click="selectSection(section.id)"
      >
        <el-icon><component :is="section.icon" /></el-icon>
        <span>{{ section.label }}</span>
      </button>
    </div>

    <main class="workspace" v-loading="loading">
      <div class="workspace-head">
        <div>
          <p class="workspace-kicker">{{ current.caption.toUpperCase() }} / {{ isOperations ? "OPERATIONS" : "CONFIGURATION" }}</p>
          <h1>{{ current.label }}</h1>
        </div>
        <div class="save-state">
          <span class="save-state-dot" />
          <span>上次保存 {{ formatUpdatedAt(config.updatedAt) }}</span>
        </div>
      </div>

      <section v-show="activeSection === 'crawler'" class="workspace-section">
        <div class="section-intro">
          <div>
            <span class="section-number">01</span>
            <h2 class="section-title">Tibo 动态采集策略</h2>
            <p class="section-copy">设置目标账号、匹配词、抓取节奏和每次读取数量。</p>
          </div>
          <div :class="['status-pill', { 'status-pill--paused': !config.crawler.scheduleEnabled }]">
            <i />{{ config.crawler.scheduleEnabled ? "定时任务在线" : "定时任务已暂停" }}
          </div>
        </div>

        <div class="strategy-grid">
          <div class="panel-surface config-panel">
            <div class="panel-label"><Setting /><span>基础设置</span></div>
            <el-form label-position="top">
              <el-form-item label="监控账号">
                <el-input v-model="config.crawler.account" size="large" maxlength="50">
                  <template #prefix><span class="input-at">@</span></template>
                </el-input>
                <p class="field-help">填写 X 用户名，不需要输入 @ 或完整链接。</p>
              </el-form-item>

              <el-form-item label="自动采集">
                <div class="switch-field">
                  <div><b>定时任务</b><small>按设置的时间间隔持续检查公开动态</small></div>
                  <el-switch v-model="config.crawler.scheduleEnabled" />
                </div>
              </el-form-item>

              <div class="number-fields">
                <el-form-item label="抓取频率">
                  <el-input-number v-model="config.crawler.intervalMinutes" :min="5" :max="10080" :step="5" controls-position="right" />
                  <p class="field-help">分钟，范围 5 分钟至 7 天</p>
                </el-form-item>
                <el-form-item label="每次抓取">
                  <el-input-number v-model="config.crawler.maxPosts" :min="1" :max="100" controls-position="right" />
                  <p class="field-help">条，范围 1–100</p>
                </el-form-item>
              </div>
            </el-form>
          </div>

          <div class="panel-surface keyword-panel">
            <div class="panel-label"><Document /><span>关键词过滤</span></div>
            <p class="panel-description">帖子命中任意一个关键词后进入情报判断。英文统一按小写保存。</p>
            <div class="keyword-input">
              <el-input v-model="keywordInput" maxlength="40" placeholder="输入关键词" @keyup.enter="addKeyword" />
              <el-button :icon="Plus" aria-label="添加关键词" @click="addKeyword" />
            </div>
            <div class="keyword-cloud">
              <el-tag
                v-for="keyword in config.crawler.keywords"
                :key="keyword"
                closable
                disable-transitions
                @close="removeKeyword(keyword)"
              >{{ keyword }}</el-tag>
            </div>
            <div class="reference-note">
              <Lock />
              <p><b>边界与参考项目一致</b><span>抓取间隔 5–10080 分钟；每次 1–100 条。</span></p>
            </div>
          </div>
        </div>
      </section>

      <section v-show="activeSection === 'tutorials'" class="workspace-section">
        <div class="section-intro">
          <div>
            <span class="section-number">02</span>
            <h2 class="section-title">AI 教程板块</h2>
            <p class="section-copy">只有已保存的教程会出现在小程序；列表为空时整个板块隐藏。</p>
          </div>
          <el-button type="primary" :icon="Plus" @click="emit('addTutorial')">添加教程</el-button>
        </div>

        <div v-if="config.tutorials.length" class="tutorial-editor-list">
          <article v-for="(tutorial, index) in config.tutorials" :key="tutorial.id" class="tutorial-editor">
            <div class="tutorial-order">
              <span>{{ String(index + 1).padStart(2, "0") }}</span>
              <div>
                <el-tooltip content="上移" placement="top"><button :disabled="index === 0" aria-label="上移" @click="emit('moveTutorial', index, -1)"><ArrowUp /></button></el-tooltip>
                <el-tooltip content="下移" placement="top"><button :disabled="index === config.tutorials.length - 1" aria-label="下移" @click="emit('moveTutorial', index, 1)"><ArrowDown /></button></el-tooltip>
              </div>
            </div>
            <div class="tutorial-fields">
              <el-form label-position="top">
                <div class="tutorial-main-fields">
                  <el-form-item label="教程标题"><el-input v-model="tutorial.title" maxlength="80" show-word-limit placeholder="例如：Codex 新手快速上手" /></el-form-item>
                  <el-form-item label="教程链接"><el-input v-model="tutorial.url" maxlength="500" placeholder="https://..."><template #prefix><el-icon><Link /></el-icon></template></el-input></el-form-item>
                </div>
                <el-form-item label="一句话介绍"><el-input v-model="tutorial.description" maxlength="160" show-word-limit placeholder="告诉用户这篇教程能解决什么问题" /></el-form-item>
              </el-form>
            </div>
            <el-tooltip content="删除教程" placement="top">
              <button class="delete-action" aria-label="删除教程" @click="removeTutorial(index)"><Delete /></button>
            </el-tooltip>
          </article>
        </div>

        <div v-else class="content-empty">
          <span class="empty-symbol"><Reading /></span>
          <h3>暂未配置教程</h3>
          <p>当前小程序不会展示 AI 教程板块。</p>
          <el-button :icon="Plus" @click="emit('addTutorial')">添加第一篇教程</el-button>
        </div>
      </section>

      <section v-show="activeSection === 'community'" class="workspace-section">
        <div class="section-intro">
          <div>
            <span class="section-number">03</span>
            <h2 class="section-title">交流群入口</h2>
            <p class="section-copy">上传群二维码后，小程序才会展示完整的社群邀请区。</p>
          </div>
          <div class="community-switch">
            <span>{{ config.community ? "已启用" : "未启用" }}</span>
            <el-switch :model-value="Boolean(config.community)" @change="updateCommunity(Boolean($event))" />
          </div>
        </div>

        <div v-if="config.community" class="community-layout">
          <div class="panel-surface config-panel">
            <div class="panel-label"><ChatLineRound /><span>展示文案</span></div>
            <el-form label-position="top">
              <el-form-item label="板块标题"><el-input v-model="config.community.title" maxlength="40" show-word-limit /></el-form-item>
              <el-form-item label="社群介绍"><el-input v-model="config.community.description" type="textarea" :rows="4" maxlength="160" show-word-limit /></el-form-item>
            </el-form>
            <div :class="['visibility-callout', { visible: communityVisible }]">
              <Check v-if="communityVisible" /><Upload v-else />
              <div><b>{{ communityVisible ? "小程序将展示此板块" : "等待上传二维码" }}</b><span>{{ communityVisible ? "保存后用户即可长按识别入群" : "没有二维码时，板块保持隐藏" }}</span></div>
            </div>
          </div>

          <div class="panel-surface qr-panel">
            <div class="panel-label"><Upload /><span>群二维码</span></div>
            <div class="qr-stage">
              <img v-if="config.community.qrCode" :src="config.community.qrCode" alt="交流群二维码预览" />
              <div v-else class="qr-empty"><span>QR</span><small>暂无图片</small></div>
            </div>
            <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="readQr">
              <el-button class="upload-button" :icon="Upload">选择二维码图片</el-button>
            </el-upload>
            <el-button v-if="config.community.qrCode" text type="danger" @click="config.community.qrCode = ''">移除当前图片</el-button>
            <p class="upload-hint">支持 JPG、PNG、WebP，文件不超过 2MB。</p>
          </div>
        </div>

        <div v-else class="content-empty">
          <span class="empty-symbol"><ChatLineRound /></span>
          <h3>交流群入口未启用</h3>
          <p>小程序当前不会显示社群相关内容。</p>
          <el-button :icon="Plus" @click="emit('enableCommunity')">启用交流群配置</el-button>
        </div>
      </section>

      <section v-show="activeSection === 'deployment'" class="workspace-section">
        <div class="section-intro">
          <div>
            <span class="section-number">05</span>
            <h2 class="section-title">生产环境部署</h2>
            <p class="section-copy">按服务独立构建与更新，避免无关镜像拉取阻塞发布。</p>
          </div>
          <div :class="['deploy-status', `deploy-status--${deployment.status}`]">
            <i />{{ deploymentLabel }}
          </div>
        </div>

        <div class="deployment-grid">
          <div class="panel-surface deployment-action-panel">
            <div class="deployment-emblem"><Promotion /></div>
            <p class="workspace-kicker">RELEASE PIPELINE</p>
            <h3>选择部署目标</h3>
            <p>固定执行安全的快进拉取与 Docker Compose 构建流程，不接受页面传入的命令或路径。</p>
            <ol class="deployment-steps">
              <li><span>01</span><div><b>同步仓库</b><small>git pull --ff-only</small></div></li>
              <li><span>02</span><div><b>构建目标镜像</b><small>server 或 admin</small></div></li>
              <li><span>03</span><div><b>更新并校验目标服务</b><small>docker compose up -d --no-deps</small></div></li>
            </ol>
            <div class="deployment-buttons">
              <el-button
                type="primary"
                size="large"
                :icon="Promotion"
                :loading="deploying && deployment.target === 'admin'"
                :disabled="deployment.status === 'running' || deployment.status === 'unavailable'"
                @click="confirmDeploy('admin')"
              >{{ deployment.status === "running" && deployment.target === "admin" ? "正在部署管理端" : deployment.status === "unavailable" ? "部署服务未配置" : "部署 Admin" }}</el-button>
              <el-button
                size="large"
                :icon="Promotion"
                :loading="deploying && deployment.target === 'server'"
                :disabled="deployment.status === 'running' || deployment.status === 'unavailable'"
                @click="confirmDeploy('server')"
              >{{ deployment.status === "running" && deployment.target === "server" ? "正在部署 API" : deployment.status === "unavailable" ? "部署服务未配置" : "部署 Server" }}</el-button>
            </div>
          </div>

          <div class="deployment-inspection-column">
            <div class="deployment-version-panel">
              <div class="deployment-version-head"><span>RUNNING RELEASES</span><el-button text :icon="Refresh" :loading="deployment.status === 'running'" @click="emit('refreshDeployment')">刷新核对</el-button></div>
              <div class="deployment-version-list">
                <div v-for="target in ['admin', 'server'] as const" :key="target" class="deployment-version-row">
                  <span :class="['deployment-version-service', `deployment-version-service--${target}`]">{{ target === 'admin' ? 'ADMIN' : 'API' }}</span>
                  <div><small>版本号</small><b>{{ deployedVersion(target) }}</b></div>
                  <div><small>部署时间</small><b>{{ deployedAt(target) }}</b></div>
                </div>
              </div>
            </div>
            <div class="panel-surface deployment-log-panel">
            <div class="deployment-log-head">
              <div>
                <component :is="deployment.status === 'failed' ? Warning : CircleCheck" />
                <span><b>{{ deploymentTargetLabel }}{{ deploymentLabel }}</b><small>{{ deployment.finishedAt ? formatUpdatedAt(deployment.finishedAt) : "等待执行" }}</small></span>
              </div>
              <el-button text :icon="Refresh" :loading="deployment.status === 'running'" @click="emit('refreshDeployment')">刷新</el-button>
            </div>
            <pre class="deployment-log">{{ deployment.log || "$ 等待部署任务…" }}</pre>
            </div>
          </div>
        </div>
      </section>

      <section v-show="activeSection === 'reminders'" class="workspace-section">
        <div class="section-intro">
          <div>
            <span class="section-number">04</span>
            <h2 class="section-title">微信订阅推送测试</h2>
            <p class="section-copy">仅显示已在小程序完成订阅的用户。OpenID 始终脱敏；测试发送会消耗一次订阅授权。</p>
          </div>
          <el-button :icon="Refresh" :loading="reminderLoading" @click="emit('refreshReminders')">刷新列表</el-button>
        </div>

        <div class="reminder-guide">
          <Bell />
          <div><b>建议测试流程</b><span>先用测试微信号在小程序点击“订阅重置提醒”，回到这里刷新并选择该条记录发送。</span></div>
        </div>

        <div v-if="reminderSubscriptions.length" class="reminder-list" v-loading="reminderLoading">
          <article v-for="subscription in reminderSubscriptions" :key="subscription.id" class="reminder-row">
            <div class="reminder-user"><span><Bell /></span><div><b>{{ subscription.openidMasked }}</b><small>订阅于 {{ formatUpdatedAt(subscription.subscribedAt) }}</small></div></div>
            <div class="reminder-meta"><small>模板</small><b>{{ subscription.templateId }}</b></div>
            <div :class="['reminder-credit', { exhausted: subscription.remainingDeliveries === 0 }]">
              <small>可用次数</small><b>{{ subscription.remainingDeliveries }}</b>
            </div>
            <el-button type="primary" :loading="testingSubscriptionId === subscription.id" :disabled="subscription.remainingDeliveries === 0" @click="confirmReminderTest(subscription)">
              {{ subscription.remainingDeliveries === 0 ? "已用完" : "发送测试" }}
            </el-button>
          </article>
        </div>
        <div v-else class="content-empty reminder-empty" v-loading="reminderLoading">
          <span class="empty-symbol"><Bell /></span>
          <h3>暂无可测试的订阅</h3>
          <p>请先在小程序内完成一次“订阅重置提醒”。</p>
        </div>
      </section>

      <section v-show="activeSection === 'logs'" class="workspace-section">
        <div class="section-intro">
          <div>
            <span class="section-number">05</span>
            <h2 class="section-title">接口请求日志</h2>
            <p class="section-copy">查看 API 调用时间、来源 IP、状态码与响应耗时；日志会保留在服务端。</p>
          </div>
          <el-button :icon="Refresh" :loading="requestLogsLoading" @click="refreshRequestLogs(logOffset)">刷新日志</el-button>
        </div>

        <div class="panel-surface request-log-panel">
          <div class="request-log-toolbar">
            <div class="request-log-count"><i />已记录 <b>{{ requestLogs.total }}</b> 条请求</div>
            <div class="request-log-filters">
              <el-select v-model="logStatus" clearable placeholder="全部状态" @change="refreshRequestLogs()">
                <el-option :value="200" label="200 成功" />
                <el-option :value="400" label="400 客户端错误" />
                <el-option :value="401" label="401 未认证" />
                <el-option :value="404" label="404 未找到" />
                <el-option :value="500" label="500 服务端错误" />
              </el-select>
              <el-input v-model="logPath" clearable placeholder="筛选接口路径" @keyup.enter="refreshRequestLogs()" />
              <el-button @click="refreshRequestLogs()">筛选</el-button>
            </div>
          </div>
          <div class="request-log-table-wrap" v-loading="requestLogsLoading">
            <table class="request-log-table">
              <thead><tr><th>请求时间</th><th>来源 IP</th><th>方法</th><th>接口路径</th><th>状态</th><th>耗时</th><th>客户端</th></tr></thead>
              <tbody>
                <tr v-for="log in requestLogs.items" :key="log.id">
                  <td>{{ formatLogTime(log.requestedAt) }}</td><td>{{ log.clientIp }}</td><td><span class="method-tag">{{ log.method }}</span></td>
                  <td class="request-log-path" :title="log.path">{{ log.path }}</td><td><span :class="['request-status', `request-status--${String(log.statusCode)[0]}`]">{{ log.statusCode }}</span></td>
                  <td>{{ log.durationMs }} ms</td><td class="request-log-agent" :title="log.userAgent">{{ log.userAgent || "—" }}</td>
                </tr>
                <tr v-if="!requestLogsLoading && !requestLogs.items.length"><td colspan="7" class="request-log-empty">暂无匹配的请求记录</td></tr>
              </tbody>
            </table>
          </div>
          <div class="request-log-pagination">
            <span>每页 {{ logLimit }} 条</span>
            <el-button :disabled="logOffset === 0" @click="refreshRequestLogs(Math.max(0, logOffset - logLimit))">上一页</el-button>
            <el-button :disabled="logOffset + logLimit >= requestLogs.total" @click="refreshRequestLogs(logOffset + logLimit)">下一页</el-button>
          </div>
        </div>
      </section>

      <footer v-if="!['deployment', 'reminders', 'logs'].includes(activeSection)" class="save-bar">
        <div><span class="save-bar-beacon" /><p><b>配置变更尚需保存</b><small>保存后公开接口与小程序同步生效</small></p></div>
        <el-button type="primary" size="large" :loading="saving" @click="submit">{{ saving ? "正在保存" : "保存全部配置" }}</el-button>
      </footer>
    </main>
  </div>
</template>
