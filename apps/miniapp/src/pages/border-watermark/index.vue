<script setup lang="ts">
import { onShareAppMessage, onShareTimeline, onShow } from "@dcloudio/uni-app";

import BorderWatermarkApp from "../../components/BorderWatermarkApp.vue";
import { createPageShare } from "../../composables/usePageShare";

const pageShare = createPageShare({
  title: "边框水印｜奇思妙箱",
  path: "/pages/border-watermark/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);
</script>

<template>
  <BorderWatermarkApp />
</template>
