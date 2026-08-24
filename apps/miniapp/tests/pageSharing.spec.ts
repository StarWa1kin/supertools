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

describe("page sharing", () => {
  it("enables friend and timeline sharing on every page", () => {
    for (const page of pagesConfig.pages) {
      expect(page.style?.enableShareAppMessage, page.path).toBe(true);
      expect(page.style?.enableShareTimeline, page.path).toBe(true);
    }
  });
});
