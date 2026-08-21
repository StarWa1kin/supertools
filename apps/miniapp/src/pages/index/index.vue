<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import CodexWatchApp from "../../components/CodexWatchApp.vue";
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
</template>
