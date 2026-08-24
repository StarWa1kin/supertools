<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { computed, getCurrentInstance, nextTick, ref } from "vue";

import { useBorderWatermark } from "../composables/borderWatermark";
import {
  brandLogoPacks,
  framePresets,
  type BrandLogoId,
  type FramePreset,
} from "../config/borderWatermark";
import { ensurePrivacyAuthorization } from "../utils/privacy";

interface ChosenPhoto {
  id: string;
  path: string;
  size: number;
  name: string;
}

interface ChooseMediaFile {
  tempFilePath: string;
  size: number;
}

interface MediaApi {
  chooseMedia?: (options: {
    count: number;
    mediaType: ["image"];
    sourceType: Array<"album" | "camera">;
    success: (result: { tempFiles: ChooseMediaFile[] }) => void;
    fail: (reason: { errMsg?: string }) => void;
  }) => void;
}

type EditorTab = "template" | "frame" | "brand" | "meta";

const CANVAS_ID = "border-watermark-export-canvas";
const MAX_EXPORT_EDGE = 4096;
const componentInstance = getCurrentInstance();
const { settings, preset, brand, parameterLine, restore, save, applyPreset } =
  useBorderWatermark();

const photos = ref<ChosenPhoto[]>([]);
const selectedPhotoIndex = ref(0);
const activeTab = ref<EditorTab>("template");
const exporting = ref(false);
const canvasWidth = ref(300);
const canvasHeight = ref(300);

const currentPhoto = computed(() => photos.value[selectedPhotoIndex.value]);
const frameStyle = computed(() => ({
  padding: `${Math.max(10, settings.framePercent * 2.2)}rpx`,
  paddingBottom: `${Math.max(64, settings.framePercent * 3.6 + 50)}rpx`,
  borderRadius: `${settings.cornerRadius}rpx`,
  background: preset.value.background,
  color: preset.value.foreground,
}));

const modelDefaults: Record<BrandLogoId, string> = {
  apple: "iPhone 17 Pro",
  canon: "Canon EOS R5 Mark II",
  sony: "Sony α7R V",
  custom: "CAMERA / UNKNOWN",
};

function appendPhotos(files: ChooseMediaFile[]) {
  const nextPhotos = files.map((file, index) => ({
    id: `${Date.now()}-${index}`,
    path: file.tempFilePath,
    size: Number(file.size ?? 0),
    name: `照片 ${photos.value.length + index + 1}`,
  }));
  photos.value.push(...nextPhotos);
  selectedPhotoIndex.value = Math.max(0, photos.value.length - nextPhotos.length);
}

function isSelectionCancelled(reason: unknown) {
  const message =
    typeof reason === "object" && reason && "errMsg" in reason
      ? String((reason as { errMsg?: string }).errMsg ?? "")
      : String(reason ?? "");
  return /cancel/i.test(message);
}

function selectionErrorMessage(reason: unknown) {
  const message =
    typeof reason === "object" && reason && "errMsg" in reason
      ? String((reason as { errMsg?: string }).errMsg ?? "")
      : String(reason ?? "");

  if (/privacy|authorize|authorization|declare/i.test(message)) {
    return `微信尚未允许读取相册。请先同意隐私保护提示；开发版还需在公众平台的《用户隐私保护指引》中声明“选中的照片或视频信息”。\n\n错误信息：${message}`;
  }
  return message ? `微信返回：${message}` : "请确认当前设备支持从相册选择图片。";
}

function handleSelectionFailure(reason: unknown) {
  if (isSelectionCancelled(reason)) return;
  uni.showModal({
    title: "暂时无法读取照片",
    content: selectionErrorMessage(reason),
    showCancel: false,
  });
}

function chooseWithLegacyApi(count: number) {
  uni.chooseImage({
    count,
    sizeType: ["original"],
    sourceType: ["album", "camera"],
    success(result) {
      const paths = Array.isArray(result.tempFilePaths)
        ? result.tempFilePaths
        : [result.tempFilePaths];
      const files = Array.isArray(result.tempFiles)
        ? result.tempFiles
        : [result.tempFiles];
      appendPhotos(paths.map((path: string, index: number) => {
        const tempFile = files[index];
        return {
          tempFilePath: path,
          size: typeof tempFile === "object" ? Number(tempFile.size ?? 0) : 0,
        };
      }));
    },
    fail: handleSelectionFailure,
  });
}

async function choosePhotos() {
  const count = Math.max(1, 9 - photos.value.length);
  try {
    await ensurePrivacyAuthorization();
  } catch (reason) {
    handleSelectionFailure(reason);
    return;
  }

  const mediaApi = uni as unknown as MediaApi;
  if (!mediaApi.chooseMedia) {
    chooseWithLegacyApi(count);
    return;
  }

  mediaApi.chooseMedia({
    count,
    mediaType: ["image"],
    sourceType: ["album", "camera"],
    success: (result) => appendPhotos(result.tempFiles),
    fail: handleSelectionFailure,
  });
}

function removePhoto(index: number) {
  photos.value.splice(index, 1);
  selectedPhotoIndex.value = Math.min(
    selectedPhotoIndex.value,
    Math.max(0, photos.value.length - 1),
  );
}

function selectPreset(presetId: FramePreset["id"]) {
  applyPreset(presetId);
}

function selectBrand(brandId: BrandLogoId) {
  settings.brandId = brandId;
  settings.model = modelDefaults[brandId];
  save();
}

function updateFrame(event: { detail: { value: number } }) {
  settings.framePercent = Number(event.detail.value);
  save();
}

function updateRadius(event: { detail: { value: number } }) {
  settings.cornerRadius = Number(event.detail.value);
  save();
}

function toggleParameters() {
  settings.showParameters = !settings.showParameters;
  save();
}

function getImageInfo(src: string) {
  return new Promise<UniApp.GetImageInfoSuccessData>((resolve, reject) => {
    uni.getImageInfo({ src, success: resolve, fail: reject });
  });
}

function canvasToFile(width: number, height: number) {
  return new Promise<string>((resolve, reject) => {
    uni.canvasToTempFilePath(
      {
        canvasId: CANVAS_ID,
        width,
        height,
        destWidth: width,
        destHeight: height,
        fileType: "jpg",
        quality: 0.94,
        success: (result) => resolve(result.tempFilePath),
        fail: reject,
      },
      componentInstance?.proxy,
    );
  });
}

function drawAppleMark(
  context: UniApp.CanvasContext,
  x: number,
  y: number,
  size: number,
  color: string,
) {
  context.save();
  context.translate(x, y);
  context.scale(size / 24, size / 24);
  context.setFillStyle(color);
  context.beginPath();
  context.moveTo(12.2, 6.9);
  context.bezierCurveTo(9.8, 6.9, 9.2, 5.8, 7.2, 5.9);
  context.bezierCurveTo(2.8, 6.1, 1.2, 11.1, 3.2, 16.7);
  context.bezierCurveTo(4.3, 20, 6, 23.8, 8.6, 23.8);
  context.bezierCurveTo(10.3, 23.8, 10.8, 22.8, 12.5, 22.8);
  context.bezierCurveTo(14.2, 22.8, 14.8, 23.8, 16.5, 23.8);
  context.bezierCurveTo(19.3, 23.8, 21.5, 19.6, 22, 17.5);
  context.bezierCurveTo(18.2, 15.9, 17.6, 11, 21.2, 8.2);
  context.bezierCurveTo(19.7, 6.1, 16.8, 5.1, 14.3, 6.2);
  context.bezierCurveTo(13.5, 6.5, 12.9, 6.9, 12.2, 6.9);
  context.fill();
  context.beginPath();
  context.moveTo(12.1, 5.4);
  context.bezierCurveTo(12, 2.8, 13.8, 0.6, 16.7, 0.1);
  context.bezierCurveTo(17, 2.5, 15.3, 4.9, 12.1, 5.4);
  context.fill();
  context.restore();
}

function drawRoundedImage(
  context: UniApp.CanvasContext,
  path: string,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  if (radius <= 0) {
    context.drawImage(path, x, y, width, height);
    return;
  }

  const safeRadius = Math.min(radius, width / 2, height / 2);
  context.save();
  context.beginPath();
  context.moveTo(x + safeRadius, y);
  context.lineTo(x + width - safeRadius, y);
  context.quadraticCurveTo(x + width, y, x + width, y + safeRadius);
  context.lineTo(x + width, y + height - safeRadius);
  context.quadraticCurveTo(x + width, y + height, x + width - safeRadius, y + height);
  context.lineTo(x + safeRadius, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - safeRadius);
  context.lineTo(x, y + safeRadius);
  context.quadraticCurveTo(x, y, x + safeRadius, y);
  context.clip();
  context.drawImage(path, x, y, width, height);
  context.restore();
}

async function renderPhoto(photo: ChosenPhoto) {
  const info = await getImageInfo(photo.path);
  const baseFrame = Math.round(info.width * (settings.framePercent / 100));
  const baseMetaHeight = Math.round(info.width * (settings.showParameters ? 0.15 : 0.11));
  const rawWidth = info.width + baseFrame * 2;
  const rawHeight = info.height + baseFrame + baseMetaHeight;
  const scale = Math.min(1, MAX_EXPORT_EDGE / Math.max(rawWidth, rawHeight));
  const imageWidth = Math.max(1, Math.round(info.width * scale));
  const imageHeight = Math.max(1, Math.round(info.height * scale));
  const frame = Math.max(16, Math.round(baseFrame * scale));
  const metaHeight = Math.max(96, Math.round(baseMetaHeight * scale));
  const outputWidth = imageWidth + frame * 2;
  const outputHeight = imageHeight + frame + metaHeight;

  canvasWidth.value = outputWidth;
  canvasHeight.value = outputHeight;
  await nextTick();

  const context = uni.createCanvasContext(CANVAS_ID, componentInstance?.proxy);
  context.setFillStyle(preset.value.background);
  context.fillRect(0, 0, outputWidth, outputHeight);
  drawRoundedImage(
    context,
    photo.path,
    frame,
    frame,
    imageWidth,
    imageHeight,
    Math.round((settings.cornerRadius / 100) * frame * 1.8),
  );

  const metadataTop = frame + imageHeight;
  const smallFont = Math.max(20, Math.round(outputWidth * 0.024));
  const tinyFont = Math.max(16, Math.round(outputWidth * 0.016));
  const horizontalInset = frame;
  context.setFillStyle(preset.value.foreground);
  context.setTextAlign("left");
  context.setTextBaseline("top");
  context.setFontSize(smallFont);
  context.fillText(settings.model, horizontalInset, metadataTop + metaHeight * 0.28);
  context.setFillStyle(preset.value.muted);
  context.setFontSize(tinyFont);
  context.fillText(settings.signature, horizontalInset, metadataTop + metaHeight * 0.58);

  context.setTextAlign("right");
  context.setFillStyle(preset.value.foreground);
  if (settings.brandId === "apple") {
    const markSize = smallFont * 1.2;
    drawAppleMark(
      context,
      outputWidth - horizontalInset - markSize,
      metadataTop + metaHeight * 0.2,
      markSize,
      preset.value.foreground,
    );
  } else {
    context.setFontSize(Math.round(smallFont * 1.15));
    context.fillText(brand.value.shortName, outputWidth - horizontalInset, metadataTop + metaHeight * 0.22);
  }

  if (settings.showParameters) {
    context.setFillStyle(preset.value.muted);
    context.setFontSize(tinyFont);
    context.fillText(
      parameterLine.value,
      outputWidth - horizontalInset,
      metadataTop + metaHeight * 0.58,
    );
  }

  await new Promise<void>((resolve) => context.draw(false, resolve));
  return canvasToFile(outputWidth, outputHeight);
}

function saveToAlbum(filePath: string) {
  return new Promise<void>((resolve, reject) => {
    // #ifdef H5
    const link = document.createElement("a");
    link.href = filePath;
    link.download = `supertools-frame-${Date.now()}.jpg`;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
    resolve();
    // #endif

    // #ifndef H5
    uni.saveImageToPhotosAlbum({ filePath, success: () => resolve(), fail: reject });
    // #endif
  });
}

async function exportPhotos() {
  if (!photos.value.length) {
    choosePhotos();
    return;
  }
  if (exporting.value) return;

  exporting.value = true;
  uni.showLoading({ title: `正在生成 1/${photos.value.length}`, mask: true });
  try {
    for (let index = 0; index < photos.value.length; index += 1) {
      uni.showLoading({ title: `正在生成 ${index + 1}/${photos.value.length}`, mask: true });
      const outputPath = await renderPhoto(photos.value[index]);
      await saveToAlbum(outputPath);
    }
    uni.hideLoading();
    uni.showToast({ title: `已保存 ${photos.value.length} 张`, icon: "success" });
  } catch (error) {
    uni.hideLoading();
    const message = String((error as { errMsg?: string })?.errMsg ?? error);
    uni.showModal({
      title: "导出没有完成",
      content: message.includes("auth deny")
        ? "请在小程序设置中允许访问相册后重试。"
        : "图片可能过大或格式暂不支持，请换一张照片重试。",
      showCancel: false,
    });
  } finally {
    exporting.value = false;
  }
}

onShow(restore);
</script>

<template>
  <view class="watermark-page">
    <view class="watermark-page__grain" />
    <view class="watermark-shell">
      <view class="workbench-header">
        <view>
          <text class="workbench-header__eyebrow">FRAME LAB / 04</text>
          <text class="workbench-header__title">边框水印</text>
        </view>
        <button class="export-button" :disabled="exporting" @click="exportPhotos">
          {{ photos.length ? `导出 ${photos.length} 张` : "选择照片" }}
        </button>
      </view>

      <text class="workbench-header__description">
        把照片装进一张会说话的相纸。品牌、参数与署名均在本地完成。
      </text>

      <view class="preview-stage">
        <view class="preview-stage__rail preview-stage__rail--top">
          <text>LIVE PREVIEW</text>
          <text>{{ photos.length ? `${selectedPhotoIndex + 1} / ${photos.length}` : "NO. 00" }}</text>
        </view>

        <view v-if="currentPhoto" class="photo-frame" :style="frameStyle">
          <image
            class="photo-frame__image"
            :src="currentPhoto.path"
            mode="widthFix"
            :style="{ borderRadius: `${settings.cornerRadius}rpx` }"
          />
          <view class="photo-frame__meta">
            <view class="photo-frame__identity">
              <text class="photo-frame__model">{{ settings.model }}</text>
              <text class="photo-frame__signature">{{ settings.signature }}</text>
            </view>
            <view class="photo-frame__capture">
              <image
                v-if="brand.asset"
                class="photo-frame__logo"
                :src="brand.asset"
                mode="aspectFit"
              />
              <text v-else class="photo-frame__wordmark">{{ brand.shortName }}</text>
              <text v-if="settings.showParameters" class="photo-frame__parameters">
                {{ parameterLine }}
              </text>
            </view>
          </view>
        </view>

        <button v-else class="empty-preview" @click="choosePhotos">
          <view class="empty-preview__aperture">
            <view v-for="index in 6" :key="index" class="empty-preview__blade" />
          </view>
          <text class="empty-preview__title">放入第一张照片</text>
          <text class="empty-preview__copy">支持单张或最多 9 张批量处理</text>
        </button>

        <scroll-view v-if="photos.length" class="photo-strip" scroll-x>
          <view class="photo-strip__inner">
            <view
              v-for="(photo, index) in photos"
              :key="photo.id"
              :class="['photo-thumb', { 'photo-thumb--active': selectedPhotoIndex === index }]"
              @click="selectedPhotoIndex = index"
            >
              <image :src="photo.path" mode="aspectFill" />
              <button class="photo-thumb__remove" @click.stop="removePhoto(index)">×</button>
            </view>
            <button v-if="photos.length < 9" class="photo-strip__add" @click="choosePhotos">＋</button>
          </view>
        </scroll-view>
      </view>

      <view class="editor-panel">
        <view class="editor-tabs">
          <button
            v-for="tab in [
              { id: 'template', label: '模板' },
              { id: 'frame', label: '边框' },
              { id: 'brand', label: '品牌' },
              { id: 'meta', label: '参数' },
            ]"
            :key="tab.id"
            :class="['editor-tab', { 'editor-tab--active': activeTab === tab.id }]"
            @click="activeTab = tab.id as EditorTab"
          >
            {{ tab.label }}
          </button>
        </view>

        <view v-if="activeTab === 'template'" class="editor-content preset-grid">
          <button
            v-for="item in framePresets"
            :key="item.id"
            :class="['preset-card', { 'preset-card--active': settings.presetId === item.id }]"
            @click="selectPreset(item.id)"
          >
            <view class="preset-card__swatch" :style="{ background: item.background }">
              <view class="preset-card__photo" />
              <view class="preset-card__line" :style="{ background: item.foreground }" />
            </view>
            <text class="preset-card__name">{{ item.name }}</text>
            <text class="preset-card__subtitle">{{ item.subtitle }}</text>
          </button>
        </view>

        <view v-else-if="activeTab === 'frame'" class="editor-content control-stack">
          <view class="control-row">
            <view class="control-row__heading">
              <text>留白宽度</text><text>{{ settings.framePercent }}%</text>
            </view>
            <slider
              :value="settings.framePercent"
              min="2"
              max="18"
              active-color="#e98a3f"
              background-color="#42423e"
              block-color="#f5efe3"
              :block-size="18"
              @change="updateFrame"
            />
          </view>
          <view class="control-row">
            <view class="control-row__heading">
              <text>照片圆角</text><text>{{ settings.cornerRadius }}</text>
            </view>
            <slider
              :value="settings.cornerRadius"
              min="0"
              max="40"
              active-color="#e98a3f"
              background-color="#42423e"
              block-color="#f5efe3"
              :block-size="18"
              @change="updateRadius"
            />
          </view>
        </view>

        <view v-else-if="activeTab === 'brand'" class="editor-content brand-grid">
          <button
            v-for="item in brandLogoPacks"
            :key="item.id"
            :class="['brand-card', { 'brand-card--active': settings.brandId === item.id }]"
            @click="selectBrand(item.id)"
          >
            <view class="brand-card__mark">
              <image v-if="item.asset" :src="item.asset" mode="aspectFit" />
              <text v-else>{{ item.shortName }}</text>
            </view>
            <text class="brand-card__name">{{ item.name }}</text>
            <text class="brand-card__note">{{ item.note }}</text>
          </button>
          <text class="brand-disclaimer">
            品牌名称与标识归各权利人所有，仅用于标注照片拍摄设备，不代表品牌合作或背书。
          </text>
        </view>

        <view v-else class="editor-content form-stack">
          <label class="field-row">
            <text>设备型号</text>
            <input v-model="settings.model" maxlength="32" @blur="save" />
          </label>
          <label class="field-row">
            <text>个人署名</text>
            <input v-model="settings.signature" maxlength="32" @blur="save" />
          </label>
          <view class="parameter-grid">
            <label><text>焦距</text><input v-model="settings.focalLength" maxlength="12" @blur="save" /></label>
            <label><text>光圈</text><input v-model="settings.aperture" maxlength="12" @blur="save" /></label>
            <label><text>快门</text><input v-model="settings.shutter" maxlength="12" @blur="save" /></label>
            <label><text>感光度</text><input v-model="settings.iso" maxlength="12" @blur="save" /></label>
          </view>
          <button class="parameter-toggle" @click="toggleParameters">
            <text>显示拍摄参数</text>
            <view :class="['switch-track', { 'switch-track--on': settings.showParameters }]">
              <view class="switch-track__thumb" />
            </view>
          </button>
        </view>
      </view>

      <view class="privacy-note">
        <text class="privacy-note__mark">LOCAL</text>
        <text>原图、署名和导出结果默认只在你的设备上处理。</text>
      </view>
    </view>

    <canvas
      :canvas-id="CANVAS_ID"
      :id="CANVAS_ID"
      class="export-canvas"
      :style="{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }"
    />
  </view>
</template>

<style scoped>
.watermark-page { position: relative; min-height: 100vh; overflow: hidden; background: #11110f; color: #f4efe4; }
.watermark-page__grain { position: absolute; inset: 0; opacity: .2; pointer-events: none; background-image: radial-gradient(rgba(255,255,255,.18) .7px, transparent .7px); background-size: 7rpx 7rpx; mask-image: linear-gradient(to bottom, #000, transparent 65%); }
.watermark-shell { position: relative; z-index: 1; width: 100%; max-width: 720px; margin: 0 auto; padding: 70rpx 28rpx 110rpx; }
.workbench-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 24rpx; }
.workbench-header__eyebrow { display: block; color: #e98a3f; font-family: "Courier New", monospace; font-size: 19rpx; font-weight: 700; letter-spacing: .2em; }
.workbench-header__title { display: block; margin-top: 13rpx; font-family: "Songti SC", "STSong", serif; font-size: 68rpx; font-weight: 800; letter-spacing: .04em; line-height: 1; }
.workbench-header__description { display: block; max-width: 590rpx; margin-top: 24rpx; color: rgba(244,239,228,.54); font-size: 25rpx; line-height: 1.65; }
.export-button { min-width: 160rpx; height: 72rpx; margin: 0; padding: 0 24rpx; border-radius: 8rpx; background: #e98a3f; color: #1a120b; font-size: 24rpx; font-weight: 800; line-height: 72rpx; box-shadow: 7rpx 7rpx 0 #562b13; }
.export-button[disabled] { opacity: .55; }
.preview-stage { position: relative; margin-top: 48rpx; padding: 46rpx 22rpx 24rpx; border: 1px solid rgba(244,239,228,.16); background: rgba(27,27,24,.92); box-shadow: 0 34rpx 90rpx rgba(0,0,0,.35); }
.preview-stage__rail { position: absolute; top: 16rpx; right: 20rpx; left: 20rpx; display: flex; justify-content: space-between; color: rgba(244,239,228,.36); font-family: "Courier New", monospace; font-size: 16rpx; letter-spacing: .14em; }
.photo-frame { position: relative; width: 100%; overflow: hidden; transition: padding 180ms ease, background 180ms ease; }
.photo-frame__image { display: block; width: 100%; }
.photo-frame__meta { position: absolute; right: 0; bottom: 0; left: 0; display: flex; min-height: 52rpx; align-items: center; justify-content: space-between; gap: 18rpx; padding: 0 18rpx 8rpx; }
.photo-frame__identity, .photo-frame__capture { display: flex; min-width: 0; flex-direction: column; }
.photo-frame__capture { align-items: flex-end; }
.photo-frame__model { overflow: hidden; font-family: "Georgia", "Times New Roman", serif; font-size: 17rpx; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.photo-frame__signature, .photo-frame__parameters { margin-top: 4rpx; font-family: "Courier New", monospace; font-size: 12rpx; letter-spacing: .03em; opacity: .55; white-space: nowrap; }
.photo-frame__logo { width: 62rpx; height: 25rpx; }
.photo-frame__wordmark { font-family: "Times New Roman", serif; font-size: 19rpx; font-weight: 800; }
.empty-preview { display: flex; width: 100%; min-height: 650rpx; margin: 0; padding: 60rpx 30rpx; align-items: center; justify-content: center; flex-direction: column; border: 1px dashed rgba(244,239,228,.24); border-radius: 0; background: radial-gradient(circle at 50% 40%, #34342f, #171714 58%); color: #f4efe4; }
.empty-preview__aperture { position: relative; width: 124rpx; height: 124rpx; margin-bottom: 36rpx; border: 1px solid rgba(233,138,63,.42); border-radius: 50%; }
.empty-preview__blade { position: absolute; top: 50%; left: 50%; width: 48rpx; height: 2px; background: #e98a3f; transform-origin: 0 50%; }
.empty-preview__blade:nth-child(1) { transform: rotate(0deg); }.empty-preview__blade:nth-child(2) { transform: rotate(60deg); }.empty-preview__blade:nth-child(3) { transform: rotate(120deg); }.empty-preview__blade:nth-child(4) { transform: rotate(180deg); }.empty-preview__blade:nth-child(5) { transform: rotate(240deg); }.empty-preview__blade:nth-child(6) { transform: rotate(300deg); }
.empty-preview__title { font-family: "Songti SC", serif; font-size: 37rpx; font-weight: 700; }
.empty-preview__copy { margin-top: 13rpx; font-size: 22rpx; opacity: .42; }
.photo-strip { width: 100%; margin-top: 22rpx; white-space: nowrap; }
.photo-strip__inner { display: inline-flex; align-items: center; gap: 14rpx; padding-right: 12rpx; }
.photo-thumb, .photo-strip__add { position: relative; width: 92rpx; height: 92rpx; flex: none; overflow: hidden; border: 2px solid transparent; background: #242420; }
.photo-thumb--active { border-color: #e98a3f; }
.photo-thumb image { width: 100%; height: 100%; }
.photo-thumb__remove { position: absolute; top: 2rpx; right: 2rpx; width: 28rpx; height: 28rpx; margin: 0; padding: 0; border-radius: 50%; background: rgba(0,0,0,.72); color: #fff; font-size: 21rpx; line-height: 25rpx; }
.photo-strip__add { margin: 0; padding: 0; border: 1px dashed rgba(244,239,228,.3); color: rgba(244,239,228,.7); font-size: 42rpx; line-height: 88rpx; }
.editor-panel { margin-top: 24rpx; border: 1px solid rgba(244,239,228,.16); background: #1b1b18; }
.editor-tabs { display: grid; grid-template-columns: repeat(4, 1fr); border-bottom: 1px solid rgba(244,239,228,.12); }
.editor-tab { position: relative; height: 88rpx; margin: 0; padding: 0; border-radius: 0; background: transparent; color: rgba(244,239,228,.42); font-size: 25rpx; line-height: 88rpx; }
.editor-tab--active { color: #f4efe4; }
.editor-tab--active::before { position: absolute; right: 25%; bottom: -1px; left: 25%; height: 4rpx; background: #e98a3f; content: ""; }
.editor-content { padding: 26rpx; }
.preset-grid, .brand-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18rpx; }
.preset-card, .brand-card { margin: 0; padding: 16rpx; border: 1px solid rgba(244,239,228,.12); border-radius: 0; background: #23231f; color: #f4efe4; text-align: left; }
.preset-card--active, .brand-card--active { border-color: #e98a3f; box-shadow: inset 0 0 0 1px #e98a3f; }
.preset-card__swatch { position: relative; height: 116rpx; padding: 12rpx; }
.preset-card__photo { height: 75rpx; background: linear-gradient(145deg, #374a56, #a36e50 48%, #263037); }
.preset-card__line { position: absolute; right: 14rpx; bottom: 10rpx; width: 38%; height: 3rpx; opacity: .65; }
.preset-card__name, .brand-card__name { display: block; margin-top: 13rpx; font-size: 24rpx; font-weight: 800; }
.preset-card__subtitle, .brand-card__note { display: block; margin-top: 2rpx; color: rgba(244,239,228,.38); font-size: 18rpx; line-height: 1.35; }
.brand-card__mark { display: flex; height: 76rpx; align-items: center; justify-content: center; background: #f4f1e8; color: #111; }
.brand-card__mark image { width: 100rpx; height: 44rpx; }
.brand-card__mark text { font-family: "Times New Roman", serif; font-size: 25rpx; font-weight: 800; }
.brand-disclaimer { grid-column: 1 / -1; padding: 12rpx 4rpx 0; color: rgba(244,239,228,.32); font-size: 18rpx; line-height: 1.6; }
.control-stack, .form-stack { display: flex; flex-direction: column; gap: 24rpx; }
.control-row { padding: 20rpx 18rpx; background: #23231f; }
.control-row__heading { display: flex; justify-content: space-between; font-size: 24rpx; font-weight: 700; }
.control-row__heading text:last-child { color: #e98a3f; font-family: "Courier New", monospace; }
.field-row { display: flex; min-height: 88rpx; align-items: center; justify-content: space-between; gap: 20rpx; padding: 0 20rpx; background: #23231f; }
.field-row > text { flex: none; color: rgba(244,239,228,.52); font-size: 22rpx; }
.field-row input { min-width: 0; flex: 1; color: #f4efe4; font-size: 25rpx; text-align: right; }
.parameter-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14rpx; }
.parameter-grid label { padding: 18rpx; background: #23231f; }
.parameter-grid text { display: block; color: rgba(244,239,228,.38); font-size: 18rpx; }
.parameter-grid input { height: 54rpx; color: #f4efe4; font-family: "Courier New", monospace; font-size: 25rpx; }
.parameter-toggle { display: flex; height: 82rpx; margin: 0; padding: 0 20rpx; align-items: center; justify-content: space-between; border-radius: 0; background: #23231f; color: #f4efe4; font-size: 23rpx; }
.switch-track { width: 76rpx; height: 42rpx; padding: 5rpx; border-radius: 999px; background: #44443f; transition: background 160ms ease; }
.switch-track__thumb { width: 32rpx; height: 32rpx; border-radius: 50%; background: #eee9df; transition: transform 160ms ease; }
.switch-track--on { background: #e98a3f; }.switch-track--on .switch-track__thumb { transform: translateX(34rpx); }
.privacy-note { display: flex; margin-top: 26rpx; align-items: flex-start; gap: 14rpx; color: rgba(244,239,228,.38); font-size: 19rpx; line-height: 1.55; }
.privacy-note__mark { flex: none; padding: 3rpx 8rpx; border: 1px solid rgba(233,138,63,.45); color: #e98a3f; font-family: "Courier New", monospace; font-size: 15rpx; letter-spacing: .08em; }
.export-canvas { position: fixed; top: -99999px; left: -99999px; pointer-events: none; }
button::after { border: 0; }
@media (prefers-reduced-motion: reduce) { .photo-frame, .switch-track, .switch-track__thumb { transition: none; } }
</style>
