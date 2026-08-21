FROM node:22-alpine AS build

ENV CI=true \
    COREPACK_ENABLE_PROJECT_SPEC=0

WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@10.17.1 --activate

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/admin/package.json apps/admin/package.json
COPY apps/miniapp/package.json apps/miniapp/package.json
RUN pnpm install --filter @supertools/admin... --frozen-lockfile --config.package-import-method=copy

COPY apps/admin ./apps/admin
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN pnpm --dir apps/admin build

FROM nginx:1.27-alpine

ARG APP_VERSION=dev
ARG APP_DEPLOYED_AT=
LABEL io.supertools.version=$APP_VERSION \
    io.supertools.deployed-at=$APP_DEPLOYED_AT

COPY infra/nginx/admin.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/admin/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1
