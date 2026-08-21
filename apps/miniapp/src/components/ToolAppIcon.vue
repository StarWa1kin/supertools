<script setup lang="ts">
import type { ToolApp } from "../config/apps";

withDefaults(
  defineProps<{
    app: ToolApp;
    size?: "card" | "grid";
  }>(),
  { size: "grid" },
);
</script>

<template>
  <view :class="['app-icon', `app-icon--${size}`]">
    <image class="app-icon__image" :src="app.icon" mode="aspectFit" />
  </view>
</template>

<style scoped>
.app-icon {
  position: relative;
  flex: none;
  overflow: hidden;
  border: 1px solid var(--color-soft-border);
  border-radius: 25%;
  box-shadow:
    0 12rpx 26rpx var(--color-shadow-soft),
    inset 0 1px 0 rgba(255, 255, 255, 0.42);
}

.app-icon--card {
  width: 104rpx;
  height: 104rpx;
}

.app-icon--grid {
  width: 120rpx;
  height: 120rpx;
}

.app-icon__image {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
