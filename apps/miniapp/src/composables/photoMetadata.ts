import * as exifr from "exifr";

export interface PhotoMetadata {
  make: string;
  model: string;
  capturedAt: string;
  focalLength: string;
  aperture: string;
  shutter: string;
  iso: string;
  location: string;
  latitude?: number;
  longitude?: number;
}

type ExifValue = string | number | Date | undefined;

interface ExifResult {
  Make?: ExifValue;
  Model?: ExifValue;
  DateTimeOriginal?: ExifValue;
  CreateDate?: ExifValue;
  ModifyDate?: ExifValue;
  FocalLength?: ExifValue;
  FNumber?: ExifValue;
  ApertureValue?: ExifValue;
  ExposureTime?: ExifValue;
  ISOSpeedRatings?: ExifValue;
  PhotographicSensitivity?: ExifValue;
  latitude?: ExifValue;
  longitude?: ExifValue;
}

function cleanText(value: ExifValue) {
  return typeof value === "string" ? value.replace(/\0/g, "").trim() : "";
}

function formatNumber(value: number, digits = 1) {
  return Number.isInteger(value) ? String(value) : value.toFixed(digits).replace(/\.0+$/, "");
}

export function formatExifDate(value: ExifValue) {
  if (!value) return "";
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    const pad = (part: number) => String(part).padStart(2, "0");
    return `${value.getFullYear()}.${pad(value.getMonth() + 1)}.${pad(value.getDate())} ${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`;
  }
  const normalized = cleanText(value).replace(
    /^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}:\d{2}:\d{2})/,
    "$1.$2.$3 $4",
  );
  return normalized.slice(0, 19);
}

export function formatShutterSpeed(value: ExifValue) {
  const seconds = Number(value);
  if (!Number.isFinite(seconds) || seconds <= 0) return "";
  if (seconds < 1) return `1/${Math.max(1, Math.round(1 / seconds))}`;
  return `${formatNumber(seconds, 1)}s`;
}

function toDms(value: number, positive: string, negative: string) {
  const absolute = Math.abs(value);
  const totalSeconds = Math.round(absolute * 3600);
  const degrees = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${degrees}°${String(minutes).padStart(2, "0")}'${String(seconds).padStart(2, "0")}"${value >= 0 ? positive : negative}`;
}

export function formatCoordinates(latitude?: number, longitude?: number) {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return "";
  return `${toDms(latitude as number, "N", "S")} ${toDms(longitude as number, "E", "W")}`;
}

export function normalizeExif(raw: ExifResult | null | undefined): PhotoMetadata | null {
  if (!raw) return null;
  const latitude = Number(raw.latitude);
  const longitude = Number(raw.longitude);
  const focalLength = Number(raw.FocalLength);
  const aperture = Number(raw.FNumber ?? raw.ApertureValue);
  const iso = Number(raw.ISOSpeedRatings ?? raw.PhotographicSensitivity);
  const metadata: PhotoMetadata = {
    make: cleanText(raw.Make),
    model: cleanText(raw.Model),
    capturedAt: formatExifDate(raw.DateTimeOriginal ?? raw.CreateDate ?? raw.ModifyDate),
    focalLength: Number.isFinite(focalLength) && focalLength > 0 ? `${formatNumber(focalLength)}mm` : "",
    aperture: Number.isFinite(aperture) && aperture > 0 ? `f/${formatNumber(aperture)}` : "",
    shutter: formatShutterSpeed(raw.ExposureTime),
    iso: Number.isFinite(iso) && iso > 0 ? `ISO${Math.round(iso)}` : "",
    location: formatCoordinates(latitude, longitude),
    ...(Number.isFinite(latitude) ? { latitude } : {}),
    ...(Number.isFinite(longitude) ? { longitude } : {}),
  };
  return Object.values(metadata).some((value) => value !== "" && value !== undefined)
    ? metadata
    : null;
}

interface FileSystemApi {
  readFile(options: {
    filePath: string;
    success: (result: { data: ArrayBuffer | string }) => void;
    fail: (reason: unknown) => void;
  }): void;
}

async function readPhoto(path: string) {
  const platformApi = uni as unknown as {
    getFileSystemManager?: () => FileSystemApi;
  };
  const nativeApi = globalThis as unknown as {
    wx?: { getFileSystemManager?: () => FileSystemApi };
  };
  const getFileSystemManager =
    platformApi.getFileSystemManager ?? nativeApi.wx?.getFileSystemManager;
  if (getFileSystemManager) {
    return new Promise<ArrayBuffer>((resolve, reject) => {
      getFileSystemManager().readFile({
        filePath: path,
        success: (result) =>
          result.data instanceof ArrayBuffer
            ? resolve(result.data)
            : reject(new Error("照片未以二进制格式返回")),
        fail: reject,
      });
    });
  }
  const response = await fetch(path);
  if (!response.ok) throw new Error("无法读取照片文件");
  return response.arrayBuffer();
}

export async function readPhotoMetadata(path: string) {
  const buffer = await readPhoto(path);
  const raw = (await exifr.parse(buffer, {
    tiff: true,
    exif: true,
    gps: true,
    interop: false,
    ifd1: false,
    translateValues: true,
  })) as ExifResult | undefined;
  return normalizeExif(raw);
}
