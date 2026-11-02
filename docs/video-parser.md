# 视频解析接口

## 本地接入 media-parser

服务端不再内置平台解析逻辑，所有分享链接都转交独立的 media-parser 服务解析。
小程序继续使用本项目的 `/api/v1/video-parser/resolve` 和 `/media`。
FastAPI 将上游结果转换为既有字段，并继续对媒体地址校验、签名和中转。
不会将 API Key 下发给小程序；上游失败时直接返回错误。

在 `apps/server/.env` 中设置：

```dotenv
MEDIA_PARSER_BASE_URL=http://127.0.0.1:8051
MEDIA_PARSER_API_KEY=
MEDIA_PARSER_TIMEOUT_SECONDS=95
```

在仓库根目录另开终端启动同级目录的解析项目：

```bash
sh scripts/dev-media-parser.sh
```

该脚本使用 `../media-parser/.venv/bin/python`，仅在本次进程中启用
`API_ONLY=true`，监听 `127.0.0.1:8051`，不修改上游项目的配置或代码。
已有 8051 服务时不要重复启动；如已有服务开启鉴权，在 FastAPI 的
`MEDIA_PARSER_API_KEY` 中填写对应 Key。还可用 `MEDIA_PARSER_PROJECT_DIR`、
`MEDIA_PARSER_PYTHON`、`MEDIA_PARSER_PORT` 自定义启动路径和端口；变更端口时同步修改基础地址。

随后启动或重启 FastAPI 和 H5 开发服务。本地小程序开发配置使用
`apps/miniapp/.env.development.local` 中的 `VITE_API_BASE_URL=http://127.0.0.1:8000`，
不影响生产构建。真机调试需换成电脑可访问的局域网地址，并配置相应调试域名。
解析请求单独等待 120 秒，其余 API 仍默认 30 秒。

本项目不维护分享平台白名单，由上游识别平台并判断是否支持。
抖音、快手、小红书继续返回 `douyin`、`kuaishou`、`xiaohongshu`；其他平台保留上游名称，
前端和本地历史记录接受这些平台字段。
此配置不保证上游一定支持视频号等特定平台，平台规则及内容可访问性仍由上游决定。

视频列表去重后转换为视频资源；没有视频时使用图片列表，
兼容字符串和对象形式的图片；暂不展示 Live Photo 附带视频、音频及字幕。
上游未提供作品时长与最终页面地址，分别保留空值和用户提交的分享地址。
上游返回预览片段或登录校验时按内容不可访问处理。
上游只使用匿名公开内容，勿为本工具配置平台登录 Cookie 或动态代理绕过逻辑。

分享链接仍校验 HTTP/HTTPS、凭据、端口及私网 IP；启用 `VIDEO_PARSER_RESOLVE_DNS` 时，
转交上游前还会检查入口域名的公网 DNS。上游自身也需逐跳校验其内部发起的请求。
只有上游返回并通过地址检查的媒体才能取得本项目签名，不再使用 CDN 域名白名单，
封面和头像同理。中转仍验证签名、地址及重定向，按配置检查公网 DNS，并限制类型、大小及超时。

Docker 部署时需在 `.env.production` 中显式设置 `MEDIA_PARSER_BASE_URL`
（如 `http://host.docker.internal:8051` 或解析容器服务名），
不要使用指向 API 容器自身的 `127.0.0.1`。

## 解析公开内容

`POST /api/v1/video-parser/resolve`

```json
{
  "url": "https://v.douyin.com/example"
}
```

支持的平台范围由 media-parser 决定。
响应中的 `mediaType` 为 `video` 或 `images`，每个 `assets` 项包含原始平台地址、同源预览路径和下载路径：

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
- 服务端校验媒体签名与地址，按配置逐跳检查公网 DNS，不接受调用方提供任意未签名 URL。
- 只接收解析服务返回并签名的媒体地址。
- 媒体若跳转到动态 CDN，服务端验证 HTTPS、地址及按配置检查公网 DNS 后继续中转，不将原始跳转暴露给客户端。
- 视频默认上限 200 MB，图片默认上限 20 MB；流式响应结束后不会保留文件。

## 部署配置

- 复制 `apps/server/.env.example` 并设置随机的 `VIDEO_MEDIA_SIGNING_SECRET`。生产环境禁止使用开发默认值。
- 设置 `MEDIA_PARSER_BASE_URL` 与 `MEDIA_PARSER_API_KEY`，指向生产可访问的 media-parser 服务。
- `APP_CORS_ORIGINS` 只填写实际 H5 来源，不使用通配符。
- 微信公众平台需将自有 HTTPS API 域名加入 request、downloadFile 和媒体访问域名。小程序不需要直接放行平台动态 CDN。
- 上游解析器只使用匿名公开页面，不配置或转发用户 Cookie。

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

解析测试通过 mock 的 media-parser 响应进行，不应在自动测试中访问实时平台或上游服务。
