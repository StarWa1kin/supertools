<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";

const sourceUrl = ref("");

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
