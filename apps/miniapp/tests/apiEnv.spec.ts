import { describe, expect, it } from "vitest";

import {
  createApiEnvPresets,
  describeApiBaseUrl,
  normalizeBaseUrl,
  resolveApiBaseUrl,
} from "../src/config/apiEnv";

const presets = createApiEnvPresets({
  VITE_API_LOCAL_URL: "http://127.0.0.1:8000/",
  VITE_API_LAN_URL: "",
  VITE_API_REMOTE_URL: "https://api.example.com",
});

describe("api environment presets", () => {
  it("keeps only configured presets and strips trailing slashes", () => {
    expect(presets).toEqual([
      { id: "local", label: "本地", baseUrl: "http://127.0.0.1:8000" },
      { id: "remote", label: "线上", baseUrl: "https://api.example.com" },
    ]);
  });

  it("rejects values that are not http(s) base URLs", () => {
    expect(normalizeBaseUrl("api.example.com")).toBe("");
    expect(normalizeBaseUrl("javascript:alert(1)")).toBe("");
    expect(normalizeBaseUrl(undefined)).toBe("");
    expect(normalizeBaseUrl(" https://api.example.com// ")).toBe(
      "https://api.example.com",
    );
  });
});

describe("resolveApiBaseUrl", () => {
  const buildBaseUrl = "https://api.example.com";

  it("uses the stored preset in switchable builds", () => {
    expect(
      resolveApiBaseUrl({
        buildBaseUrl,
        overrideId: "local",
        switchable: true,
        presets,
      }),
    ).toBe("http://127.0.0.1:8000");
  });

  it("ignores the stored preset in release builds", () => {
    expect(
      resolveApiBaseUrl({
        buildBaseUrl,
        overrideId: "local",
        switchable: false,
        presets,
      }),
    ).toBe(buildBaseUrl);
  });

  it("falls back to the build URL for unknown or unconfigured presets", () => {
    for (const overrideId of ["lan", "http://evil.example", 42, undefined]) {
      expect(
        resolveApiBaseUrl({ buildBaseUrl, overrideId, switchable: true, presets }),
      ).toBe(buildBaseUrl);
    }
  });
});

describe("describeApiBaseUrl", () => {
  it("labels known presets and shows only the host", () => {
    expect(describeApiBaseUrl("http://127.0.0.1:8000", presets)).toBe(
      "本地 127.0.0.1:8000",
    );
    expect(describeApiBaseUrl("http://10.0.0.2:8000", presets)).toBe(
      "10.0.0.2:8000",
    );
    expect(describeApiBaseUrl("", presets)).toBe("未配置");
  });
});
