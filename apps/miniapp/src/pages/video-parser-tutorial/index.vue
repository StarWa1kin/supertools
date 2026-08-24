<script setup lang="ts">
import { useTheme } from "../../composables/useTheme";

const { themeClass } = useTheme();

const steps = [
  {
    number: "01",
    title: "打开作品分享菜单",
    description: "在短视频平台找到要解析的公开作品，点击右下角「更多」或「分享」。",
    image: "/static/tutorials/video-parser/step-1-more.jpg",
    alt: "短视频作品页，箭头指向右下角更多按钮",
  },
  {
    number: "02",
    title: "复制作品链接",
    description: "在分享面板中找到「复制链接」。平台复制出的整段分享文案也可以直接使用。",
    image: "/static/tutorials/video-parser/step-2-copy-link.jpg",
    alt: "分享面板，箭头指向复制链接按钮",
  },
  {
    number: "03",
    title: "粘贴并开始解析",
    description: "返回视频解析页，点击「粘贴」，再点击「开始解析」。解析完成后即可预览和保存。",
    image: "/static/tutorials/video-parser/step-3-paste.jpg",
    alt: "视频解析页，箭头指向粘贴按钮",
  },
];

function startParsing() {
  uni.navigateBack();
}
</script>

<template>
  <view :class="['page-shell tutorial-page', themeClass]">
    <view class="tutorial-hero">
      <text class="tutorial-kicker">3 STEPS · ABOUT 10 SECONDS</text>
      <text class="tutorial-title">如何解析视频</text>
      <text class="tutorial-lead">
        复制公开作品链接，粘贴到工具中，即可解析视频或图片。
      </text>
    </view>

    <view class="steps-list">
      <view v-for="step in steps" :key="step.number" class="step-card">
        <view class="step-copy">
          <text class="step-number">{{ step.number }}</text>
          <view class="step-text">
            <text class="step-title">{{ step.title }}</text>
            <text class="step-description">{{ step.description }}</text>
          </view>
        </view>

        <view class="screenshot-shell">
          <image
            class="step-image"
            :src="step.image"
            mode="aspectFit"
            :aria-label="step.alt"
          />
        </view>
      </view>
    </view>

    <view class="tutorial-tip">
      <text class="tip-mark">i</text>
      <text class="tip-copy">
        找不到复制链接？请先确认作品为公开内容。不同平台的分享入口名称和位置可能略有差异。
      </text>
    </view>

    <button class="start-button" @click="startParsing">我知道了，开始解析</button>

    <text class="legal-copy">
      请仅解析你有权下载的公开内容，并遵守平台条款与著作权规则。
    </text>
  </view>
</template>

<style scoped>
.tutorial-page {
  box-sizing: border-box;
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding-top: 64rpx;
  padding-bottom: calc(80rpx + env(safe-area-inset-bottom));
}

.tutorial-hero {
  padding-bottom: 44rpx;
  border-bottom: 1px solid var(--color-border);
}

.tutorial-kicker {
  display: block;
  color: var(--color-moss);
  font-family: monospace;
  font-size: 21rpx;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.tutorial-title {
  display: block;
  margin-top: 16rpx;
  font-family: "Songti SC", "STSong", serif;
  font-size: 60rpx;
  font-weight: 700;
  line-height: 1.18;
}

.tutorial-lead {
  display: block;
  max-width: 580rpx;
  margin-top: 20rpx;
  font-size: 28rpx;
  line-height: 1.75;
  opacity: 0.68;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
  padding: 40rpx 0;
}

.step-card {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  box-shadow: 8rpx 8rpx 0 var(--color-shadow);
}

.step-copy {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
  padding: 30rpx;
}

.step-number {
  flex: 0 0 auto;
  color: var(--color-signal);
  font-family: monospace;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1.4;
}

.step-text {
  min-width: 0;
}

.step-title,
.step-description {
  display: block;
}

.step-title {
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.35;
}

.step-description {
  margin-top: 10rpx;
  font-size: 25rpx;
  line-height: 1.65;
  opacity: 0.64;
}

.screenshot-shell {
  display: flex;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
  padding: 28rpx 0;
  border-top: 1px solid var(--color-soft-border);
  background: #111512;
}

.step-image {
  display: block;
  width: 500rpx;
  height: 1088rpx;
  border-radius: 6px;
}

.tutorial-tip {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  padding: 26rpx;
  border-left: 8rpx solid var(--color-moss);
  background: var(--color-subtle);
}

.tip-mark {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 36rpx;
  height: 36rpx;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-family: serif;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1;
}

.tip-copy {
  min-width: 0;
  font-size: 24rpx;
  line-height: 1.65;
}

.start-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 96rpx;
  margin: 40rpx 0 0;
  border-radius: 8px;
  background: var(--color-ink);
  color: var(--color-page);
  font-size: 29rpx;
  font-weight: 800;
}

.start-button::after {
  border: 0;
}

.legal-copy {
  display: block;
  padding: 24rpx 20rpx 0;
  font-size: 21rpx;
  line-height: 1.6;
  text-align: center;
  opacity: 0.48;
}
</style>
