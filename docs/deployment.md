# 服务器部署

本项目的服务器部分由两个 Docker 服务组成：

- `server`：Python 3.12 + FastAPI，仅绑定宿主机 `127.0.0.1:8000`，由 `api.devhooks.cn` 反向代理。
- `admin`：Vue 管理端的生产构建，由容器内 Nginx 提供静态文件，仅绑定宿主机 `127.0.0.1:8080`，由 `admin.devhooks.cn` 反向代理。

小程序不在服务器上构建。小程序开发者工具继续使用自己的构建和上传流程，接口基地址使用 `https://api.devhooks.cn`；请求封装会自行拼接 `/api/v1/...`。

## 首次部署

服务器要求：Linux、Docker Engine 24+ 和 Docker Compose v2。以下示例使用 `/opt/supertools` 作为部署目录。

```bash
sudo mkdir -p /opt/supertools
sudo chown "$USER":"$USER" /opt/supertools
cd /opt/supertools
git clone <你的仓库地址> .
cp .env.production.example .env.production
nano .env.production
```

必须修改 `ADMIN_PASSWORD`、`ADMIN_TOKEN_SECRET`、`REMINDER_SECRET_ENCRYPTION_KEY` 和 `VIDEO_MEDIA_SIGNING_SECRET`。`REMINDER_SECRET_ENCRYPTION_KEY` 用于加密数据卷中保存的微信 AppSecret，必须是独立的长随机值，且后续不得随意更换；更换后将无法解密既有配置。`APP_CORS_ORIGINS` 需要包含 `https://admin.devhooks.cn`。不要把 `.env.production` 提交到 Git。

### 出站代理（可选）

若服务器无法直连 Cloudflare 或视频平台，可在宿主机运行 Mihomo/Clash，并在 `.env.production` 增加：

```ini
HTTP_PROXY=http://host.docker.internal:7890
HTTPS_PROXY=http://host.docker.internal:7890
NO_PROXY=localhost,127.0.0.1,api.weixin.qq.com
```

`server` 容器会将 `host.docker.internal` 映射到 Docker 宿主机；不要填写 `127.0.0.1:7890`，它在容器中指向当前容器自身。微信 API 应保留在 `NO_PROXY` 中直连，避免部分代理提前断开 HTTPS 连接。Python 的 HTTP 客户端会自动读取这些标准环境变量，Admin 的隔离构建容器也会继承它们。修改后重新创建 API 容器：

```bash
docker compose --env-file .env.production up -d --force-recreate server
docker compose --env-file .env.production exec server python -c "import httpx; print(httpx.get('https://codex-reset.com', timeout=10).status_code)"
```

启动并检查：

```bash
docker compose --env-file .env.production build --pull
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
docker compose --env-file .env.production logs -f --tail=100 server admin
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:8080/
```

API 和管理端默认仅监听服务器回环地址。将 `infra/nginx/sites/supertools.conf` 安装到宿主机 Nginx 后，为 `api.devhooks.cn` 和 `admin.devhooks.cn` 签发 HTTPS 证书。不要把 8000 或 8080 端口直接暴露到公网。

仓库中的 Nginx 配置默认读取 `/etc/nginx/ssl/wildcard.devhooks.cn.pem` 和 `/etc/nginx/ssl/wildcard.devhooks.cn.key`。证书必须覆盖 `*.devhooks.cn`；如果服务器使用其他证书路径，需要同步修改配置。安装配置后先执行 `nginx -t`，成功后再 reload。

### 旧宿主机的管理端构建兼容

Admin Dockerfile 会在临时内存文件系统中安装依赖和构建静态文件，避免部分 CentOS 7/旧 overlay 文件系统中的 `EPERM` 或 SQLite `disk I/O error`。因此仍使用标准 Compose 命令即可。若配置了 `HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY`，这些变量也会自动传入 Admin 构建阶段，用于下载 npm 依赖。

`dist/` 是部署产物，不应提交到仓库。

## 更新与回滚

```bash
cd /opt/supertools
git pull --ff-only
docker compose --env-file .env.production build --pull
docker compose --env-file .env.production up -d --remove-orphans
docker compose --env-file .env.production ps
```

升级前可先备份配置数据卷：

```bash
docker run --rm -v supertools-data:/data -v "$PWD":/backup alpine \
  tar czf /backup/supertools-data-$(date +%Y%m%d-%H%M%S).tgz -C /data .
```

数据只包含 Codex 监控配置，位于 Docker 卷 `supertools-data`。查看镜像和日志：

```bash
docker compose --env-file .env.production images
docker compose --env-file .env.production logs --since=30m server
docker compose --env-file .env.production down   # 仅停止服务，不删除数据卷
```

## 域名与小程序

HTTPS 代理配置完成后，管理端地址为 `https://admin.devhooks.cn/`，接口健康检查为 `https://api.devhooks.cn/health`，接口文档为 `https://api.devhooks.cn/docs`（如需开放文档，请在外层代理配置访问控制）。小程序中的 `VITE_API_BASE_URL` 应设置为 `https://api.devhooks.cn`，并在微信公众平台配置 request、downloadFile 和媒体访问域名。

管理端和 API 使用不同域名，因此 `.env.production` 中的 `VITE_API_BASE_URL` 必须保持为 `https://api.devhooks.cn`，`APP_CORS_ORIGINS` 必须包含 `https://admin.devhooks.cn`。

## 安全检查

- 服务器防火墙只开放 80/443（以及必要的 SSH），不开放 8000。
- 使用 HTTPS，不在生产环境使用示例密码或示例密钥。
- 定期备份 `supertools-data` 卷和 `.env.production`（密钥文件应使用受控的密码管理或备份系统）。
- 日志中不应出现管理员密码、令牌或完整用户分享链接。
