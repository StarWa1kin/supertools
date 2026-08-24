import { describe, expect, it } from "vitest";

import {
  defaultBorderWatermarkSettings,
  formatParameterLine,
  sanitizeBorderWatermarkSettings,
} from "../src/composables/borderWatermark";
import {
  brandLogoPacks,
  framePresets,
  getBrandLogo,
  getFramePreset,
} from "../src/config/borderWatermark";

describe("border watermark settings", () => {
  it("ships the requested brand logo packs", () => {
    expect(brandLogoPacks.map((brand) => brand.id)).toEqual(
      expect.arrayContaining(["apple", "canon", "sony"]),
    );
    expect(brandLogoPacks.filter((brand) => brand.asset)).toHaveLength(3);
  });

  it("keeps frame and brand lookups on a safe default", () => {
    expect(getFramePreset("missing" as never).id).toBe(framePresets[0].id);
    expect(getBrandLogo("missing" as never).id).toBe(brandLogoPacks[0].id);
  });

  it("sanitizes stored values and clamps visual controls", () => {
    expect(
      sanitizeBorderWatermarkSettings({
        presetId: "missing" as never,
        brandId: "missing" as never,
        framePercent: 99,
        cornerRadius: -8,
        signature: "  MY   STUDIO\n2026  ",
        model: "",
        showParameters: false,
      }),
    ).toMatchObject({
      presetId: "gallery",
      brandId: "apple",
      framePercent: 18,
      cornerRadius: 0,
      signature: "MY STUDIO 2026",
      model: defaultBorderWatermarkSettings.model,
      showParameters: false,
    });
  });

  it("builds a compact camera parameter line", () => {
    expect(formatParameterLine(defaultBorderWatermarkSettings)).toBe(
      "28mm · ƒ/2.4 · 1/100s · ISO 200",
    );
    expect(
      formatParameterLine({
        ...defaultBorderWatermarkSettings,
        showParameters: false,
      }),
    ).toBe("");
  });
});
