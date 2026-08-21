import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.admin.request_logs import get_request_log_store
from app.api.router import api_router
from app.core.config import get_settings
from app.domains.codex_watch.reminders import start_reminder_monitor, stop_reminder_monitor
from app.domains.video_parser.service import close_video_parser_service

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    start_reminder_monitor()
    yield
    await stop_reminder_monitor()
    await close_video_parser_service()


app = FastAPI(
    title="Supertools API",
    version="0.1.0",
    description="Backend services for the Supertools mini program.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type", "Range"],
    expose_headers=["Accept-Ranges", "Content-Length", "Content-Range", "Content-Disposition"],
)


@app.middleware("http")
async def capture_request_log(request: Request, call_next):
    started_at = perf_counter()
    response = await call_next(request)
    if request.url.path != "/api/v1/admin/request-logs":
        try:
            forwarded_for = request.headers.get("x-forwarded-for", "")
            client_ip = request.client.host if request.client else "unknown"
            if settings.request_log_trust_proxy_headers and forwarded_for:
                client_ip = forwarded_for.split(",", 1)[0].strip()
            get_request_log_store(settings).add(
                client_ip=client_ip,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round((perf_counter() - started_at) * 1000),
                user_agent=request.headers.get("user-agent", ""),
            )
        except (OSError, sqlite3.Error):
            # Request logging is diagnostic only. A full, locked, or unavailable
            # log store must never replace an otherwise valid API response with 500.
            pass
    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
