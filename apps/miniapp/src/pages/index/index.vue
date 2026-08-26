<script setup lang="ts">
import {
  onShareAppMessage,
  onShareTimeline,
  onShow,
} from "@dcloudio/uni-app";

import CodexWatchApp from "../../components/CodexWatchApp.vue";
import BorderWatermarkApp from "../../components/BorderWatermarkApp.vue";
import HandBannerApp from "../../components/HandBannerApp.vue";
import VideoParserApp from "../../components/VideoParserApp.vue";
import { createPageShare } from "../../composables/usePageShare";
import { usePrimaryApp } from "../../composables/usePrimaryApp";

const { primaryApp, refreshPrimaryApp } = usePrimaryApp();

const pageShare = createPageShare({
  title: () => `${primaryApp.value.name}｜奇思妙箱`,
  path: "/pages/index/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);

function refreshHome() {
  refreshPrimaryApp();
  uni.setNavigationBarTitle({ title: primaryApp.value.name });
}

refreshPrimaryApp();
onShow(refreshHome);
</script>

<template>
  <CodexWatchApp v-if="primaryApp.id === 'codex-watch'" />
  <VideoParserApp v-else-if="primaryApp.id === 'video-parser'" />
  <HandBannerApp v-else-if="primaryApp.id === 'hand-banner'" />
  <BorderWatermarkApp v-else-if="primaryApp.id === 'border-watermark'" />
</template>
