import { describe, expect, it } from "vitest";

import type { WatchPost } from "../src/api/codexWatch";
import {
  buildWatchConclusion,
  buildReminderState,
  formatBriefDate,
  selectLatestPosts,
} from "../src/composables/useCodexWatch";

const basePost: WatchPost = {
  id: "post-1",
  text: "Codex quota reset update",
  url: "https://example.com/post-1",
  publishedAt: "2026-08-18T10:00:00Z",
  confidence: "third_party",
  matchedKeywords: ["quota", "reset"],
};

describe("Codex watch brief", () => {
  it("shows a clear result when no signals were found", () => {
    expect(buildWatchConclusion([]).kind).toBe("clear");
    expect(buildWatchConclusion([]).answer).toBe("暂未");
  });

  it("does not present third-party signals as official confirmation", () => {
    const conclusion = buildWatchConclusion([basePost]);

    expect(conclusion.kind).toBe("signal");
    expect(conclusion.answer).toBe("有信号");
  });

  it("prioritizes an official signal", () => {
    const officialPost = { ...basePost, id: "post-2", confidence: "official" as const };

    expect(buildWatchConclusion([basePost, officialPost]).kind).toBe("confirmed");
  });

  it("does not treat an old reset as today's confirmation when forecast is present", () => {
    const officialPost = { ...basePost, confidence: "official" as const };
    const forecast = {
      updatedAt: "2026-08-19T12:00:00Z",
      lastResetAt: "2026-08-13T01:00:00Z",
      probability24h: 30,
      probability48h: 50,
      confidence: "medium" as const,
      commonWindow: "11 PM - 2 AM",
      recentMedianDays: 2.3,
      weightedMeanDays: 5.7,
      accelerating: true,
      ageDays: 6.7,
      recentSample: 5,
      verifiedResetCount: 35,
      allTimeMedianDays: 3.8,
      recent30dMedianDays: 3.6,
      longestWaitDays: 73,
      modelVersion: "rate-v3",
    };

    expect(buildWatchConclusion(
      [officialPost],
      "",
      forecast,
      new Date("2026-08-19T18:00:00Z"),
    ).kind).toBe("signal");
  });

  it("marks failed scans as unknown", () => {
    expect(buildWatchConclusion([], "network error").answer).toBe("未知");
  });

  it("formats the daily poster date", () => {
    expect(formatBriefDate(new Date(2026, 7, 18))).toBe("2026.08.18");
  });

  it("keeps only the three newest Tibo posts", () => {
    const posts = [
      { ...basePost, id: "oldest", publishedAt: "2026-08-15T10:00:00Z" },
      { ...basePost, id: "newest", publishedAt: "2026-08-18T10:00:00Z" },
      { ...basePost, id: "second", publishedAt: "2026-08-17T10:00:00Z" },
      { ...basePost, id: "third", publishedAt: "2026-08-16T10:00:00Z" },
    ];

    expect(selectLatestPosts(posts).map((post) => post.id)).toEqual([
      "newest",
      "second",
      "third",
    ]);
  });

  it("enables subscriptions whenever the backend service is configured", () => {
    expect(buildReminderState(true, "template-1").available).toBe(true);
    expect(buildReminderState(true, "").available).toBe(false);
    expect(buildReminderState(false, "template-1").available).toBe(false);
  });

});
