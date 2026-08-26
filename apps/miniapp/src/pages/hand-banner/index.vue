<script setup lang="ts">
import { onShareAppMessage, onShareTimeline, onShow } from "@dcloudio/uni-app";

import HandBannerApp from "../../components/HandBannerApp.vue";
import { createPageShare } from "../../composables/usePageShare";

const pageShare = createPageShare({
  title: "手持弹幕｜奇思妙箱",
  path: "/pages/hand-banner/index",
});
onShareAppMessage(pageShare.shareAppMessage);
onShareTimeline(pageShare.shareTimeline);
onShow(pageShare.showShareMenu);
</script>

<template>
  <view class="hand-banner-page">
    <HandBannerApp />
  </view>
</template>

<style scoped>
.hand-banner-page {
  min-height: 100%;
}
</style>
