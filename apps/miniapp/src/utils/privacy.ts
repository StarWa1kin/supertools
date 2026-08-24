interface PrivacyApi {
  getPrivacySetting?: (options: {
    success: (result: { needAuthorization: boolean }) => void;
    fail: () => void;
  }) => void;
  requirePrivacyAuthorize?: (options: {
    success: () => void;
    fail: (reason: unknown) => void;
  }) => void;
}

export function ensurePrivacyAuthorization() {
  const privacyApi = uni as unknown as PrivacyApi;
  if (!privacyApi.getPrivacySetting || !privacyApi.requirePrivacyAuthorize) {
    return Promise.resolve();
  }

  return new Promise<void>((resolve, reject) => {
    privacyApi.getPrivacySetting?.({
      success(setting) {
        if (!setting.needAuthorization) {
          resolve();
          return;
        }
        privacyApi.requirePrivacyAuthorize?.({ success: resolve, fail: reject });
      },
      fail: resolve,
    });
  });
}
