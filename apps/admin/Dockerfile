# syntax=docker/dockerfile:1.7

FROM node:22-alpine AS build

ENV CI=true \
    COREPACK_ENABLE_PROJECT_SPEC=0

WORKDIR /src
RUN corepack enable && corepack prepare pnpm@10.17.1 --activate

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/admin/package.json apps/admin/package.json
COPY apps/miniapp/package.json apps/miniapp/package.json
COPY apps/admin ./apps/admin

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG VITE_API_BASE_URL=

# Some older Docker overlay filesystems reject pnpm's many small writes with EPERM.
# Build the dependency tree on tmpfs, then copy only the production assets out.
RUN --mount=type=tmpfs,target=/workspace,size=1073741824 \
    --mount=type=cache,target=/root/.npm \
    sh -ec 'cp -a /src/. /workspace/ \
      && cd /workspace/apps/admin \
      && npm install --ignore-scripts --no-package-lock --no-audit --no-fund \
      && VITE_API_BASE_URL="$VITE_API_BASE_URL" npm run build \
      && mkdir -p /output \
      && cp -a dist/. /output/'

FROM nginx:1.27-alpine

ARG APP_VERSION=dev
ARG APP_DEPLOYED_AT=
LABEL io.supertools.version=$APP_VERSION \
    io.supertools.deployed-at=$APP_DEPLOYED_AT

COPY infra/nginx/admin.conf /etc/nginx/conf.d/default.conf
COPY --from=build /output /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1
