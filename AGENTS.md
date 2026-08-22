# Repository Guidelines

## 项目定位与技术栈

本项目是以微信小程序为主要发布端的工具集合。前端使用 UniApp、Vue 3、TypeScript 和 UnoCSS；服务端使用 Python 3.12、FastAPI 与 Pydantic。优先保证工具启动快、操作路径短，并兼顾 H5 调试体验。

## 首期工具

1. **Codex 额度情报监控**：定时获取指定 X（Twitter）账号（初始目标为 Tibo）的公开帖子，按 Codex、quota、limit、reset 等可配置关键词筛选，判断是否出现额度调整或重置信息。保存原文链接、发布时间、抓取时间和匹配原因，并通过帖子 ID 去重。账号、关键词和轮询频率必须来自配置，不得硬编码；页面需明确区分“官方确认”“第三方消息”和“程序推测”。
2. **视频链接解析**：接收抖音、快手等平台的公开分享链接，识别平台、解析标题/封面/作者及可用的视频地址，并允许用户下载。每个平台使用独立 adapter，单个平台规则变化不得影响其他平台。仅处理用户有权下载的公开内容，不绕过登录、付费、DRM 或访问控制；页面应展示版权与平台条款提示。

## 目录结构

- `apps/miniapp/`：UniApp 前端工程。
- `apps/miniapp/src/pages/`：页面；每个工具使用独立目录，如 `pages/text-counter/`。
- `apps/miniapp/src/components/`：跨页面复用组件。
- `apps/miniapp/src/composables/`：组合式逻辑；`api/` 存放请求封装。
- `apps/miniapp/src/config/apps.ts`：工具应用注册表，是首页和更多页入口的唯一数据源。
- `apps/miniapp/src/static/`：图标、图片等静态资源。
- `apps/server/app/`：FastAPI 应用；按业务域拆分 `routers/`、`services/`、`schemas/`。
- `apps/server/tests/`：后端测试；前端测试放在 `apps/miniapp/tests/`。
- `docs/`：接口、部署和重要设计决策。

业务逻辑不得直接堆放在页面或路由处理函数中；前端提取到 composable，后端下沉到 service。

首期页面建议使用 `pages/codex-watch/` 和 `pages/video-parser/`。后端领域模块使用 `app/domains/codex_watch/` 与 `app/domains/video_parser/`；视频平台适配器放在 `video_parser/adapters/`，共享 HTTP 客户端放在 `app/clients/`。

## 前端信息架构

主界面使用 UniApp 原生 `tabBar`，暂时固定两个 Tab：

1. **首页**（`pages/index/index`）：展示精选或常用应用。展示内容必须可配置，不在模板中直接硬编码工具卡片。
2. **更多**（`pages/more/index`）：展示全部已启用应用，采用类似 iPhone 桌面的图标网格；默认每行 4 个，圆角方形图标在上、应用名称在下，保持一致尺寸和触控区域。

Tab 页面之间使用 `uni.switchTab`，普通工具页面使用 `uni.navigateTo`。两个 Tab 必须注册在 `pages.json` 的 `tabBar` 中，Tab 图标放在 `src/static/tabbar/`；工具图标统一放在 `src/static/apps/`。

所有工具由 `src/config/apps.ts` 注册，建议结构为：

```ts
interface ToolApp {
  id: string;
  name: string;
  description: string;
  icon: string;
  route: string;
  enabled: boolean;
  featured: boolean;
  order: number;
}
```

首页只读取 `enabled && featured` 的应用并按 `order` 排序；更多页读取全部 `enabled` 应用。新增、隐藏或调整首页应用时，应只修改注册表配置。应用列表初期使用本地静态配置，后续接入远程配置时仍需保留本地默认值，并对服务端数据执行字段校验和失败回退。

更多页应优先保证图标识别度和快速扫描，不使用首页的大卡片布局。图标名称过长时最多显示两行；禁用应用不显示，尚未开放的应用可使用明确的“即将上线”状态但不得允许进入空页面。

## 开发、构建与检查

前端统一使用 `pnpm`：

- `pnpm install`：安装依赖。
- `pnpm --dir apps/miniapp dev:mp-weixin`：启动微信小程序开发构建。
- `pnpm --dir apps/miniapp dev:h5`：启动 H5 调试服务。
- `pnpm --dir apps/miniapp build:mp-weixin`：生成小程序生产包。
- `pnpm --dir apps/miniapp lint`：运行 TypeScript/Vue 类型检查。
- `pnpm --dir apps/miniapp test`：运行 Vitest 单元测试。

后端在 `apps/server/` 中执行：

- `uv sync --dev`：创建环境、安装依赖并更新 `uv.lock`。
- `uv run fastapi dev app/main.py`：启动开发服务器。
- `uv run pytest`：运行测试。
- `uv run ruff check .`、`uv run ruff format --check .`：检查代码质量与格式。

若脚手架生成的命令不同，应同步更新本文件与根目录 `README.md`。

## 编码与命名规范

Vue 组件使用 `<script setup lang="ts">`，缩进 2 个空格；Python 缩进 4 个空格并提供类型标注。组件使用 `PascalCase.vue`，composable 使用 `useXxx.ts`，普通变量使用 `camelCase`，Python 模块与函数使用 `snake_case`。样式优先使用 UnoCSS 原子类，主题色和间距写入 UnoCSS 配置，避免散落的魔法值。平台差异必须使用 UniApp 条件编译明确隔离。

## API、安全与配置

接口统一以 `/api/v1` 开头，返回稳定的数据结构和明确的 HTTP 状态码。使用 Pydantic 校验所有外部输入；不要信任仅由小程序端执行的校验。密钥、数据库地址和小程序凭据只能放入本地 `.env`，仓库仅提交 `.env.example`。日志不得记录令牌、手机号或完整用户输入。

建议使用 `GET /api/v1/codex-watch/posts` 查询监控结果，使用 `POST /api/v1/video-parser/resolve` 解析分享链接。对外部请求设置超时、重试、并发限制和明确的 User-Agent；校验重定向目标并阻止私网地址，避免 SSRF。不得在日志中保存完整分享参数，临时视频文件应设置自动过期清理。

## 测试规范

后端使用 Pytest 和 FastAPI `TestClient`/HTTPX，测试文件命名为 `test_*.py`。前端使用 Vitest，测试文件命名为 `*.spec.ts`。新增工具至少覆盖核心计算、无效输入和边界值；修复缺陷必须增加回归测试。提交前运行前后端全部 lint、类型检查和测试。

外部平台测试必须使用保存并脱敏的 fixture 或 mock，不依赖实时网络。重点覆盖帖子去重、关键词匹配、短链重定向、平台识别、失效链接、请求超时和 SSRF 拦截。

## 提交与 Pull Request

## 临时产物

禁止在仓库根目录创建或使用 `output/`、`.data/`、`.dev-logs/`、`.playwright-cli/` 或 `.ruff_cache/`。测试临时文件、浏览器自动化状态和调试日志均使用系统临时目录或相应工具的默认目录；Ruff 缓存使用用户缓存目录；需要保留的构建与部署产物应写入仓库外的明确目标目录。不得将这些目录作为截图、压缩包、测试缓存、日志、运行时数据或部署副本的默认位置。

提交信息采用 Conventional Commits，例如 `feat(miniapp): add unit converter`、`fix(api): reject invalid timezone`。一次提交只处理一个主题。Pull Request 需说明问题、实现方式和验证命令，关联相关 issue；界面改动附微信开发者工具截图，接口或配置变更需说明兼容性与部署步骤。禁止提交构建产物、依赖目录、缓存及真实密钥。
