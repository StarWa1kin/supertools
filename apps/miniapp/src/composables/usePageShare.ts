type ShareText = string | (() => string);

interface PageShareOptions {
  title: ShareText;
  path: ShareText;
  imageUrl?: ShareText;
}

function resolveText(value: ShareText) {
  return typeof value === "function" ? value() : value;
}

function timelineQuery(path: string) {
  const queryStart = path.indexOf("?");
  return queryStart === -1 ? "" : path.slice(queryStart + 1);
}

/** Build callbacks that pages register directly so UniApp can detect native hooks. */
export function createPageShare(options: PageShareOptions) {
  function showShareMenu() {
    // #ifdef MP-WEIXIN
    uni.showShareMenu({
      withShareTicket: true,
      menus: ["shareAppMessage", "shareTimeline"],
    });
    // #endif
  }

  function shareAppMessage() {
    const imageUrl = options.imageUrl
      ? resolveText(options.imageUrl)
      : undefined;

    return {
      title: resolveText(options.title),
      path: resolveText(options.path),
      ...(imageUrl ? { imageUrl } : {}),
    };
  }

  function shareTimeline() {
    const path = resolveText(options.path);
    const imageUrl = options.imageUrl
      ? resolveText(options.imageUrl)
      : undefined;

    return {
      title: resolveText(options.title),
      query: timelineQuery(path),
      ...(imageUrl ? { imageUrl } : {}),
    };
  }

  return { showShareMenu, shareAppMessage, shareTimeline };
}
