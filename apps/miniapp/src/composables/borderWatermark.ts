import { computed, reactive } from "vue";

import {
  getBrandLogo,
  getFramePreset,
  type BrandLogoId,
  type FramePreset,
} from "../config/borderWatermark";

const STORAGE_KEY = "supertools.border-watermark.settings.v2";

export interface BorderWatermarkSettings {
  presetId: FramePreset["id"];
  brandId: BrandLogoId;
  framePercent: number;
  cornerRadius: number;
  signature: string;
  model: string;
  capturedAt: string;
  location: string;
  focalLength: string;
  aperture: string;
  shutter: string;
  iso: string;
  showParameters: boolean;
}

export const defaultBorderWatermarkSettings: BorderWatermarkSettings = {
  presetId: "gallery",
  brandId: "apple",
  framePercent: 0,
  cornerRadius: 0,
  signature: "SUPERTOOLS STUDIO",
  model: "iPhone 17 Pro",
  capturedAt: "2026.01.01 18:49:31",
  location: `48°20'22"N 86°44'27"E`,
  focalLength: "24mm",
  aperture: "f/1.8",
  shutter: "1/60",
  iso: "ISO200",
  showParameters: true,
};

function clamp(value: unknown, min: number, max: number, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.min(max, Math.max(min, parsed)) : fallback;
}

function cleanText(value: unknown, fallback: string, maxLength = 36) {
  if (typeof value !== "string") return fallback;
  const cleaned = value.replace(/[\r\n]+/g, " ").replace(/\s{2,}/g, " ").trim();
  return cleaned.slice(0, maxLength) || fallback;
}

function cleanOptionalText(value: unknown, fallback: string, maxLength = 36) {
  if (value === undefined || value === null) return fallback;
  if (typeof value !== "string") return fallback;
  return value.replace(/[\r\n]+/g, " ").replace(/\s{2,}/g, " ").trim().slice(0, maxLength);
}

export function sanitizeBorderWatermarkSettings(
  value: Partial<BorderWatermarkSettings> | null | undefined,
): BorderWatermarkSettings {
  const source = value ?? {};
  const presetId = getFramePreset(source.presetId ?? "gallery").id;
  const brandId = getBrandLogo(source.brandId ?? "apple").id;

  return {
    presetId,
    brandId,
    framePercent: clamp(source.framePercent, 0, 18, getFramePreset(presetId).defaultFrame),
    cornerRadius: clamp(source.cornerRadius, 0, 40, 0),
    signature: cleanText(source.signature, defaultBorderWatermarkSettings.signature, 32),
    model: cleanText(source.model, defaultBorderWatermarkSettings.model, 32),
    capturedAt: cleanOptionalText(source.capturedAt, defaultBorderWatermarkSettings.capturedAt, 24),
    location: cleanOptionalText(source.location, defaultBorderWatermarkSettings.location, 48),
    focalLength: cleanOptionalText(source.focalLength, defaultBorderWatermarkSettings.focalLength, 12),
    aperture: cleanOptionalText(source.aperture, defaultBorderWatermarkSettings.aperture, 12),
    shutter: cleanOptionalText(source.shutter, defaultBorderWatermarkSettings.shutter, 12),
    iso: cleanOptionalText(source.iso, defaultBorderWatermarkSettings.iso, 12),
    showParameters:
      typeof source.showParameters === "boolean" ? source.showParameters : true,
  };
}

export function formatParameterLine(settings: BorderWatermarkSettings) {
  if (!settings.showParameters) return "";
  return [settings.focalLength, settings.aperture, settings.shutter, settings.iso]
    .filter(Boolean)
    .join(" ");
}

export function useBorderWatermark() {
  const settings = reactive<BorderWatermarkSettings>({ ...defaultBorderWatermarkSettings });

  function restore() {
    const stored = uni.getStorageSync(STORAGE_KEY);
    if (!stored || typeof stored !== "object") return settings;
    Object.assign(settings, sanitizeBorderWatermarkSettings(stored));
    return settings;
  }

  function save() {
    const sanitized = sanitizeBorderWatermarkSettings(settings);
    Object.assign(settings, sanitized);
    uni.setStorageSync(STORAGE_KEY, sanitized);
    return sanitized;
  }

  function applyPreset(presetId: FramePreset["id"]) {
    const preset = getFramePreset(presetId);
    settings.presetId = preset.id;
    settings.framePercent = preset.defaultFrame;
    save();
  }

  return {
    settings,
    preset: computed(() => getFramePreset(settings.presetId)),
    brand: computed(() => getBrandLogo(settings.brandId)),
    parameterLine: computed(() => formatParameterLine(settings)),
    restore,
    save,
    applyPreset,
  };
}
