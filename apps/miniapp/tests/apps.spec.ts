import { describe, expect, it } from "vitest";

import {
  getEnabledApps,
  getFeaturedApps,
  isAppAvailable,
  toolApps,
  type ToolApp,
} from "../src/config/apps";

describe("tool app registry", () => {
  it("keeps ids and routes unique", () => {
    expect(new Set(toolApps.map((app) => app.id)).size).toBe(toolApps.length);
    expect(new Set(toolApps.map((app) => app.route)).size).toBe(toolApps.length);
  });

  it("shows only enabled featured apps on the home page", () => {
    const fixtures: ToolApp[] = [
      { ...toolApps[0], id: "later", order: 20, enabled: true, featured: true },
      { ...toolApps[0], id: "hidden", order: 5, enabled: false, featured: true },
      { ...toolApps[0], id: "first", order: 10, enabled: true, featured: true },
      { ...toolApps[0], id: "library-only", order: 1, enabled: true, featured: false },
    ];

    expect(getFeaturedApps(fixtures).map((app) => app.id)).toEqual(["first", "later"]);
    expect(getEnabledApps(fixtures).map((app) => app.id)).toEqual([
      "library-only",
      "first",
      "later",
    ]);
  });

  it("keeps internal apps usable in development but locks them in production", () => {
    const internalApp: ToolApp = {
      ...toolApps[0],
      releaseStage: "internal",
    };

    expect(isAppAvailable(internalApp, false)).toBe(true);
    expect(isAppAvailable(internalApp, true)).toBe(false);
    expect(isAppAvailable({ ...internalApp, enabled: false }, false)).toBe(false);
  });
});
