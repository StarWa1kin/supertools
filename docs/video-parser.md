# 视频解析接口

## 解析公开内容

`POST /api/v1/video-parser/resolve`

```json
{
  "url": "https://v.douyin.com/example"
}
```

接口支持抖音、快手和小红书公开分享链接。响应中的 `mediaType` 为 `video` 或 `images`，每个 `assets` 项包含原始平台地址、同源预览路径和下载路径：

```json
{
  "platform": "douyin",
  "mediaType": "video",
  "canonicalUrl": "https://www.douyin.com/video/123",
  "title": "公开视频标题",
  "author": {
    "name": "作者",
    "avatarUrl": "/api/v1/video-parser/media?token=..."
  },
  "durationMs": 12000,
  "coverUrl": "/api/v1/video-parser/media?token=...",
  "assets": [
    {
      "kind": "video",
      "sourceUrl": "https://platform-cdn.example/video.mp4",
      "previewPath": "/api/v1/video-parser/media?token=...",
      "downloadPath": "/api/v1/video-parser/media?token=...&download=true"
    }
  ]
}
```

错误响应通过 HTTP 状态码和 `detail.code` 区分无效链接、内容不可访问、上游超时、页面结构变化、媒体过大及令牌失效。客户端应显示 `detail.message`，不要依赖平台原始错误文本。

## 媒体中转

`GET /api/v1/video-parser/media?token=...&download=false`

- `token` 只能由解析接口签发，默认 15 分钟过期，篡改后无效。
- `download=true` 时返回下载响应；默认以内联方式响应，支持标准单段 Range 请求。
- 服务端逐跳验证媒体 CDN 域名和公网 DNS，不接受调用方提供任意 URL。
- 白名单 CDN 若跳转到动态终点域名，服务端验证 HTTPS 与公网 DNS 后向客户端返回 307，不会代表客户端连接未知域名。
- 视频默认上限 200 MB，图片默认上限 20 MB；流式响应结束后不会保留文件。

## 部署配置

- 复制 `apps/server/.env.example` 并设置随机的 `VIDEO_MEDIA_SIGNING_SECRET`。生产环境禁止使用开发默认值。
- `VIDEO_MEDIA_ALLOWED_HOSTS` 是媒体 CDN 域名后缀白名单。平台更换 CDN 时先验证域名归属，再更新配置。
- `APP_CORS_ORIGINS` 只填写实际 H5 来源，不使用通配符。
- 微信公众平台需将自有 HTTPS API 域名加入 request、downloadFile 和媒体访问域名。小程序不需要直接放行平台动态 CDN。
- 解析器只使用匿名公开页面，不配置或转发用户 Cookie。

## 验证

```bash
cd apps/server
uv run pytest
uv run ruff check .
uv run ruff format --check .

pnpm --dir apps/miniapp check
pnpm --dir apps/miniapp build:h5
pnpm --dir apps/miniapp build:mp-weixin
```

平台测试使用 `apps/server/tests/fixtures/` 内的脱敏快照，不应在自动测试中访问实时平台。
