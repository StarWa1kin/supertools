const platformHosts = {
  douyin: ["douyin.com", "iesdouyin.com"],
  kuaishou: ["kuaishou.com", "kuaishoup.com", "gifshow.com"],
  xiaohongshu: ["xiaohongshu.com", "xhslink.com", "xhslink.cn"],
} as const;

export type VideoPlatform = keyof typeof platformHosts;

export function extractShareUrl(value: string): string | undefined {
  const match = value.match(/https?:\/\/[^\s<>"'，。！？、；：]+/iu);
  if (!match) {
    return undefined;
  }
  return match[0].replace(/[，。！？、；：)\]}]+$/u, "");
}

function extractHttpHostname(value: string): string | undefined {
  const authority = value.match(/^https?:\/\/([^/?#]+)/i)?.[1];
  if (!authority || authority.includes("@") || authority.startsWith("[")) {
    return undefined;
  }

  const hostname = authority
    .replace(/:\d+$/, "")
    .toLowerCase()
    .replace(/\.$/, "");
  return hostname && !hostname.includes(":") ? hostname : undefined;
}

export function detectVideoPlatform(value: string): VideoPlatform | undefined {
  const candidate = extractShareUrl(value) || value.trim();
  const hostname = extractHttpHostname(candidate);
  if (!hostname) {
    return undefined;
  }

  return (Object.keys(platformHosts) as VideoPlatform[]).find((platform) =>
    platformHosts[platform].some(
      (allowed) => hostname === allowed || hostname.endsWith(`.${allowed}`),
    ),
  );
}

export function matchCodexKeywords(text: string, keywords: string[]) {
  const normalized = text.toLocaleLowerCase();
  return keywords.filter((keyword) => normalized.includes(keyword.toLocaleLowerCase()));
}
