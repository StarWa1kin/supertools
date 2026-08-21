from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from starlette.responses import Response

from app.domains.video_parser.errors import VideoParserError
from app.domains.video_parser.schemas import VideoResolveRequest, VideoResolveResult
from app.domains.video_parser.service import VideoParserService, get_video_parser_service

router = APIRouter()
ServiceDependency = Annotated[VideoParserService, Depends(get_video_parser_service)]


def _http_error(error: VideoParserError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


@router.post("/resolve", response_model=VideoResolveResult)
async def resolve_video(
    payload: VideoResolveRequest,
    service: ServiceDependency,
) -> VideoResolveResult:
    try:
        return await service.resolve(payload.url)
    except VideoParserError as exc:
        raise _http_error(exc) from exc


@router.get("/media")
async def proxy_media(
    service: ServiceDependency,
    token: Annotated[str, Query(min_length=20, max_length=8192)],
    download: bool = False,
    range_header: Annotated[str | None, Header(alias="Range")] = None,
) -> Response:
    try:
        return await service.media_proxy.response(
            token,
            download=download,
            range_header=range_header,
        )
    except VideoParserError as exc:
        raise _http_error(exc) from exc
