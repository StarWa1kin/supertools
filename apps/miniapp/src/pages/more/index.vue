<script setup lang="ts">
import {
  onShareAppMessage,
  onShareTimeline,
  onShow,
} from "@dcloudio/uni-app";

import ToolAppIcon from "../../components/ToolAppIcon.vue";
import ThemeSwitcher from "../../components/ThemeSwitcher.vue";
import { createPageShare } from "../../composables/usePageShare";
import { useTheme } from "../../composables/useTheme";
import { usePrimaryApp } from "../../composables/usePrimaryApp";
import {
  getEnabledApps,
  isAppAvailable,
  type ToolApp,
} from "../../config/apps";

const apps = getEnabledApps();
const availableCount = apps.filter((app) => isAppAvailable(app)).length;
const developingCount = apps.length - availableCount;
const { themeClass } = useTheme();
const { primaryAppId, refreshPrimaryApp, setPrimaryApp } = usePrimaryApp();
let suppressNextOpen = false;

const pageShare = createPageShare({
  title: "奇思妙箱｜简单好用的随身工具箱",
  path: "/pages/more/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);

function appIsAvailable(app: ToolApp) {
  return isAppAvailable(app);
}

function openApp(app: ToolApp) {
  if (suppressNextOpen) {
    suppressNextOpen = false;
    return;
  }

  if (!appIsAvailable(app)) {
    uni.showToast({ title: `「${app.name}」仍在开发中`, icon: "none" });
    return;
  }

  uni.navigateTo({ url: app.route });
}

function choosePrimaryApp(app: ToolApp) {
  if (!appIsAvailable(app)) return;

  suppressNextOpen = true;

  void uni
    .showModal({
      title: "设为首页主应用",
      content: `以后打开 Supertools，将优先展示「${app.name}」。`,
      confirmText: "设为首页",
      cancelText: "取消",
    })
    .then(({ confirm }) => {
      if (!confirm || !setPrimaryApp(app.id)) return;
      uni.showToast({ title: `首页已设为${app.name}`, icon: "none" });
    })
    .finally(() => {
      setTimeout(() => {
        suppressNextOpen = false;
      }, 300);
    });
}

onShow(refreshPrimaryApp);
</script>

<template>
  <view :class="['more-page', themeClass]">
    <view class="more-header">
      <view class="more-header__orbit" />
      <text class="eyebrow">Pocket utility desk</text>
      <view class="more-title" aria-label="少一点步骤，快一点答案。">
        <view class="more-title__line">
          <text class="more-title__lead">少</text>
          <text class="more-title__phrase">一点步骤</text>
          <text class="more-title__punctuation">，</text>
        </view>
        <view class="more-title__line more-title__line--answer">
          <text class="more-title__lead">快</text>
          <text class="more-title__phrase more-title__phrase--answer">一点答案</text>
          <text class="more-title__punctuation">。</text>
        </view>
      </view>
      <text class="more-description">
        『奇思妙箱』把零散但高频的需求，收进一个轻量工具台。
      </text>
    </view>

    <view class="appearance-panel">
      <view class="appearance-panel__heading">
        <text class="appearance-panel__title">外观</text>
        <text class="appearance-panel__meta">THEME</text>
      </view>
      <ThemeSwitcher />
    </view>

    <view class="app-grid" aria-label="全部工具">
      <view
        v-for="(app, index) in apps"
        :key="app.id"
        :class="[
          'app-launcher',
          {
            'app-launcher--primary':
              appIsAvailable(app) && primaryAppId === app.id,
            'app-launcher--unavailable': !appIsAvailable(app),
          },
        ]"
        :style="{ animationDelay: `${index * 45}ms` }"
        :hover-class="appIsAvailable(app) ? 'app-launcher--pressed' : 'none'"
        :hover-stay-time="80"
        :aria-disabled="!appIsAvailable(app)"
        @click="openApp(app)"
        @longpress="choosePrimaryApp(app)"
      >
        <view class="app-icon-wrap">
          <view class="app-icon-art">
            <ToolAppIcon :app="app" />
          </view>
          <text
            v-if="appIsAvailable(app) && primaryAppId === app.id"
            class="primary-badge"
            >首页</text
          >
          <text v-if="!appIsAvailable(app)" class="development-badge">
            {{ app.status }}
          </text>
        </view>
        <text class="app-launcher__name">{{ app.name }}</text>
      </view>
    </view>

    <text class="launcher-hint">长按应用图标，可设为首页主应用</text>

    <view v-if="apps.length === 0" class="empty-state">
      <text class="empty-state__mark">＋</text>
      <text class="empty-state__title">还没有可用工具</text>
      <text class="empty-state__detail"
        >在应用注册表中启用工具后，它会出现在这里。</text
      >
    </view>

    <view class="library-footer">
      <view class="library-footer__line" />
      <text v-if="developingCount > 0">
        {{ availableCount }} READY / {{ developingCount }} IN DEV
      </text>
      <text v-else>{{ apps.length }} APPS / READY</text>
    </view>
  </view>
</template>

<style scoped>
.more-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: calc(var(--status-bar-height, 0px) + 96rpx) 32rpx 180rpx;
  background-color: var(--color-page);
  color: var(--color-ink);
}

.more-header {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding: 0 8rpx;
}

.more-header__orbit {
  position: absolute;
  top: -56rpx;
  right: -176rpx;
  width: 352rpx;
  height: 352rpx;
  border: 1px solid currentColor;
  border-radius: 50%;
  opacity: 0.12;
  pointer-events: none;
}

.more-title {
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  margin-top: 26rpx;
  padding-bottom: 8rpx;
}

.more-title__line {
  display: flex;
  align-items: baseline;
  font-family: "Songti SC", "STSong", serif;
  line-height: 0.94;
  opacity: 0;
  transform: translateY(18rpx);
  animation: title-arrive 560ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.more-title__line--answer {
  position: relative;
  margin-top: 14rpx;
  margin-left: 54rpx;
  animation-delay: 80ms;
}

.more-title__line--answer::after {
  position: absolute;
  right: 18rpx;
  bottom: -16rpx;
  width: 122rpx;
  height: 3rpx;
  background: var(--color-signal);
  content: "";
  opacity: 0.72;
  transform: rotate(-2deg);
}

.more-title__lead,
.more-title__phrase,
.more-title__punctuation {
  display: block;
}

.more-title__lead {
  margin-right: 10rpx;
  font-size: 112rpx;
  font-weight: 900;
  letter-spacing: -0.1em;
  line-height: 0.78;
  text-shadow: 5rpx 6rpx 0 var(--color-shadow-soft);
}

.more-title__phrase {
  font-size: 66rpx;
  font-weight: 700;
  letter-spacing: 0.035em;
}

.more-title__phrase--answer {
  font-weight: 800;
}

.more-title__punctuation {
  margin-left: -4rpx;
  color: var(--color-signal);
  font-size: 62rpx;
  font-weight: 800;
}

.more-description {
  display: block;
  margin-top: 20rpx;
  max-width: 560rpx;
  font-size: 28rpx;
  line-height: 1.6;
  opacity: 0.58;
}

.appearance-panel {
  display: flex;
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 720px;
  min-height: 80rpx;
  margin: 42rpx auto 0;
  padding: 8rpx 4rpx 8rpx 8rpx;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--color-soft-border);
  border-bottom: 1px solid var(--color-soft-border);
}

.appearance-panel__heading {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.appearance-panel__title {
  font-size: 26rpx;
  font-weight: 700;
}

.appearance-panel__meta {
  font-family: monospace;
  font-size: 18rpx;
  letter-spacing: 0.08em;
  opacity: 0.32;
}

.app-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  column-gap: 18rpx;
  row-gap: 50rpx;
  width: 100%;
  max-width: 720px;
  margin: 44rpx auto 0;
}

.app-launcher {
  display: flex;
  min-width: 0;
  align-items: center;
  flex-direction: column;
  opacity: 0;
  transform: translateY(16rpx) scale(0.96);
  animation: app-arrive 360ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.app-icon-wrap {
  position: relative;
}

.primary-badge {
  position: absolute;
  right: -14rpx;
  bottom: -8rpx;
  display: flex;
  min-height: 34rpx;
  align-items: center;
  padding: 0 11rpx;
  border: 2rpx solid var(--color-page);
  border-radius: 999px;
  background: var(--color-ink);
  color: var(--color-page);
  font-size: 17rpx;
  font-weight: 800;
  line-height: 34rpx;
}

.development-badge {
  position: absolute;
  right: -16rpx;
  bottom: -8rpx;
  display: flex;
  min-height: 34rpx;
  align-items: center;
  padding: 0 11rpx;
  border: 2rpx solid var(--color-page);
  border-radius: 999px;
  background: #777771;
  color: #fff;
  font-size: 17rpx;
  font-weight: 800;
  line-height: 34rpx;
  letter-spacing: 0.04em;
}

.app-launcher--unavailable .app-icon-art {
  filter: grayscale(1);
  opacity: 0.42;
}

.app-launcher--unavailable .app-launcher__name {
  font-weight: 500;
  opacity: 0.38;
}

.app-launcher--primary .app-launcher__name {
  font-weight: 800;
}

.app-launcher--pressed {
  transform: scale(0.92) !important;
  opacity: 0.72 !important;
  transition:
    transform 100ms ease-out,
    opacity 100ms ease-out;
}

.app-launcher__name {
  display: -webkit-box;
  width: 100%;
  margin-top: 16rpx;
  overflow: hidden;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1.25;
  text-align: center;
  letter-spacing: 0.01em;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.launcher-hint {
  display: block;
  margin: 34rpx auto 0;
  color: var(--color-ink);
  font-size: 21rpx;
  text-align: center;
  opacity: 0.4;
}

.empty-state {
  display: flex;
  margin-top: 100rpx;
  align-items: center;
  flex-direction: column;
  text-align: center;
}

.empty-state__mark {
  display: flex;
  width: 112rpx;
  height: 112rpx;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--color-soft-border);
  border-radius: 28rpx;
  font-size: 46rpx;
}

.empty-state__title {
  margin-top: 28rpx;
  font-weight: 700;
}

.empty-state__detail {
  max-width: 440rpx;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.6;
  opacity: 0.5;
}

.library-footer {
  position: absolute;
  right: 40rpx;
  bottom: 130rpx;
  left: 40rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
  font-family: monospace;
  font-size: 20rpx;
  opacity: 0.35;
}

.library-footer__line {
  height: 1px;
  flex: 1;
  background: currentColor;
}

@keyframes app-arrive {
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes title-arrive {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .more-title__line,
  .app-launcher {
    opacity: 1;
    transform: none;
    animation: none;
  }

  .app-launcher--pressed {
    transform: none !important;
  }
}
</style>
