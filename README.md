# Supertools

面向微信小程序的轻量工具集合。前端基于 UniApp、Vue 3、TypeScript 和 UnoCSS，服务端基于 Python、FastAPI 与 Pydantic。

## 项目结构

```text
apps/
  admin/    # Codex 情报管理端
  miniapp/  # 微信小程序与 H5 前端
  server/   # FastAPI 服务
docs/       # 接口与架构文档
```

首期包含 Codex 额度情报监控和公开视频链接解析两个工具。视频解析已经支持抖音、快手和小红书的公开视频及图文内容，并通过受控流式中转向小程序提供预览和相册保存能力。

## 本地开发

```bash
pnpm install
pnpm dev:admin
pnpm dev:h5
pnpm dev:miniapp
```

后端需要先安装 [uv](https://docs.astral.sh/uv/)，然后执行：

```bash
cd apps/server
uv sync --dev
uv run fastapi dev
```

API 文档位于 `http://127.0.0.1:8000/docs`。复制前后端 `.env.example` 为 `.env` 后再修改本地配置，禁止提交真实密钥。

Codex 情报管理端默认位于 `http://127.0.0.1:5174`，开发账号为 `admin`、密码为 `come2u`。部署前必须通过 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 和 `ADMIN_TOKEN_SECRET` 更换默认凭据。

视频解析接口及生产配置说明见 [`docs/video-parser.md`](docs/video-parser.md)。正式微信小程序需要将自有 HTTPS API 域名加入 request、downloadFile 和媒体访问域名配置；生产环境必须替换 `VIDEO_MEDIA_SIGNING_SECRET`。

## Docker 服务器部署

仓库已提供 `docker-compose.yml`，用于部署 Python API 和管理端。复制 `.env.production.example` 为服务器上的 `.env.production`，替换生产密钥后执行：

```bash
docker compose --env-file .env.production build --pull
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
```

Python API 默认仅绑定宿主机 `127.0.0.1:8000`，管理端默认仅绑定 `127.0.0.1:8080`，分别由 `api.devhooks.cn` 和 `admin.devhooks.cn` 的宿主机 Nginx 反向代理。HTTPS、小程序 API 配置、更新和备份步骤见 [`docs/deployment.md`](docs/deployment.md)。小程序代码不包含在服务器 Compose 部署中。
