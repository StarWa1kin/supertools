<script setup lang="ts">
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import { useTheme } from "../../composables/useTheme";
import {
  clearVideoParserHistory,
  getVideoParserHistory,
  removeVideoParserHistory,
  setVideoParserPrefill,
  type VideoParserHistoryItem,
} from "../../composables/videoParserHistory";

const { themeClass } = useTheme();
const records = ref<VideoParserHistoryItem[]>([]);

const statusNames = {
  pending: "解析中",
  success: "解析成功",
  failed: "解析失败",
} as const;

function refresh() {
  records.value = getVideoParserHistory();
}

function formatTime(timestamp: number) {
  const date = new Date(timestamp);
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}.${pad(date.getMonth() + 1)}.${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function removeRecord(id: string) {
  removeVideoParserHistory(id);
  refresh();
}

async function clearRecords() {
  const modal = await uni.showModal({
    title: "清空解析记录？",
    content: "本地保存的全部解析记录将被删除，且无法恢复。",
    confirmText: "清空",
    confirmColor: "#ff5a36",
  });
  if (!modal.confirm) return;
  clearVideoParserHistory();
  refresh();
}

function parseAgain(record: VideoParserHistoryItem) {
  setVideoParserPrefill(record.input || record.url);
  uni.navigateBack();
}

function goToParser() {
  uni.navigateBack();
}

onShow(refresh);
</script>

<template>
  <view :class="['page-shell history-page pt-8', themeClass]">
    <view class="history-heading">
      <view>
        <text class="history-title">解析记录</text>
        <text class="mt-2 block text-xs opacity-55">仅保存在当前设备</text>
      </view>
      <button v-if="records.length" class="clear-action" @click="clearRecords">
        清空
      </button>
    </view>

    <view class="history-summary mt-7">
      <view>
        <text class="history-summary__count">{{ records.length }}</text>
        <text class="ml-2 text-sm opacity-65">条本地记录</text>
      </view>
      <text class="text-xs opacity-45">最多保留最近 50 条</text>
    </view>

    <view v-if="records.length" class="record-list mt-5">
      <view v-for="record in records" :key="record.id" class="record-card">
        <view class="record-head">
          <text :class="['status-chip', `status-chip--${record.status}`]">
            {{ statusNames[record.status] }}
          </text>
        </view>
        <text class="record-time mt-3">{{ formatTime(record.createdAt) }}</text>
        <view class="record-source mt-4">
          <text class="record-source__label">LINK</text>
          <text class="record-url">{{ record.url }}</text>
        </view>
        <text class="record-content mt-4">
          {{ record.title || record.error || record.input }}
        </text>
        <view class="record-actions mt-5">
          <button class="record-button" @click="removeRecord(record.id)">
            删除
          </button>
          <button class="record-button record-button--primary" @click="parseAgain(record)">
            重新解析
          </button>
        </view>
      </view>
    </view>

    <view v-else class="empty-state mt-10">
      <text class="empty-state__mark">0</text>
      <text class="mt-5 block text-lg font-700">暂无解析记录</text>
      <text class="mt-2 block text-sm leading-6 opacity-55">
        粘贴受支持的公开链接并点击解析后，记录会保存在这里。
      </text>
      <button class="empty-state__action mt-6" @click="goToParser">
        返回视频解析
      </button>
    </view>
  </view>
</template>

<style scoped>
.history-page {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding-bottom: 120rpx;
  overflow-x: hidden;
}

.history-heading,
.history-summary,
.record-head,
.record-source,
.record-actions {
  display: flex;
  align-items: center;
}

.history-heading,
.history-summary {
  justify-content: space-between;
}

.history-summary {
  width: 100%;
  min-width: 0;
  min-height: 104rpx;
  padding: 20rpx 24rpx;
  border: 1px solid var(--color-soft-border, rgba(23, 25, 21, 0.28));
  border-radius: 9px;
  background: var(--color-subtle, #e7e3d8);
}

.history-summary__count {
  font-family: monospace;
  font-size: 42rpx;
  font-weight: 700;
}

.history-title {
  display: block;
  font-family: "Songti SC", "STSong", serif;
  font-size: 56rpx;
  font-weight: 700;
  line-height: 1.2;
}

.clear-action,
.record-button {
  margin: 0;
  border: 1px solid var(--color-soft-border);
  background: transparent;
  color: var(--color-ink);
}

.clear-action {
  min-height: 60rpx;
  padding: 0 22rpx;
  border-radius: 999px;
  font-size: 24rpx;
  line-height: 58rpx;
}

.clear-action::after,
.record-button::after {
  border: 0;
}

.record-list {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  width: 100%;
  min-width: 0;
  gap: 24rpx;
}

.record-card {
  width: 100%;
  min-width: 0;
  overflow: hidden;
  padding: 28rpx;
  border: 1px solid var(--color-soft-border);
  border-radius: 10px;
  background: var(--color-panel);
}

.record-head {
  width: 100%;
  min-width: 0;
  justify-content: flex-end;
  gap: 16rpx;
}

.record-time {
  display: block;
  color: var(--color-ink);
  font-family: monospace;
  font-size: 21rpx;
  opacity: 0.48;
}

.status-chip {
  flex: 0 0 auto;
  padding: 7rpx 14rpx;
  border-radius: 999px;
  font-size: 21rpx;
  font-weight: 700;
  line-height: 1.25;
  white-space: nowrap;
}

.status-chip {
  font-family: inherit;
}

.status-chip--success {
  background: var(--color-moss);
  color: var(--color-page);
}

.status-chip--failed {
  background: var(--color-signal);
  color: #fff;
}

.status-chip--pending {
  background: var(--color-subtle);
}

.record-source {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  gap: 12rpx;
  padding: 16rpx 18rpx;
  border-radius: 6px;
  background: var(--color-subtle);
}

.record-source__label {
  flex: 0 0 auto;
  font-family: monospace;
  font-size: 19rpx;
  font-weight: 700;
  opacity: 0.46;
}

.record-url {
  display: block;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  opacity: 0.48;
  font-family: monospace;
  font-size: 20rpx;
  font-weight: 400;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-content {
  width: 100%;
  max-width: 100%;
  display: -webkit-box;
  overflow: hidden;
  font-size: 29rpx;
  line-height: 1.65;
  overflow-wrap: anywhere;
  word-break: break-all;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.record-actions {
  display: grid;
  grid-template-columns: 132rpx minmax(0, 1fr);
  width: 100%;
  min-width: 0;
  gap: 14rpx;
}

.record-button {
  width: 100%;
  min-width: 0;
  min-height: 72rpx;
  border-radius: 7px;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 70rpx;
}

.record-button--primary {
  border-color: var(--color-ink);
  background: var(--color-ink);
  color: var(--color-page);
}

.empty-state {
  padding: 80rpx 44rpx;
  border: 1px dashed var(--color-soft-border);
  border-radius: 12px;
  text-align: center;
}

.empty-state__action {
  min-height: 76rpx;
  margin-right: auto;
  margin-left: auto;
  padding: 0 30rpx;
  border: 0;
  border-radius: 8px;
  background: var(--color-ink, #171915);
  color: var(--color-page, #f4f1e8);
  font-size: 25rpx;
  font-weight: 700;
  line-height: 76rpx;
}

.empty-state__action::after {
  border: 0;
}

.empty-state__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: var(--color-subtle);
  font-family: monospace;
  font-size: 34rpx;
}
</style>
