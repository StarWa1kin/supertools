# Supertools Server

```bash
uv sync --dev
uv run fastapi dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

默认监听 `127.0.0.1:8000`，交互式接口文档位于 `/docs`。

Codex 情报管理接口：

- `POST /api/v1/admin/login`：管理员登录。
- `GET/PUT /api/v1/admin/codex-watch/config`：读取和保存抓取、教程、交流群配置。
- `GET /api/v1/admin/codex-watch/reminder-subscriptions`：查看脱敏后的订阅记录。
- `POST /api/v1/admin/codex-watch/reminder-subscriptions/{id}/test`：向指定订阅发送一条真实测试消息（消耗一次授权）。
- `GET /api/v1/codex-watch/config`：小程序使用的公开展示配置。
- `POST /api/v1/codex-watch/subscriptions`：使用 `wx.login` code 登记一次微信重置提醒。

微信订阅消息默认关闭。配置 `WECHAT_REMINDER_ENABLED=true`、小程序
`WECHAT_APP_ID`、`WECHAT_APP_SECRET` 和 `WECHAT_RESET_TEMPLATE_ID` 后启用；模板字段名通过
`WECHAT_TEMPLATE_STATUS_KEY`、`WECHAT_TEMPLATE_TIME_KEY`、
`WECHAT_TEMPLATE_REMARK_KEY` 与微信后台模板保持一致。普通订阅每成功发送一次消耗一次授权。

后台接口统一放在 `app/admin/`，并通过 `app/admin/router.py` 聚合。新增后台业务时，
在该目录创建对应路由模块并挂载到聚合路由，避免后台接口混入公开领域路由。

生产部署必须覆盖 `.env.example` 中的默认管理员密码和令牌密钥。
