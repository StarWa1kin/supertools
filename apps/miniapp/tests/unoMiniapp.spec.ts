import { createPresets, resolveOptions } from "@uni-helper/unocss-preset-uni";
import { createGenerator, type Preset } from "unocss";
import { describe, expect, it } from "vitest";

describe("UnoCSS mini-program output", () => {
  it("encodes class-name characters unsupported by WXSS", async () => {
    const profile = { isMp: true, platform: "mp-weixin" as const };
    const options = resolveOptions({ attributify: false }, profile);
    const uno = await createGenerator({
      presets: createPresets(options, profile) as Preset[],
    });

    const { css } = await uno.generate("w-2/5 w-3/4");

    expect(css).toContain(".w-2_a_5");
    expect(css).toContain(".w-3_a_4");
    expect(css).not.toContain("\\");
  });
});
