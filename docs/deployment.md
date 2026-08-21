# 服务器部署

本项目的服务器部分由两个 Docker 服务组成：

- `server`：Python 3.12 + FastAPI，仅绑定宿主机 `127.0.0.1:8000`，由 `api.devhooks.cn` 反向代理。
- `admin`：Vue 管理端的生产构建，由容器内 Nginx 提供静态文件，仅绑定宿主机 `127.0.0.1:8080`，由 `admin.devhooks.cn` 反向代理。
- `deployer`：仅在 Compose 内网提供部署控制，挂载仓库和 Docker socket，供登录后的管理端触发固定发布流程。

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

必须修改 `ADMIN_PASSWORD`、`ADMIN_TOKEN_SECRET`、`DEPLOY_SERVICE_TOKEN` 和 `VIDEO_MEDIA_SIGNING_SECRET`。`DEPLOY_SERVICE_TOKEN` 建议使用独立的 32 字节以上随机值，不能与管理员令牌密钥复用。私有 SSH 仓库还需将 `DEPLOY_SSH_DIR` 指向宿主机部署账号的 `.ssh` 目录，其中应包含只读部署密钥和 `known_hosts`。`APP_CORS_ORIGINS` 需要包含 `https://admin.devhooks.cn`。不要把 `.env.production` 提交到 Git。

### 出站代理（可选）

若服务器无法直连 Cloudflare 或视频平台，可在宿主机运行 Mihomo/Clash，并在 `.env.production` 增加：

```ini
HTTP_PROXY=http://host.docker.internal:7890
HTTPS_PROXY=http://host.docker.internal:7890
NO_PROXY=localhost,127.0.0.1,deployer
```

`server` 容器已将 `host.docker.internal` 映射到 Docker 宿主机；不要填写 `127.0.0.1:7890`，它在容器中指向 API 容器自身。Python 的 HTTP 客户端会自动读取这些标准环境变量。修改后重新创建 API 容器：

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

首次启用管理端一键部署，或者从不包含 `deployer` 的旧版本升级时，必须先在服务器执行一次完整引导。尚未运行的部署器无法自行完成这个步骤：

```bash
git pull --ff-only
docker compose --env-file .env.production build server admin deployer
docker compose --env-file .env.production up -d --remove-orphans
docker compose --env-file .env.production ps
```

确认 `server`、`admin` 和 `deployer` 都为 running/healthy 后，管理端可分别点击“部署 Server”或“部署 Admin”。两种操作都会固定执行 `git pull --ff-only`，但只构建、更新并健康检查所选服务。管理端构建会在临时内存文件系统中从当前源码重新构建，以避开部分宿主机 Docker 存储层的写入限制；若构建失败，部署任务会明确失败，不会回退发布仓库中的旧静态产物。部署器不映射宿主机端口，且不会接受管理端传入的自定义命令。

部署页的“运行中版本”会显示 Admin 和 API 容器实际使用镜像的 Git 提交短号与构建时间（UTC 自动换算为浏览器本地时间）。这些数据来自运行中容器的镜像标签，而非页面缓存或一次性部署日志；因此可用于确认新镜像已经真正启动。首次升级到包含此功能的版本后，需要先按上面的完整引导流程重建 `deployer`，随后通过管理端重新部署各目标服务一次；历史镜像会显示“未识别”。

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
