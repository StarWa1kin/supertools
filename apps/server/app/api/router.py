from fastapi import APIRouter

from app.admin.router import router as admin_router
from app.domains.codex_watch.router import router as codex_watch_router
from app.domains.video_parser.router import router as video_parser_router

api_router = APIRouter()
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(codex_watch_router, prefix="/codex-watch", tags=["codex-watch"])
api_router.include_router(video_parser_router, prefix="/video-parser", tags=["video-parser"])
