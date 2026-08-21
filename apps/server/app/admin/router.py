from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.admin.auth import create_admin_session, require_admin
from app.admin.codex_watch import router as codex_watch_router
from app.admin.deployment import DeploymentService, get_deployment_service
from app.admin.request_logs import RequestLogStore, iter_request_log_store
from app.admin.schemas import AdminLoginRequest, AdminSession, RequestLogPage
from app.core.config import Settings, get_settings

router = APIRouter()


@router.post("/login", response_model=AdminSession)
async def login(
    credentials: AdminLoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AdminSession:
    return create_admin_session(credentials, settings)


@router.get("/deployment/status")
async def deployment_status(
    _admin: Annotated[str, Depends(require_admin)],
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
) -> dict[str, object]:
    return await service.status()


@router.post("/deployment/server")
async def start_server_deployment(
    _admin: Annotated[str, Depends(require_admin)],
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
) -> dict[str, object]:
    return await service.start("server")


@router.post("/deployment/admin")
async def start_admin_deployment(
    _admin: Annotated[str, Depends(require_admin)],
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
) -> dict[str, object]:
    return await service.start("admin")


@router.get("/request-logs", response_model=RequestLogPage)
async def request_logs(
    _admin: Annotated[str, Depends(require_admin)],
    store: Annotated[RequestLogStore, Depends(iter_request_log_store)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: Annotated[int | None, Query(ge=100, le=599)] = None,
    path: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
) -> RequestLogPage:
    total, items = store.list(limit=limit, offset=offset, status=status, path=path)
    return RequestLogPage(total=total, items=items)


router.include_router(codex_watch_router, prefix="/codex-watch", tags=["admin-codex-watch"])
