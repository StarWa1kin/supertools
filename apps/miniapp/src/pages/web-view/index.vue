<script setup lang="ts">
import {
  onLoad,
  onShareAppMessage,
  onShareTimeline,
  onShow,
} from "@dcloudio/uni-app";
import { ref } from "vue";

import { createPageShare } from "../../composables/usePageShare";

const sourceUrl = ref("");

const pageShare = createPageShare({
  title: "AI 实用教程｜奇思妙箱",
  path: () =>
    sourceUrl.value
      ? `/pages/web-view/index?url=${encodeURIComponent(sourceUrl.value)}`
      : "/pages/web-view/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);

onLoad((options) => {
  const rawUrl = typeof options?.url === "string" ? decodeURIComponent(options.url) : "";
  if (!rawUrl.startsWith("https://mp.weixin.qq.com/")) {
    uni.showToast({ title: "链接不可用", icon: "none" });
    return;
  }
  sourceUrl.value = rawUrl;
});
</script>

<template>
  <web-view v-if="sourceUrl" :src="sourceUrl" />
</template>
