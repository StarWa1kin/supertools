<script setup lang="ts">
import { onShareAppMessage, onShareTimeline, onShow } from "@dcloudio/uni-app";

import VideoParserApp from "../../components/VideoParserApp.vue";
import { createPageShare } from "../../composables/usePageShare";

const pageShare = createPageShare({
  title: "视频链接解析｜奇思妙箱",
  path: "/pages/video-parser/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);
</script>

<template>
  <VideoParserApp />
</template>
