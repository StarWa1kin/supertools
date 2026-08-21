<script setup lang="ts">
import { computed } from "vue";
import { onShow } from "@dcloudio/uni-app";

import { useVideoParser } from "../composables/useVideoParser";
import { useTheme } from "../composables/useTheme";
import { consumeVideoParserPrefill } from "../composables/videoParserHistory";

const { theme, themeClass } = useTheme();
const progressColor = computed(() =>
  theme.value === "dark"
    ? "#58a6ff"
    : theme.value === "blue"
      ? "#2563eb"
      : "#171915",
);
const progressBackground = computed(() =>
  theme.value === "dark"
    ? "#2c3742"
    : theme.value === "blue"
      ? "#c8d9ef"
      : "#ddd8ca",
);

const {
  activeResultView,
  clear,
  copySource,
  copyCaption,
  copyFeedback,
  coverUrl,
  downloadAllImages,
  downloadAsset,
  downloadProgress,
  error,
  loading,
  pasteFromClipboard,
  previewAssets,
  previewImage,
  result,
  saveStatus,
  saving,
  shareText,
  submit,
} = useVideoParser();

function showTutorial() {
  uni.showModal({
    title: "使用教程",
    content:
      "1. 在平台内复制公开作品的分享链接\n2. 粘贴分享文案或链接并开始解析\n3. 解析完成后预览并保存视频或图片",
    showCancel: false,
    confirmText: "知道了",
  });
}

function openHistory() {
  uni.navigateTo({ url: "/pages/video-parser-history/index" });
}

onShow(() => {
  const prefill = consumeVideoParserPrefill();
  if (prefill) shareText.value = prefill;
});
</script>

<template>
  <view :class="['page-shell parser-page pt-8', themeClass]">
    <view class="page-intro">
      <text class="page-title">视频解析</text>
      <view class="intro-meta mt-3">
        <text class="text-sm leading-6 opacity-65">下载无水印的视频</text>
        <view class="intro-actions">
          <button class="header-action" @click="openHistory">解析记录</button>
          <button class="header-action" @click="showTutorial">
            <text class="header-action__mark" aria-hidden="true">?</text>
            <text>使用教程</text>
          </button>
        </view>
      </view>
    </view>

    <view class="input-panel mt-7">
      <view class="mb-3 flex items-center justify-between gap-3">
        <text class="text-sm font-700">分享文案或链接</text>
        <view class="flex shrink-0 items-center gap-2">
          <button v-if="shareText" class="utility-button" @click="clear">
            清空
          </button>
          <button
            class="utility-button utility-button--accent"
            @click="pasteFromClipboard"
          >
            粘贴
          </button>
        </view>
      </view>
      <textarea
        v-model="shareText"
        class="share-field"
        maxlength="2048"
        placeholder="粘贴平台分享文案或 https:// 链接"
        placeholder-class="share-placeholder"
      />
      <button
        class="parse-button mt-4"
        :class="{ 'parse-button--disabled': loading || !shareText.trim() }"
        :disabled="loading || !shareText.trim()"
        :loading="loading"
        @click="submit"
      >
        {{ loading ? "正在解析" : "开始解析" }}
      </button>
    </view>

    <view v-if="loading" class="loading-panel mt-6" aria-label="正在解析">
      <view class="loading-preview" />
      <view class="mt-4 h-5 w-3/4 loading-line" />
      <view class="mt-3 h-4 w-2/5 loading-line" />
    </view>

    <view v-if="error" class="error-panel mt-5">
      <text class="error-mark">!</text>
      <text class="min-w-0 flex-1 text-sm leading-6">{{ error }}</text>
    </view>

    <view v-if="result" class="result-panel mt-7">
      <view class="result-switch" role="tablist">
        <button
          class="result-switch__item"
          :class="{
            'result-switch__item--active': activeResultView === 'media',
          }"
          :aria-selected="activeResultView === 'media'"
          @click="activeResultView = 'media'"
        >
          {{
            result.mediaType === "video"
              ? "视频"
              : `图片 ${result.assets.length}`
          }}
        </button>
        <button
          class="result-switch__item"
          :class="{
            'result-switch__item--active': activeResultView === 'caption',
          }"
          :aria-selected="activeResultView === 'caption'"
          @click="activeResultView = 'caption'"
        >
          文案
        </button>
      </view>

      <view v-if="activeResultView === 'media'" class="result-pane">
        <view v-if="result.mediaType === 'video'" class="video-stage mt-5">
          <video
            v-if="previewAssets[0]"
            class="video-player"
            :src="previewAssets[0].previewUrl"
            :poster="coverUrl"
            controls
            object-fit="contain"
          />
        </view>

        <view v-else class="image-grid mt-5">
          <view
            v-for="(asset, index) in previewAssets"
            :key="asset.previewPath"
            class="image-tile"
            hover-class="image-tile--pressed"
            @click="previewImage(index)"
          >
            <image
              class="result-image"
              :src="asset.previewUrl"
              mode="aspectFill"
            />
            <text class="image-index">{{ index + 1 }}</text>
          </view>
        </view>

        <view v-if="saving" class="save-progress mt-5">
          <view class="mb-2 flex items-center justify-between text-xs">
            <text>{{ saveStatus || "正在准备下载" }}</text>
            <text class="font-mono">{{ downloadProgress }}%</text>
          </view>
          <progress
            :percent="downloadProgress"
            stroke-width="4"
            :active-color="progressColor"
            :background-color="progressBackground"
          />
        </view>
        <text v-else-if="saveStatus" class="save-status mt-4">{{
          saveStatus
        }}</text>

        <view class="primary-actions mt-5">
          <button
            v-if="result.mediaType === 'video' && result.assets[0]"
            class="result-action result-action--primary"
            :disabled="saving"
            @click="downloadAsset(result.assets[0])"
          >
            保存视频
          </button>
          <button
            v-else
            class="result-action result-action--primary"
            :disabled="saving"
            @click="downloadAllImages"
          >
            保存全部图片
          </button>
        </view>

        <button
          v-if="result.assets[0]"
          class="copy-row mt-3"
          @click="copySource(result.assets[0])"
        >
          <text>复制媒体地址</text>
          <text aria-hidden="true">↗</text>
        </button>
      </view>

      <view v-else class="result-pane caption-pane mt-5">
        <view class="caption-heading">
          <text class="font-mono text-xs opacity-45">ORIGINAL CAPTION</text>
          <text class="caption-count">{{ result.title.length }} 字</text>
        </view>
        <text class="caption-text mt-4" selectable user-select>{{
          result.title
        }}</text>
        <button class="caption-copy mt-5" @click="copyCaption">复制文案</button>
      </view>

      <view class="result-footer mt-4">
        <text v-if="copyFeedback" class="copy-feedback">{{
          copyFeedback
        }}</text>
        <view v-else />
        <button class="text-action" @click="submit">重新解析</button>
      </view>
    </view>

    <view class="legal-note mt-10">
      <text class="block text-xs leading-5 opacity-55">
        仅处理公开且你拥有下载权利的内容。本工具不会绕过登录、付费、DRM
        或其他访问控制；使用时请遵守平台条款与著作权规则。
      </text>
    </view>
  </view>
</template>

<style scoped>
.parser-page {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding-bottom: 120rpx;
}

.page-title {
  display: block;
  font-family: "Songti SC", "STSong", serif;
  font-size: 68rpx;
  font-weight: 700;
  line-height: 1.15;
}

.intro-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.intro-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 10rpx;
}

.header-action {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8rpx;
  min-height: 56rpx;
  margin: 0;
  padding: 0 14rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-ink);
  font-size: 23rpx;
  font-weight: 700;
  line-height: 54rpx;
}

.header-action::after {
  border: 0;
}

.header-action__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30rpx;
  height: 30rpx;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-family: monospace;
  font-size: 19rpx;
  line-height: 1;
}

.input-panel {
  padding: 8rpx 0 0;
}

.utility-button {
  min-width: 96rpx;
  min-height: 56rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 8px;
  background: transparent;
  color: var(--color-ink);
  font-size: 24rpx;
  line-height: 54rpx;
}

.utility-button--accent {
  border-color: var(--color-border);
  background: var(--color-ink);
  color: var(--color-page);
}

.share-field {
  width: 100%;
  height: 140rpx;
  padding: 28rpx;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-panel);
  color: var(--color-ink);
  font-size: 28rpx;
  line-height: 1.65;
}

.share-placeholder {
  color: var(--color-placeholder);
}

.parse-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 96rpx;
  border-radius: 8px;
  background: var(--color-ink);
  color: var(--color-page);
  font-size: 30rpx;
  font-weight: 700;
  transition:
    transform 120ms ease-out,
    opacity 120ms ease-out;
}

.parse-button:active {
  transform: translateY(2px);
}

.parse-button--disabled {
  opacity: 0.38;
}

.loading-panel,
.result-panel {
  padding: 32rpx;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  box-shadow: 8rpx 8rpx 0 var(--color-shadow);
}

.loading-preview {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: 6px;
  background: var(--color-fog);
  animation: pulse 1.1s ease-in-out infinite alternate;
}

.loading-line {
  border-radius: 3px;
  background: var(--color-fog);
  animation: pulse 1.1s 120ms ease-in-out infinite alternate;
}

.error-panel {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
  padding: 28rpx;
  border: 1px solid var(--color-border);
  border-left: 10rpx solid var(--color-signal);
  border-radius: 8px;
  background: var(--color-panel);
}

.error-mark {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: var(--color-signal);
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
}

.primary-actions,
.result-footer,
.caption-heading,
.copy-row {
  display: flex;
  align-items: center;
}

.result-footer,
.caption-heading,
.copy-row {
  justify-content: space-between;
}

.result-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  height: 84rpx;
  padding: 6rpx;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-subtle);
}

.result-switch__item {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 68rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: var(--color-ink);
  opacity: 0.58;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1;
}

.result-switch__item::after {
  border: 0;
}

.result-switch__item--active {
  background: var(--color-ink);
  color: var(--color-page);
  opacity: 1;
}

.result-pane {
  animation: pane-in 180ms ease-out both;
}

.video-stage,
.video-player {
  width: 100%;
  height: 450rpx;
}

.video-stage {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #0f100e;
}

.video-player {
  display: block;
  height: 100%;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.image-tile {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-fog);
  transition: opacity 100ms linear;
}

.image-tile--pressed {
  opacity: 0.72;
}

.result-image {
  width: 100%;
  height: 100%;
}

.image-index {
  position: absolute;
  right: 10rpx;
  bottom: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44rpx;
  height: 44rpx;
  border: 1px solid var(--color-page);
  border-radius: 50%;
  background: var(--color-ink);
  color: var(--color-page);
  font-family: monospace;
  font-size: 20rpx;
}

.save-progress,
.save-status {
  padding: 20rpx;
  border-radius: 6px;
  background: var(--color-subtle);
}

.save-status {
  display: block;
  font-size: 24rpx;
}

.primary-actions {
  gap: 16rpx;
}

.result-action {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 88rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  color: var(--color-ink);
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.3;
}

.result-action--primary {
  background: var(--color-ink);
  color: var(--color-page);
}

.copy-row {
  width: 100%;
  min-height: 72rpx;
  margin-right: 0;
  margin-left: 0;
  padding: 0 4rpx;
  border: 0;
  border-radius: 0;
  border-bottom: 1px solid var(--color-soft-border);
  background: transparent;
  color: var(--color-ink);
  font-size: 24rpx;
  line-height: 1;
}

.copy-row::after {
  border: 0;
}

.caption-pane {
  min-height: 320rpx;
  padding: 28rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 8px;
  background: var(--color-panel);
}

.caption-count {
  padding: 6rpx 12rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 999px;
  font-size: 20rpx;
  opacity: 0.58;
}

.caption-text {
  display: block;
  font-family: "Songti SC", "STSong", serif;
  font-size: 34rpx;
  line-height: 1.72;
  word-break: break-word;
}

.caption-copy {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 88rpx;
  margin: 0;
  border-radius: 8px;
  background: var(--color-acid);
  color: #102014;
  font-size: 26rpx;
  font-weight: 800;
}

.copy-feedback {
  color: var(--color-moss);
  font-size: 22rpx;
  font-weight: 700;
}

.text-action {
  min-height: 64rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  background-color: transparent;
  color: var(--color-ink);
  font-size: 24rpx;
  line-height: 64rpx;
  text-decoration: underline;
}

.text-action::after {
  border: 0;
}

.legal-note {
  padding-top: 32rpx;
  border-top: 1px solid var(--color-soft-border);
}

@keyframes pulse {
  from {
    opacity: 0.52;
  }
  to {
    opacity: 1;
  }
}

@keyframes pane-in {
  from {
    opacity: 0;
    transform: translateY(8rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .loading-preview,
  .loading-line {
    animation: none;
  }

  .parse-button {
    transition: none;
  }

  .result-pane {
    animation: none;
  }
}
</style>
