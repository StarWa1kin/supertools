<script setup lang="ts">
import {
  confidenceMeta,
  formatPostDate,
  useCodexWatch,
} from "../composables/useCodexWatch";
import { useTheme } from "../composables/useTheme";

const { themeClass } = useTheme();
const {
  monitoredAccount,
  aiTutorials,
  aiCommunity,
  reminderState,
  subscribing,
  latestPosts,
  loading,
  error,
  configError,
  conclusion,
  dateLabel,
  scanTimeLabel,
  retryConfig,
  openTutorial,
  subscribeResetReminder,
} = useCodexWatch();
</script>

<template>
  <view :class="['watch-page', themeClass]">
    <view class="watch-shell">
      <view :class="['result-poster', `result-poster--${conclusion.kind}`]">
        <view class="poster-grid" />
        <view class="poster-radar-axis" />
        <view class="poster-radar-sweep" />
        <view class="poster-orbit poster-orbit--outer" />
        <view class="poster-orbit poster-orbit--inner" />
        <view class="poster-satellite poster-satellite--left" />
        <view class="poster-satellite poster-satellite--right" />

        <view class="poster-topline">
          <view class="poster-badge">
            <view class="poster-badge-mark">C</view>
            <text>每日监测结果</text>
          </view>
          <view class="live-indicator">
            <view :class="['live-dot', { 'live-dot--scanning': loading }]" />
            <text>{{ loading ? "扫描中" : `更新于 ${scanTimeLabel}` }}</text>
          </view>
        </view>

        <view class="poster-content">
          <text class="poster-question">今天 Codex 重置了吗？</text>
          <text class="poster-answer">{{ loading ? "扫描中" : conclusion.answer }}</text>
          <text class="poster-date">{{ dateLabel }}</text>
          <view class="poster-status">
            <view class="poster-status-mark" />
            <text>{{ loading ? "正在检查公开信息" : conclusion.headline }}</text>
          </view>
          <text class="poster-detail">{{ conclusion.detail }}</text>
        </view>

        <view class="poster-footer">
          <text>MONITOR / @{{ monitoredAccount }}</text>
        </view>
      </view>

      <button
        :class="['subscribe-button', { 'subscribe-button--unavailable': !reminderState.available }]"
        hover-class="subscribe-button--pressed"
        @click="subscribeResetReminder"
      >
        <view class="subscribe-button-icon">订</view>
        <view class="subscribe-button-copy">
          <text class="subscribe-button-title">{{ subscribing ? "正在订阅…" : reminderState.title }}</text>
          <text class="subscribe-button-caption">{{ reminderState.caption }}</text>
        </view>
        <text v-if="reminderState.available" class="subscribe-button-arrow">›</text>
        <text v-else class="subscribe-button-status">未启用</text>
      </button>

      <view v-if="configError" class="config-error">
        <view class="config-error-copy">
          <text class="config-error-title">页面配置加载失败</text>
          <text class="config-error-text">教程和交流群暂时未同步：{{ configError }}</text>
        </view>
        <button class="config-retry" hover-class="config-retry--pressed" @click="retryConfig">
          重试
        </button>
      </view>

      <view class="section-block tweet-section">
        <view class="section-heading">
          <view>
            <text class="section-title">Tibo 最新推文</text>
          </view>
          <text class="section-meta">中文翻译 · 最近 3 条</text>
        </view>

        <view v-if="error" class="empty-state empty-state--error">
          <text class="empty-state-mark">!</text>
          <view>
            <text class="empty-state-title">暂时无法读取推文</text>
            <text class="empty-state-text">{{ error }}</text>
          </view>
        </view>

        <view v-else-if="!loading && latestPosts.length === 0" class="empty-state">
          <text class="empty-state-mark">T</text>
          <view>
            <text class="empty-state-title">等待 Tibo 最新推文</text>
            <text class="empty-state-text">抓取并翻译后，最近三条会显示在这里。</text>
          </view>
        </view>

        <view v-else class="tweet-list">
          <view v-for="(post, index) in latestPosts" :key="post.id" class="tweet-card">
            <view class="tweet-card-body">
              <view class="tweet-meta-row">
                <text class="tweet-number">{{ String(index + 1).padStart(2, "0") }}</text>
                <text class="tweet-time">{{ formatPostDate(post.publishedAt) }}</text>
              </view>

              <view class="translation-label-row">
                <text class="translation-label">
                  {{ post.translatedText ? "中文译文" : "原文待翻译" }}
                </text>
                <text v-if="post.isReply" class="reply-label">回复</text>
                <text :class="['confidence-label', confidenceMeta[post.confidence].className]">
                  {{ confidenceMeta[post.confidence].label }}
                </text>
              </view>

              <text class="tweet-translation">{{ post.translatedText || post.text }}</text>

            </view>
          </view>
        </view>
      </view>

      <view v-if="aiTutorials.length" class="section-block tutorial-section">
        <view class="section-heading">
          <view>
            <text class="section-title">更多 AI 教程</text>
          </view>
          <text class="section-meta">公众号精选</text>
        </view>

        <view class="tutorial-list">
          <button
            v-for="(tutorial, index) in aiTutorials"
            :key="tutorial.id"
            class="tutorial-row"
            hover-class="tutorial-row--pressed"
            @click="openTutorial(tutorial.url)"
          >
            <text class="tutorial-number">{{
              String(index + 1).padStart(2, "0")
            }}</text>
            <view class="tutorial-copy">
              <text class="tutorial-title">{{ tutorial.title }}</text>
              <text class="tutorial-description">{{ tutorial.description }}</text>
            </view>
            <text class="tutorial-action">↗</text>
          </button>
        </view>
      </view>

      <view v-if="aiCommunity" class="section-block community-section">
        <view class="section-heading">
          <view>
            <text class="section-title">{{ aiCommunity.title }}</text>
          </view>
          <text class="section-meta">扫码加入</text>
        </view>

        <view class="community-panel">
          <view class="community-copy">
            <text class="community-eyebrow">SUPERTOOLS COMMUNITY</text>
            <text class="community-title">一起交流 AI 实战</text>
            <text class="community-description">{{ aiCommunity.description }}</text>
            <view class="community-tags">
              <text>Codex</text>
              <text>AI 编程</text>
              <text>自动化</text>
            </view>
          </view>

          <view class="qr-frame">
            <image
              class="qr-image"
              :src="aiCommunity.qrCode"
              mode="aspectFill"
              show-menu-by-longpress
            />
          </view>
        </view>

        <text class="community-note">二维码上传后，可长按识别加入交流群。</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.watch-page {
  min-height: 100vh;
  overflow-x: hidden;
  background: var(--color-page);
  color: var(--color-ink);
}

.watch-shell {
  width: 100%;
  max-width: 860rpx;
  min-width: 0;
  margin: 0 auto;
  padding: 48rpx 32rpx 110rpx;
}

.poster-topline,
.poster-footer,
.section-heading,
.tweet-meta-row,
.translation-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.poster-question,
.poster-answer,
.poster-date,
.poster-detail,
.section-title,
.section-meta,
.empty-state-title,
.empty-state-text,
.tweet-number,
.tweet-time,
.tweet-translation,
.tutorial-number,
.tutorial-title,
.tutorial-description {
  display: block;
}

.live-indicator {
  display: flex;
  flex: none;
  align-items: center;
  gap: 12rpx;
  min-height: 50rpx;
  padding: 0 16rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 25rpx;
  background: var(--color-panel);
  font-size: 19rpx;
  font-weight: 700;
}

.live-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: var(--color-moss);
}

.live-dot--scanning {
  animation: live-pulse 1s ease-in-out infinite;
}

.result-poster {
  position: relative;
  min-height: 810rpx;
  overflow: hidden;
  padding: 34rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 16rpx;
  background: var(--color-surface);
  box-shadow: 0 30rpx 70rpx var(--color-shadow-soft);
  --poster-accent: #2563eb;
  --poster-soft: #dbeafe;
}

.result-poster--signal {
  --poster-accent: #b96800;
  --poster-soft: #f8e8b8;
}

.result-poster--confirmed {
  --poster-accent: #07825d;
  --poster-soft: #cceee1;
}

.result-poster--offline {
  --poster-accent: #d94a3f;
  --poster-soft: #f5d5d2;
}

.poster-grid {
  position: absolute;
  inset: 0;
  opacity: 0.25;
  background-image:
    linear-gradient(rgba(37, 99, 235, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.07) 1px, transparent 1px);
  background-size: 64rpx 64rpx;
}

.poster-radar-axis,
.poster-radar-sweep {
  position: absolute;
  left: 50%;
  top: 49%;
  width: 650rpx;
  height: 650rpx;
  border-radius: 50%;
  pointer-events: none;
}

.poster-radar-axis {
  opacity: 0.28;
  background:
    linear-gradient(transparent calc(50% - 1px), rgba(37, 99, 235, 0.16) 50%, transparent calc(50% + 1px)),
    linear-gradient(90deg, transparent calc(50% - 1px), rgba(37, 99, 235, 0.16) 50%, transparent calc(50% + 1px));
  transform: translate(-50%, -50%);
}

.poster-radar-sweep {
  z-index: 1;
  opacity: 0.26;
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    transparent 306deg,
    var(--poster-soft) 346deg,
    var(--poster-accent) 360deg
  );
  transform: translate(-50%, -50%) rotate(0deg);
  animation: radar-scan 6s linear infinite;
  will-change: transform;
}

.poster-orbit {
  position: absolute;
  left: 50%;
  top: 49%;
  border: 1px solid rgba(37, 99, 235, 0.13);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.poster-orbit--outer {
  width: 650rpx;
  height: 650rpx;
}

.poster-orbit--inner {
  width: 430rpx;
  height: 430rpx;
  box-shadow: 0 0 110rpx rgba(37, 99, 235, 0.13);
}

.poster-satellite {
  position: absolute;
  z-index: 1;
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: var(--poster-accent);
  box-shadow: 0 0 30rpx var(--poster-soft);
  animation: radar-blip 3s ease-in-out infinite;
}

.poster-satellite--left {
  left: 68rpx;
  top: 43%;
}

.poster-satellite--right {
  right: 78rpx;
  top: 64%;
  width: 30rpx;
  height: 30rpx;
  animation-delay: -1.5s;
}

.poster-topline,
.poster-content,
.poster-footer {
  position: relative;
  z-index: 2;
}

.poster-badge {
  display: flex;
  align-items: center;
  gap: 14rpx;
  min-height: 58rpx;
  padding: 0 20rpx 0 10rpx;
  border-radius: 29rpx;
  background: var(--poster-soft);
  color: var(--poster-accent);
  font-size: 23rpx;
  font-weight: 800;
}

.poster-badge-mark {
  display: flex;
  width: 42rpx;
  height: 42rpx;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--poster-accent);
  color: #ffffff;
  font-family: Georgia, serif;
  font-size: 24rpx;
  font-weight: 800;
}

.poster-footer {
  font-family: "Courier New", monospace;
  font-size: 18rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  opacity: 0.38;
}

.poster-content {
  display: flex;
  min-height: 626rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 46rpx 0 28rpx;
  text-align: center;
}

.poster-question {
  max-width: 590rpx;
  font-family: "Songti SC", "STSong", serif;
  font-size: 49rpx;
  font-weight: 800;
  line-height: 1.25;
}

.poster-answer {
  margin-top: 74rpx;
  color: var(--poster-accent);
  font-family: "Songti SC", "STSong", serif;
  font-size: 164rpx;
  font-weight: 900;
  line-height: 0.95;
  text-shadow: 0 16rpx 44rpx var(--poster-soft);
}

.poster-date {
  margin-top: 48rpx;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 54rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
}

.poster-status {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 30rpx;
  font-size: 25rpx;
  font-weight: 800;
  opacity: 0.7;
}

.poster-status-mark {
  width: 18rpx;
  height: 18rpx;
  border: 5rpx solid var(--poster-accent);
  border-radius: 50%;
  opacity: 0.55;
}

.poster-detail {
  max-width: 560rpx;
  margin-top: 22rpx;
  font-size: 22rpx;
  line-height: 1.75;
  opacity: 0.48;
}

.subscribe-button {
  display: flex;
  width: 100%;
  min-height: 112rpx;
  align-items: center;
  gap: 18rpx;
  margin-top: 30rpx;
  padding: 0 32rpx;
  border-radius: 12rpx;
  background: var(--color-ink);
  color: var(--color-page);
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1;
  transition: transform 120ms ease, opacity 120ms ease;
}


.subscribe-button--pressed {
  opacity: 0.84;
  transform: scale(0.985);
}

.subscribe-button--unavailable {
  background: var(--color-panel);
  color: var(--color-ink);
  box-shadow: inset 0 0 0 1px var(--color-soft-border);
}

.subscribe-button-icon {
  display: flex;
  width: 48rpx;
  height: 48rpx;
  flex: none;
  align-items: center;
  justify-content: center;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-family: Georgia, serif;
  font-size: 30rpx;
  font-weight: 800;
}

.subscribe-button-copy {
  min-width: 0;
  flex: 1;
  text-align: left;
}

.subscribe-button-title,
.subscribe-button-caption {
  display: block;
}

.subscribe-button-title {
  font-size: 29rpx;
  font-weight: 800;
}

.subscribe-button-caption {
  margin-top: 8rpx;
  font-size: 19rpx;
  font-weight: 500;
  opacity: 0.58;
}

.subscribe-button-arrow {
  margin-left: auto;
  font-size: 48rpx;
  font-weight: 300;
  opacity: 0.65;
}

.subscribe-button-status {
  flex: none;
  padding: 8rpx 12rpx;
  border: 1px solid currentColor;
  border-radius: 6rpx;
  font-size: 18rpx;
  font-weight: 800;
  opacity: 0.45;
}

.section-block {
  margin-top: 70rpx;
}

.config-error {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 20rpx;
  padding: 22rpx 24rpx;
  border: 1px solid var(--color-signal);
  border-radius: 10rpx;
  background: rgba(255, 90, 54, 0.08);
}

.config-error-copy {
  min-width: 0;
  flex: 1;
}

.config-error-title,
.config-error-text {
  display: block;
}

.config-error-title {
  font-size: 23rpx;
  font-weight: 800;
}

.config-error-text {
  margin-top: 6rpx;
  overflow: hidden;
  font-size: 19rpx;
  line-height: 1.5;
  opacity: 0.58;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-retry {
  min-width: 86rpx;
  min-height: 58rpx;
  flex: none;
  margin: 0;
  padding: 0 18rpx;
  border: 1px solid var(--color-ink);
  border-radius: 6rpx;
  background: transparent;
  color: var(--color-ink);
  font-size: 20rpx;
  font-weight: 800;
  line-height: 58rpx;
}

.config-retry--pressed {
  opacity: 0.55;
}

.section-heading {
  gap: 24rpx;
  margin-bottom: 26rpx;
  padding-bottom: 20rpx;
  border-bottom: 1px solid var(--color-soft-border);
}

.section-heading > view:first-child {
  display: flex;
  align-items: baseline;
  gap: 16rpx;
}

.section-title {
  font-family: "Songti SC", "STSong", serif;
  font-size: 38rpx;
  font-weight: 800;
}

.section-meta {
  flex: none;
  font-size: 19rpx;
  opacity: 0.4;
}

.empty-state {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 34rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 10rpx;
  background: var(--color-panel);
}

.empty-state--error {
  border-color: var(--color-signal);
}

.empty-state-mark {
  display: flex;
  width: 72rpx;
  height: 72rpx;
  flex: none;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-ink);
  border-radius: 50%;
  font-family: Georgia, serif;
  font-size: 31rpx;
  font-weight: 800;
}

.empty-state-title {
  font-size: 25rpx;
  font-weight: 800;
}

.empty-state-text {
  margin-top: 8rpx;
  font-size: 21rpx;
  line-height: 1.6;
  opacity: 0.52;
}

.tweet-list {
  display: flex;
  width: 100%;
  min-width: 0;
  flex-direction: column;
  gap: 20rpx;
}

.tweet-card {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  padding: 28rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 10rpx;
  background: var(--color-panel);
}

.tweet-number {
  font-family: "Courier New", monospace;
  font-size: 19rpx;
  font-weight: 800;
  opacity: 0.4;
}

.tweet-card-body {
  width: 100%;
  min-width: 0;
}

.tweet-meta-row {
  gap: 18rpx;
}

.tweet-time {
  font-size: 18rpx;
  opacity: 0.4;
}

.tweet-time {
  flex: none;
}

.translation-label-row {
  gap: 12rpx;
  margin-top: 24rpx;
}

.translation-label,
.confidence-label,
.reply-label {
  display: inline-flex;
  min-height: 38rpx;
  align-items: center;
  border-radius: 6rpx;
  font-size: 18rpx;
  font-weight: 800;
}

.reply-label {
  padding: 0 10rpx;
  border: 1px solid var(--color-soft-border);
  color: var(--color-ink);
  opacity: 0.52;
}

.translation-label {
  padding: 0 12rpx;
  background: var(--color-ink);
  color: var(--color-page);
}

.confidence-label {
  padding: 0 10rpx;
}

.confidence-official {
  background: #d1fae5;
  color: #076247;
}

.confidence-third-party {
  background: #f8e8b8;
  color: #8d4d00;
}

.confidence-inferred {
  background: var(--color-subtle);
  color: var(--color-ink);
}

.tweet-translation {
  width: 100%;
  max-width: 100%;
  margin-top: 18rpx;
  overflow-wrap: anywhere;
  word-break: break-all;
  white-space: normal;
  font-family: "Songti SC", "STSong", serif;
  font-size: 27rpx;
  font-weight: 600;
  line-height: 1.75;
}

.tutorial-row--pressed {
  opacity: 0.55;
}

.tutorial-list {
  border-top: 1px solid var(--color-ink);
}

.tutorial-row {
  display: grid;
  width: 100%;
  min-height: 150rpx;
  grid-template-columns: 72rpx minmax(0, 1fr) auto;
  align-items: center;
  gap: 22rpx;
  padding: 24rpx 4rpx;
  border-bottom: 1px solid var(--color-soft-border);
  border-radius: 0;
  background: transparent;
  color: var(--color-ink);
  text-align: left;
  transition: opacity 100ms ease;
}

.tutorial-row--pending {
  opacity: 0.68;
}

.tutorial-number {
  font-family: Georgia, serif;
  font-size: 42rpx;
  font-weight: 800;
  text-align: center;
}

.tutorial-copy {
  min-width: 0;
}

.tutorial-title {
  font-family: "Songti SC", "STSong", serif;
  font-size: 27rpx;
  font-weight: 800;
  line-height: 1.35;
}

.tutorial-description {
  margin-top: 9rpx;
  font-size: 20rpx;
  line-height: 1.5;
  opacity: 0.48;
}

.tutorial-action {
  min-width: 64rpx;
  font-size: 20rpx;
  font-weight: 800;
  text-align: right;
  opacity: 0.42;
}

.community-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 230rpx;
  gap: 28rpx;
  align-items: center;
  padding: 34rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 10rpx;
  background: var(--color-ink);
  color: var(--color-page);
}

.community-copy {
  min-width: 0;
}

.community-eyebrow,
.community-title,
.community-description,
.community-note {
  display: block;
}

.community-eyebrow {
  font-family: "Courier New", monospace;
  font-size: 17rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
  opacity: 0.42;
}

.community-title {
  margin-top: 18rpx;
  font-family: "Songti SC", "STSong", serif;
  font-size: 38rpx;
  font-weight: 800;
  line-height: 1.25;
}

.community-description {
  margin-top: 14rpx;
  font-size: 21rpx;
  line-height: 1.65;
  opacity: 0.58;
}

.community-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 24rpx;
}

.community-tags text {
  display: inline-flex;
  min-height: 36rpx;
  align-items: center;
  padding: 0 11rpx;
  border: 1px solid currentColor;
  border-radius: 5rpx;
  font-size: 17rpx;
  font-weight: 700;
  opacity: 0.58;
}

.qr-frame {
  width: 230rpx;
  aspect-ratio: 1;
  padding: 12rpx;
  border-radius: 8rpx;
  background: var(--color-page);
}

.qr-image,
.qr-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 4rpx;
}

.qr-placeholder {
  position: relative;
  display: flex;
  overflow: hidden;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--color-subtle);
  color: var(--color-ink);
}

.qr-placeholder-grid {
  position: absolute;
  inset: 0;
  opacity: 0.45;
  background-image:
    linear-gradient(rgba(23, 25, 21, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23, 25, 21, 0.12) 1px, transparent 1px);
  background-size: 28rpx 28rpx;
}

.qr-placeholder-mark,
.qr-placeholder-text {
  position: relative;
  z-index: 1;
}

.qr-placeholder-mark {
  font-family: Georgia, serif;
  font-size: 64rpx;
  font-weight: 400;
  line-height: 1;
  opacity: 0.35;
}

.qr-placeholder-text {
  margin-top: 10rpx;
  font-size: 19rpx;
  font-weight: 800;
  opacity: 0.48;
}

.community-note {
  margin-top: 16rpx;
  font-size: 19rpx;
  text-align: center;
  opacity: 0.4;
}

@keyframes live-pulse {
  0%, 100% { opacity: 0.45; transform: scale(0.78); }
  50% { opacity: 1; transform: scale(1); }
}

@keyframes radar-scan {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

@keyframes radar-blip {
  0%, 100% { opacity: 0.42; transform: scale(0.82); }
  50% { opacity: 1; transform: scale(1); }
}

@media (min-width: 768px) {
  .watch-shell {
    padding-top: 64rpx;
  }

  .result-poster {
    min-height: 738rpx;
  }

  .poster-content {
    min-height: 554rpx;
  }
}

@media (prefers-reduced-motion: reduce) {
  .live-dot--scanning,
  .poster-radar-sweep,
  .poster-satellite {
    animation: none;
  }

  .poster-radar-sweep {
    opacity: 0.14;
    transform: translate(-50%, -50%) rotate(35deg);
  }

  .subscribe-button,
  .tutorial-row {
    transition: none;
  }
}
</style>
