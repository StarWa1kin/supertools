import { computed, ref } from "vue";

import { resolveApiUrl } from "../api/client";
import { resolveVideo, type VideoAsset, type VideoResolveResult } from "../api/videoParser";
import { detectVideoPlatform, extractShareUrl } from "../utils/toolRules";
import { ensurePrivacyAuthorization } from "../utils/privacy";
import {
  addVideoParserHistory,
  updateVideoParserHistory,
} from "./videoParserHistory";

function isH5Runtime() {
  return typeof window !== "undefined" && typeof window.open === "function";
}

function errorMessage(reason: unknown) {
  if (reason instanceof Error) return reason.message;
  if (typeof reason === "object" && reason) {
    if ("errMsg" in reason && typeof reason.errMsg === "string") {
      return reason.errMsg;
    }
    if ("message" in reason && typeof reason.message === "string") {
      return reason.message;
    }
  }
  return "操作失败，请稍后再试";
}

function downloadTempFile(url: string, onProgress: (progress: number) => void) {
  return new Promise<string>((resolve, reject) => {
    const task = uni.downloadFile({
      url,
      timeout: 120_000,
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.tempFilePath);
          return;
        }
        reject(new Error(`媒体下载失败（${response.statusCode}）`));
      },
      fail(reason) {
        reject(new Error(reason.errMsg || "媒体下载失败"));
      },
    });
    task.onProgressUpdate?.((event) => onProgress(event.progress));
  });
}

function saveVideo(filePath: string) {
  return new Promise<void>((resolve, reject) => {
    uni.saveVideoToPhotosAlbum({
      filePath,
      success: () => resolve(),
      fail: reject,
    });
  });
}

function saveImage(filePath: string) {
  return new Promise<void>((resolve, reject) => {
    uni.saveImageToPhotosAlbum({
      filePath,
      success: () => resolve(),
      fail: reject,
    });
  });
}

function isPermissionError(reason: unknown) {
  const message =
    typeof reason === "object" && reason && "errMsg" in reason
      ? String((reason as { errMsg?: string }).errMsg || "")
      : errorMessage(reason);
  return /auth|authorize|permission|deny|denied/i.test(message);
}

async function offerOpenSettings() {
  const modal = await uni.showModal({
    title: "需要相册权限",
    content: "请在设置中允许保存到相册，然后重新下载。",
    confirmText: "打开设置",
  });
  if (modal.confirm) {
    await uni.openSetting();
  }
}

export function useVideoParser() {
  const activeResultView = ref<"media" | "caption">("media");
  const shareText = ref("");
  const loading = ref(false);
  const saving = ref(false);
  const downloadProgress = ref(0);
  const saveStatus = ref("");
  const error = ref("");
  const copyFeedback = ref("");
  const result = ref<VideoResolveResult>();

  const shareUrl = computed(() => extractShareUrl(shareText.value));
  const detectedPlatform = computed(() => detectVideoPlatform(shareText.value));
  const previewAssets = computed(
    () =>
      result.value?.assets.map((asset) => ({
        ...asset,
        previewUrl: resolveApiUrl(asset.previewPath),
        downloadUrl: resolveApiUrl(asset.downloadPath),
      })) || [],
  );
  const coverUrl = computed(() =>
    result.value?.coverUrl ? resolveApiUrl(result.value.coverUrl) : "",
  );

  async function pasteFromClipboard() {
    try {
      const clipboard = await uni.getClipboardData();
      shareText.value = clipboard.data.trim();
      error.value = "";
    } catch (reason) {
      error.value = errorMessage(reason) || "无法读取剪贴板";
    }
  }

  function clear() {
    activeResultView.value = "media";
    shareText.value = "";
    result.value = undefined;
    error.value = "";
    saveStatus.value = "";
    copyFeedback.value = "";
  }

  async function submit() {
    if (!shareUrl.value) {
      error.value = "请粘贴包含 http 或 https 链接的分享文案";
      return;
    }
    if (!detectedPlatform.value) {
      error.value = "暂不支持该分享链接，请更换其他公开链接";
      return;
    }
    loading.value = true;
    error.value = "";
    saveStatus.value = "";
    copyFeedback.value = "";
    result.value = undefined;
    const historyId = addVideoParserHistory(
      shareText.value,
      shareUrl.value,
      detectedPlatform.value,
    );
    try {
      result.value = await resolveVideo(shareUrl.value);
      activeResultView.value = "media";
      updateVideoParserHistory(historyId, {
        status: "success",
        title: result.value.title,
      });
    } catch (reason) {
      error.value = errorMessage(reason);
      updateVideoParserHistory(historyId, {
        status: "failed",
        error: error.value,
      });
    } finally {
      loading.value = false;
    }
  }

  async function copySource(asset: VideoAsset) {
    await uni.setClipboardData({ data: asset.sourceUrl });
    copyFeedback.value = "媒体地址已复制";
  }

  async function copyCaption() {
    if (!result.value?.title) return;
    await uni.setClipboardData({ data: result.value.title });
    copyFeedback.value = "文案已复制";
  }

  function previewImage(index: number) {
    const urls = previewAssets.value
      .filter((asset) => asset.kind === "image")
      .map((asset) => asset.previewUrl);
    if (urls.length) {
      uni.previewImage({ current: index, urls });
    }
  }

  async function saveAsset(asset: VideoAsset, index = 0, total = 1) {
    if (isH5Runtime()) {
      window.open(
        resolveApiUrl(asset.downloadPath),
        "_blank",
        "noopener,noreferrer",
      );
      return;
    }
    await ensurePrivacyAuthorization();
    saveStatus.value =
      total > 1 ? `正在保存第 ${index + 1}/${total} 项` : "正在下载媒体";
    const filePath = await downloadTempFile(
      resolveApiUrl(asset.downloadPath),
      (progress) => {
        downloadProgress.value = progress;
      },
    );
    if (asset.kind === "video") {
      await saveVideo(filePath);
    } else {
      await saveImage(filePath);
    }
  }

  async function downloadAsset(asset: VideoAsset) {
    saving.value = true;
    downloadProgress.value = 0;
    error.value = "";
    try {
      await saveAsset(asset);
      saveStatus.value = isH5Runtime() ? "已在新窗口打开" : "已保存到相册";
      if (!isH5Runtime()) {
        uni.showToast({ title: "保存成功", icon: "success" });
      }
    } catch (reason) {
      saveStatus.value = "";
      if (isPermissionError(reason)) {
        await offerOpenSettings();
      } else {
        error.value = errorMessage(reason);
      }
    } finally {
      saving.value = false;
    }
  }

  async function downloadAllImages() {
    const images =
      result.value?.assets.filter((asset) => asset.kind === "image") || [];
    if (!images.length) return;
    saving.value = true;
    downloadProgress.value = 0;
    error.value = "";
    let saved = 0;
    try {
      for (const [index, image] of images.entries()) {
        await saveAsset(image, index, images.length);
        saved += 1;
      }
      saveStatus.value = isH5Runtime()
        ? `已打开 ${saved} 张图片`
        : `已保存 ${saved} 张图片`;
    } catch (reason) {
      saveStatus.value = saved ? `已保存 ${saved}/${images.length} 张图片` : "";
      if (isPermissionError(reason)) {
        await offerOpenSettings();
      } else {
        error.value = `${saveStatus.value ? `${saveStatus.value}，` : ""}${errorMessage(reason)}`;
      }
    } finally {
      saving.value = false;
    }
  }

  return {
    activeResultView,
    clear,
    copySource,
    copyCaption,
    copyFeedback,
    coverUrl,
    detectedPlatform,
    downloadAllImages,
    downloadAsset,
    downloadProgress,
    error,
    loading,
    pasteFromClipboard,
    previewAssets,
    previewImage,
    result,
    saveStatus,
    saving,
    shareText,
    submit,
  };
}
