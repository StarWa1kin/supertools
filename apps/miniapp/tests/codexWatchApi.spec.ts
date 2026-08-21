import { afterEach, describe, expect, it, vi } from "vitest";

import { getCodexWatchConfig } from "../src/api/codexWatch";

describe("Codex watch public config API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps tutorials and community from the public config endpoint", async () => {
    const request = vi.fn((options: UniApp.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          tutorials: [{
            id: "tutorial-1",
            title: "Codex 快速上手",
            description: "从第一次任务开始",
            url: "https://example.com/codex",
          }],
          community: {
            title: "AI 技术交流群",
            description: "交流 AI 实战",
            qrCode: "data:image/png;base64,qr",
          },
        },
        header: {},
        cookies: [],
        errMsg: "request:ok",
      });
    });
    vi.stubGlobal("uni", { request });

    const result = await getCodexWatchConfig();

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: "http://127.0.0.1:8000/api/v1/codex-watch/config",
      method: "GET",
    }));
    expect(result.tutorials[0].title).toBe("Codex 快速上手");
    expect(result.community?.qrCode).toBe("data:image/png;base64,qr");
  });

  it("surfaces config request failures", async () => {
    const request = vi.fn((options: UniApp.RequestOptions) => {
      options.fail?.({ errMsg: "request:fail" });
    });
    vi.stubGlobal("uni", { request });

    await expect(getCodexWatchConfig()).rejects.toThrow("request:fail");
  });
});
