import { beforeEach, describe, expect, it, vi } from "vitest";

import type { VideoAsset, VideoResolveResult } from "../src/api/videoParser";
import { useVideoParser } from "../src/composables/useVideoParser";
import { getVideoParserHistory } from "../src/composables/videoParserHistory";

const videoAsset: VideoAsset = {
  kind: "video",
  sourceUrl: "https://v.douyinvod.com/video.mp4",
  previewPath: "/api/v1/video-parser/media?token=preview",
  downloadPath: "/api/v1/video-parser/media?token=download&download=true",
};

const result: VideoResolveResult = {
  platform: "douyin",
  mediaType: "video",
  canonicalUrl: "https://www.douyin.com/video/1",
  title: "测试视频",
  author: { name: "作者" },
  durationMs: 10_000,
  assets: [videoAsset],
};

function baseUni(overrides: Record<string, unknown> = {}) {
  return {
    request: vi.fn((options) => options.success({ statusCode: 200, data: result })),
    getClipboardData: vi.fn(async () => ({ data: "" })),
    setClipboardData: vi.fn(async () => undefined),
    showToast: vi.fn(),
    showModal: vi.fn(async () => ({ confirm: false, cancel: true })),
    openSetting: vi.fn(async () => ({})),
    previewImage: vi.fn(),
    ...overrides,
  };
}

describe("useVideoParser", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("extracts a share URL and resolves it through the API", async () => {
    const storage = new Map<string, unknown>();
    const request = vi.fn((options) => options.success({ statusCode: 200, data: result }));
    vi.stubGlobal("uni", baseUni({
      getStorageSync: vi.fn((key: string) => storage.get(key)),
      request,
      setStorageSync: vi.fn((key: string, value: unknown) => storage.set(key, value)),
    }));
    const parser = useVideoParser();
    parser.shareText.value = "复制打开抖音 https://v.douyin.com/abc/ 查看作品";

    await parser.submit();

    expect(parser.result.value?.title).toBe("测试视频");
    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      method: "POST",
      data: { url: "https://v.douyin.com/abc/" },
    }));
    expect(parser.activeResultView.value).toBe("media");
    expect(getVideoParserHistory()).toEqual([
      expect.objectContaining({
        input: "复制打开抖音 https://v.douyin.com/abc/ 查看作品",
        platform: "douyin",
        status: "success",
        title: "测试视频",
        url: "https://v.douyin.com/abc/",
      }),
    ]);
  });

  it("copies the parsed caption separately from the media URL", async () => {
    const setClipboardData = vi.fn(async () => undefined);
    vi.stubGlobal("uni", baseUni({ setClipboardData }));
    const parser = useVideoParser();
    parser.result.value = result;
    parser.activeResultView.value = "caption";

    await parser.copyCaption();

    expect(setClipboardData).toHaveBeenCalledWith({ data: "测试视频" });
    expect(parser.copyFeedback.value).toBe("文案已复制");
  });

  it("saves a downloaded video to the photo album", async () => {
    const saveVideoToPhotosAlbum = vi.fn((options) => options.success());
    const downloadFile = vi.fn((options) => {
      options.success({ statusCode: 200, tempFilePath: "temp/video.mp4" });
      return { onProgressUpdate: (callback) => callback({ progress: 100 }) };
    });
    vi.stubGlobal("uni", baseUni({ downloadFile, saveVideoToPhotosAlbum }));
    const parser = useVideoParser();

    await parser.downloadAsset(videoAsset);

    expect(saveVideoToPhotosAlbum).toHaveBeenCalledWith(expect.objectContaining({
      filePath: "temp/video.mp4",
    }));
    expect(parser.downloadProgress.value).toBe(100);
    expect(parser.saveStatus.value).toBe("已保存到相册");
  });

  it("offers settings when album permission is denied", async () => {
    const openSetting = vi.fn(async () => ({}));
    const showModal = vi.fn(async () => ({ confirm: true, cancel: false }));
    const downloadFile = vi.fn((options) => {
      options.success({ statusCode: 200, tempFilePath: "temp/video.mp4" });
      return { onProgressUpdate: vi.fn() };
    });
    const saveVideoToPhotosAlbum = vi.fn((options) => {
      options.fail({ errMsg: "saveVideoToPhotosAlbum:fail auth deny" });
    });
    vi.stubGlobal("uni", baseUni({
      downloadFile,
      openSetting,
      saveVideoToPhotosAlbum,
      showModal,
    }));
    const parser = useVideoParser();

    await parser.downloadAsset(videoAsset);

    expect(showModal).toHaveBeenCalled();
    expect(openSetting).toHaveBeenCalled();
    expect(parser.saving.value).toBe(false);
  });

  it("reports partial success when saving multiple images fails", async () => {
    const images: VideoAsset[] = [1, 2].map((index) => ({
      kind: "image",
      sourceUrl: `https://sns-img.xhscdn.com/${index}.jpg`,
      previewPath: `/preview/${index}`,
      downloadPath: `/download/${index}`,
    }));
    let saveCount = 0;
    const downloadFile = vi.fn((options) => {
      options.success({ statusCode: 200, tempFilePath: "temp/image.jpg" });
      return { onProgressUpdate: vi.fn() };
    });
    const saveImageToPhotosAlbum = vi.fn((options) => {
      saveCount += 1;
      if (saveCount === 1) options.success();
      else options.fail(new Error("磁盘空间不足"));
    });
    vi.stubGlobal("uni", baseUni({ downloadFile, saveImageToPhotosAlbum }));
    const parser = useVideoParser();
    parser.result.value = { ...result, mediaType: "images", assets: images };

    await parser.downloadAllImages();

    expect(parser.saveStatus.value).toBe("已保存 1/2 张图片");
    expect(parser.error.value).toContain("磁盘空间不足");
  });
});
