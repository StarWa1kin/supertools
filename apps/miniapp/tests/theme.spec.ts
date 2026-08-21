import { describe, expect, it } from "vitest";

import { resolveThemeName, themeOptions } from "../src/composables/useTheme";

describe("theme configuration", () => {
  it("provides the original, blue and dark themes", () => {
    expect(themeOptions.map((option) => option.name)).toEqual([
      "classic",
      "blue",
      "dark",
    ]);
  });

  it("falls back to the classic theme for invalid stored values", () => {
    expect(resolveThemeName("unknown")).toBe("classic");
    expect(resolveThemeName(undefined)).toBe("classic");
  });
});
