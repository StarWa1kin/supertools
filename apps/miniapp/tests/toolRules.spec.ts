import { afterEach, describe, expect, it, vi } from "vitest";

import {
  detectVideoPlatform,
  extractShareUrl,
  matchCodexKeywords,
} from "../src/utils/toolRules";

describe("detectVideoPlatform", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("recognizes supported share link hosts", () => {
    expect(detectVideoPlatform("https://v.douyin.com/example")).toBe("douyin");
    expect(detectVideoPlatform("https://v.kuaishou.com/example")).toBe("kuaishou");
    expect(detectVideoPlatform("https://xhslink.com/example")).toBe("xiaohongshu");
    expect(detectVideoPlatform("https://xhslink.cn/o/4NDVCw2LfT7")).toBe("xiaohongshu");
  });

  it("rejects lookalike and invalid hosts", () => {
    expect(detectVideoPlatform("https://douyin.com.example.org/video")).toBeUndefined();
    expect(detectVideoPlatform("https://user@douyin.com/video")).toBeUndefined();
    expect(detectVideoPlatform("not a url")).toBeUndefined();
  });

  it("works when the mini program runtime does not provide URL", () => {
    vi.stubGlobal("URL", undefined);

    expect(detectVideoPlatform(
      "https://v.douyin.com/Y-dJIx8wVFc/ 复制此链接，打开抖音搜索",
    )).toBe("douyin");
  });
});

describe("extractShareUrl", () => {
  it("extracts the first URL from platform share text", () => {
    expect(extractShareUrl("复制打开抖音 https://v.douyin.com/abc/ 一起看看"))
      .toBe("https://v.douyin.com/abc/");
    expect(extractShareUrl("链接：https://xhslink.com/a，复制后打开"))
      .toBe("https://xhslink.com/a");
  });

  it("returns undefined when no URL is present", () => {
    expect(extractShareUrl("只有普通文字")).toBeUndefined();
  });
});

describe("matchCodexKeywords", () => {
  it("matches keywords without case sensitivity", () => {
    expect(matchCodexKeywords("Codex quota RESET", ["quota", "reset", "limit"]))
      .toEqual(["quota", "reset"]);
  });
});
