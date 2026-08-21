const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

interface ApiErrorBody {
  detail?:
    | string
    | {
        code?: string;
        message?: string;
      };
}

export class ApiRequestError extends Error {
  code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
  }
}

export function resolveApiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  return `${apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

export function request<T>(options: UniApp.RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      url: resolveApiUrl(options.url),
      timeout: 30_000,
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data as T);
          return;
        }

        const body = response.data as ApiErrorBody | undefined;
        const detail = body?.detail;
        if (typeof detail === "string") {
          reject(new ApiRequestError(detail));
          return;
        }
        reject(
          new ApiRequestError(
            detail?.message || `请求失败（${response.statusCode}）`,
            detail?.code,
          ),
        );
      },
      fail(reason) {
        reject(
          new ApiRequestError(reason.errMsg || "网络连接失败", "network_error"),
        );
      },
    });
  });
}
