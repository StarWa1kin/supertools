<script setup lang="ts">
import { onShareAppMessage, onShareTimeline, onShow } from "@dcloudio/uni-app";

import CodexWatchApp from "../../components/CodexWatchApp.vue";
import { createPageShare } from "../../composables/usePageShare";

const pageShare = createPageShare({
  title: "Codex 额度情报｜奇思妙箱",
  path: "/pages/codex-watch/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);
</script>

<template>
  <CodexWatchApp />
</template>
