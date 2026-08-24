<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import CodexWatchApp from "../../components/CodexWatchApp.vue";
import BorderWatermarkApp from "../../components/BorderWatermarkApp.vue";
import HandBannerApp from "../../components/HandBannerApp.vue";
import VideoParserApp from "../../components/VideoParserApp.vue";
import { usePrimaryApp } from "../../composables/usePrimaryApp";

const { primaryApp, refreshPrimaryApp } = usePrimaryApp();

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
