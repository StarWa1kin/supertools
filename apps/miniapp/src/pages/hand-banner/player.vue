<script setup lang="ts">
import { onLoad, onUnload } from "@dcloudio/uni-app";
import { ref } from "vue";

import { useHandBanner } from "../../composables/handBanner";

const { message, textColor, fontScale, restore } = useHandBanner();
const showHint = ref(true);
let hintTimer: ReturnType<typeof setTimeout> | undefined;

function goBack() {
  uni.navigateBack();
}

onLoad(() => {
  restore();
  showHint.value = true;
  hintTimer = setTimeout(() => {
    showHint.value = false;
  }, 1000);
});

onUnload(() => {
  if (hintTimer !== undefined) {
    clearTimeout(hintTimer);
  }
});
</script>

<template>
  <view class="banner-player" @click="goBack">
    <view class="banner-player__scanline" />
    <view class="banner-player__track">
      <text class="banner-player__text" :style="{ color: textColor, fontSize: `${16 * fontScale}vw` }">{{ message }}</text>
      <text class="banner-player__text" :style="{ color: textColor, fontSize: `${16 * fontScale}vw` }" aria-hidden="true">{{ message }}</text>
    </view>
    <view v-if="showHint" class="banner-player__hint">轻触屏幕返回编辑</view>
  </view>
</template>

<style scoped>
.banner-player { position: relative; display: flex; width: 100vw; height: 100vh; align-items: center; overflow: hidden; background: #000; color: #fff; }
.banner-player__track { display: flex; width: max-content; align-items: center; animation: full-banner-scroll 12s linear infinite; }
.banner-player__text { flex: none; padding-right: 17vw; color: #fff; font-size: 16vw; font-weight: 900; letter-spacing: .07em; line-height: 1; white-space: nowrap; text-shadow: 0 0 18rpx rgba(255,255,255,.35); }
.banner-player__scanline { position: absolute; z-index: 1; inset: 0; pointer-events: none; opacity: .13; background: repeating-linear-gradient(0deg, transparent 0, transparent 5px, #fff 6px); }
.banner-player__hint { position: absolute; right: 28rpx; bottom: 20rpx; color: rgba(255,255,255,.42); font-size: 20rpx; }
@keyframes full-banner-scroll { to { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) { .banner-player__track { animation: none; } }
</style>
