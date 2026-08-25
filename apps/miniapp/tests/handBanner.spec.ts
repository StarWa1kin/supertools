import { beforeEach, describe, expect, it, vi } from "vitest";

import { useHandBanner } from "../src/composables/handBanner";

const getStorageSync = vi.fn();
const setStorageSync = vi.fn();

describe("hand banner", () => {
  beforeEach(() => {
    getStorageSync.mockReset();
    setStorageSync.mockReset();
    vi.stubGlobal("uni", { getStorageSync, setStorageSync });
  });

  it("keeps an explicitly cleared message empty", () => {
    const { message, save } = useHandBanner();

    message.value = "需要清空的内容";
    expect(save("")).toBe("");
    expect(message.value).toBe("");
    expect(setStorageSync).toHaveBeenCalledWith(
      "supertools.hand-banner.settings",
      expect.objectContaining({ message: "" }),
    );
  });

  it("restores a previously cleared message as empty", () => {
    getStorageSync.mockReturnValue({
      message: "",
      textColor: "#ffffff",
      fontScale: 1,
    });
    const { message, restore } = useHandBanner();

    message.value = "旧内容";
    restore();

    expect(message.value).toBe("");
  });
});
