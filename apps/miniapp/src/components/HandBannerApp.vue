<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import { useHandBanner } from "../composables/handBanner";

const {
  message,
  textColor,
  fontScale,
  colors,
  sizes,
  maxLength,
  remaining,
  restore,
  save,
} = useHandBanner();

function startPlaying() {
  save();
  uni.navigateTo({ url: "/pages/hand-banner/player" });
}

function clearMessage() {
  message.value = "";
  save();
}

onShow(restore);
</script>

<template>
  <view class="banner-editor">
    <view class="banner-editor__glow banner-editor__glow--one" />
    <view class="banner-editor__glow banner-editor__glow--two" />

    <view class="banner-editor__content">
      <text class="banner-editor__eyebrow">LIVE MESSAGE BOARD</text>
      <text class="banner-editor__title">手持弹幕</text>
      <text class="banner-editor__subtitle">写一句话，举起手机，让它横屏不停流动。</text>

      <view class="editor-card">
        <view class="editor-card__heading">
          <text>弹幕内容</text>
          <view class="editor-card__actions">
            <button
              v-if="message"
              class="editor-card__clear"
              aria-label="清空弹幕内容"
              hover-class="editor-card__clear--pressed"
              @click="clearMessage"
            >
              清空
            </button>
            <text class="editor-card__count">还可输入 {{ remaining }} 字</text>
          </view>
        </view>
        <textarea
          v-model="message"
          class="editor-card__input"
          :maxlength="maxLength"
          auto-height
          placeholder="例如：祝你今天一切顺利！"
          placeholder-class="editor-card__placeholder"
          @blur="save()"
        />
      </view>

      <view class="setting-card">
        <view class="setting-card__row">
          <text class="setting-card__label">文字颜色</text>
          <view class="color-options">
            <button
              v-for="color in colors"
              :key="color"
              :class="['color-dot', { 'color-dot--selected': textColor === color }]"
              :style="{ backgroundColor: color }"
              :aria-label="`选择颜色 ${color}`"
              @click="textColor = color; save()"
            />
          </view>
        </view>
        <view class="setting-card__divider" />
        <view class="setting-card__row">
          <text class="setting-card__label">文字大小</text>
          <view class="size-options">
            <button
              v-for="size in sizes"
              :key="size.value"
              :class="['size-option', { 'size-option--selected': fontScale === size.value }]"
              @click="fontScale = size.value; save()"
            >
              {{ size.label }}
            </button>
          </view>
        </view>
      </view>

      <view class="preview-card" aria-label="弹幕预览">
        <view class="preview-card__topline">
          <view class="live-dot" />
          <text>PREVIEW</text>
        </view>
        <view class="preview-card__window">
          <view class="preview-card__track">
            <text class="preview-card__text" :style="{ color: textColor, fontSize: `${58 * fontScale}rpx` }">{{ message || "写下你的弹幕" }}</text>
            <text class="preview-card__text" :style="{ color: textColor, fontSize: `${58 * fontScale}rpx` }" aria-hidden="true">{{ message || "写下你的弹幕" }}</text>
          </view>
        </view>
      </view>

      <button class="start-button" @click="startPlaying">
        <text class="start-button__play">▶</text>
        横屏开始播放
      </button>
      <text class="banner-editor__tip">播放页横屏显示；轻触屏幕可显示返回按钮。</text>
    </view>
  </view>
</template>

<style scoped>
.banner-editor { position: relative; min-height: 100vh; overflow: hidden; background: #08090b; color: #f8f7ed; }
.banner-editor__content { position: relative; z-index: 1; width: 100%; max-width: 720px; margin: 0 auto; padding: 76rpx 36rpx 112rpx; }
.banner-editor__glow { position: absolute; border-radius: 50%; filter: blur(3px); opacity: .42; }
.banner-editor__glow--one { top: -210rpx; right: -140rpx; width: 490rpx; height: 490rpx; background: #155bff; }
.banner-editor__glow--two { bottom: 80rpx; left: -250rpx; width: 490rpx; height: 490rpx; background: #d61f77; opacity: .24; }
.banner-editor__eyebrow { display: block; color: #89ff3c; font-family: monospace; font-size: 20rpx; font-weight: 800; letter-spacing: .18em; }
.banner-editor__title { display: block; margin-top: 18rpx; font-size: 78rpx; font-weight: 900; letter-spacing: .06em; line-height: 1; }
.banner-editor__subtitle { display: block; width: 500rpx; margin-top: 22rpx; color: rgba(248,247,237,.67); font-size: 28rpx; line-height: 1.65; }
.editor-card, .preview-card { margin-top: 56rpx; border: 1px solid rgba(255,255,255,.18); border-radius: 28rpx; background: rgba(20,22,27,.82); box-shadow: 0 24rpx 60rpx rgba(0,0,0,.24); }
.editor-card { padding: 30rpx; }
.editor-card__heading, .preview-card__topline { display: flex; align-items: center; justify-content: space-between; }
.editor-card__heading { font-size: 27rpx; font-weight: 750; }
.editor-card__actions { display: flex; align-items: center; gap: 14rpx; }
.editor-card__clear { min-width: 72rpx; height: 44rpx; margin: 0; padding: 0 14rpx; border: 1px solid rgba(255,255,255,.16); border-radius: 999px; background: rgba(255,255,255,.06); color: rgba(248,247,237,.72); font-size: 20rpx; font-weight: 650; line-height: 42rpx; }
.editor-card__clear::after { border: 0; }
.editor-card__clear--pressed { border-color: rgba(137,255,60,.42); background: rgba(137,255,60,.12); color: #89ff3c; }
.editor-card__count { color: rgba(248,247,237,.48); font-family: monospace; font-size: 20rpx; font-weight: 400; }
.editor-card__input { box-sizing: border-box; width: 100%; min-height: 160rpx; margin-top: 24rpx; padding: 22rpx 0 8rpx; border-top: 1px solid rgba(255,255,255,.1); color: #fff; font-size: 39rpx; font-weight: 700; line-height: 1.35; }
.editor-card__placeholder { color: rgba(248,247,237,.27); }
.setting-card { margin-top: 24rpx; padding: 0 30rpx; border: 1px solid rgba(255,255,255,.14); border-radius: 24rpx; background: rgba(20,22,27,.72); }
.setting-card__row { display: flex; min-height: 106rpx; align-items: center; justify-content: space-between; gap: 20rpx; }
.setting-card__label { flex: none; font-size: 27rpx; font-weight: 750; }
.setting-card__divider { height: 1px; background: rgba(255,255,255,.1); }
.color-options, .size-options { display: flex; align-items: center; gap: 14rpx; }
.color-dot { width: 38rpx; height: 38rpx; margin: 0; padding: 0; border: 3rpx solid transparent; border-radius: 50%; box-shadow: inset 0 0 0 1px rgba(0,0,0,.28); }
.color-dot::after, .size-option::after { border: 0; }
.color-dot--selected { border-color: #fff; box-shadow: 0 0 0 4rpx rgba(137,255,60,.42); }
.size-option { min-width: 58rpx; height: 52rpx; margin: 0; padding: 0 12rpx; border: 1px solid rgba(255,255,255,.16); border-radius: 12rpx; background: transparent; color: rgba(248,247,237,.55); font-size: 23rpx; font-weight: 800; line-height: 50rpx; }
.size-option--selected { border-color: #89ff3c; background: rgba(137,255,60,.13); color: #89ff3c; }
.preview-card { padding: 24rpx; }
.preview-card__topline { color: rgba(248,247,237,.58); font-family: monospace; font-size: 18rpx; letter-spacing: .12em; }
.live-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: #89ff3c; box-shadow: 0 0 16rpx #89ff3c; }
.preview-card__window { display: flex; align-items: center; height: 172rpx; margin-top: 20rpx; overflow: hidden; border-radius: 16rpx; background: #000; }
.preview-card__track { display: flex; width: max-content; align-items: center; animation: banner-scroll 9s linear infinite; }
.preview-card__text { flex: none; padding-right: 100rpx; color: #fff; font-size: 58rpx; font-weight: 900; letter-spacing: .08em; white-space: nowrap; }
.start-button { display: flex; align-items: center; justify-content: center; gap: 18rpx; width: 100%; min-height: 108rpx; margin-top: 38rpx; border-radius: 999px; background: #89ff3c; color: #0b1306; font-size: 32rpx; font-weight: 900; letter-spacing: .03em; box-shadow: 0 16rpx 34rpx rgba(137,255,60,.2); }
.start-button::after { border: 0; }
.start-button__play { font-size: 24rpx; }
.banner-editor__tip { display: block; margin-top: 26rpx; color: rgba(248,247,237,.42); font-size: 21rpx; text-align: center; }
@keyframes banner-scroll { to { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) { .preview-card__track { animation: none; } }
</style>
