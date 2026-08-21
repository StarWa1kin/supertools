FROM python:3.12-slim

ARG APP_VERSION=dev
ARG APP_DEPLOYED_AT=
LABEL io.supertools.version=$APP_VERSION \
    io.supertools.deployed-at=$APP_DEPLOYED_AT

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CODEX_WATCH_DATA_DIR=/var/lib/supertools/codex-watch \
    REQUEST_LOG_DATA_DIR=/var/lib/supertools/request-logs

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY apps/server/pyproject.toml apps/server/uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-install-project

COPY apps/server/app ./app
RUN mkdir -p /var/lib/supertools/codex-watch /var/lib/supertools/request-logs \
    && chown -R appuser:appuser /app /var/lib/supertools

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
