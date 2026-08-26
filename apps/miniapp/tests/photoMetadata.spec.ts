import { describe, expect, it } from "vitest";

import {
  formatCoordinates,
  formatExifDate,
  formatShutterSpeed,
  normalizeExif,
} from "../src/composables/photoMetadata";

describe("photo EXIF metadata", () => {
  it("formats the metadata used by the camera-strip template", () => {
    expect(
      normalizeExif({
        Make: "Apple",
        Model: "iPhone 17 Pro",
        DateTimeOriginal: "2026:01:01 18:49:31",
        FocalLength: 24,
        FNumber: 1.8,
        ExposureTime: 1 / 60,
        ISOSpeedRatings: 200,
        latitude: 48 + 20 / 60 + 22 / 3600,
        longitude: 86 + 44 / 60 + 27 / 3600,
      }),
    ).toMatchObject({
      model: "iPhone 17 Pro",
      capturedAt: "2026.01.01 18:49:31",
      focalLength: "24mm",
      aperture: "f/1.8",
      shutter: "1/60",
      iso: "ISO200",
      location: `48°20'22"N 86°44'27"E`,
    });
  });

  it("handles missing metadata without inventing values", () => {
    expect(normalizeExif({})).toBeNull();
    expect(formatCoordinates(undefined, 120)).toBe("");
    expect(formatExifDate(undefined)).toBe("");
    expect(formatShutterSpeed(2)).toBe("2s");
  });
});
