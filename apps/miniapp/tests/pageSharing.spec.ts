import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

interface PageDefinition {
  path: string;
  style?: {
    enableShareAppMessage?: boolean;
    enableShareTimeline?: boolean;
  };
}

interface PagesConfig {
  pages: PageDefinition[];
}

const pagesJsonPath = fileURLToPath(new URL("../src/pages.json", import.meta.url));
const pagesConfig = JSON.parse(readFileSync(pagesJsonPath, "utf8")) as PagesConfig;
const pageSharePath = fileURLToPath(
  new URL("../src/composables/usePageShare.ts", import.meta.url),
);
const appPath = fileURLToPath(new URL("../src/App.vue", import.meta.url));

describe("page sharing", () => {
  it("shows both WeChat share menus with share tickets enabled", () => {
    const pageShareSource = readFileSync(pageSharePath, "utf8");
    const appSource = readFileSync(appPath, "utf8");
    expect(pageShareSource).toContain("withShareTicket: true");
    expect(pageShareSource).toContain(
      'menus: ["shareAppMessage", "shareTimeline"]',
    );
    expect(appSource).toContain("uni.showShareMenu({");
    expect(appSource).toContain("withShareTicket: true");
    expect(appSource).toContain(
      'menus: ["shareAppMessage", "shareTimeline"]',
    );
  });

  it("enables friend and timeline sharing on every page", () => {
    for (const page of pagesConfig.pages) {
      expect(page.style?.enableShareAppMessage, page.path).toBe(true);
      expect(page.style?.enableShareTimeline, page.path).toBe(true);

      const pageSourcePath = fileURLToPath(
        new URL(`../src/${page.path}.vue`, import.meta.url),
      );
      const pageSource = readFileSync(pageSourcePath, "utf8");
      expect(pageSource, page.path).toContain("createPageShare({");
      expect(pageSource, page.path).toContain("onShareAppMessage(");
      expect(pageSource, page.path).toContain("onShareTimeline(");
    }
  });
});
