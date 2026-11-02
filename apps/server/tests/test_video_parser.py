import asyncio
import socket

import httpx
import pytest

from app.clients.safe_http import ensure_public_dns
from app.core.config import SERVER_ROOT, Settings
from app.domains.video_parser.errors import VideoParserError
from app.domains.video_parser.media import MediaProxy, MediaTokenService
from app.domains.video_parser.service import VideoParserService


def test_dns_guard_rejects_private_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))],
    )
    with pytest.raises(VideoParserError, match="网络地址"):
        asyncio.run(ensure_public_dns("example.test"))


def test_service_can_disable_dns_resolution_for_fake_ip_development() -> None:
    settings = Settings(
        _env_file=None,
        VIDEO_MEDIA_SIGNING_SECRET="test-secret-at-least-16",
        VIDEO_PARSER_RESOLVE_DNS=False,
    )
    service = VideoParserService(settings=settings)
    try:
        assert service.media_proxy.settings.video_parser_resolve_dns is False
        assert service.upstream._client._trust_env is False
        assert service.media_proxy._client._trust_env is False
    finally:
        asyncio.run(service.close())


def test_settings_loads_server_env_file_independent_of_launch_directory() -> None:
    assert Settings.model_config["env_file"] == SERVER_ROOT / ".env"


def test_media_token_rejects_tampering_and_expiry() -> None:
    signer = MediaTokenService("test-secret-at-least-16", ttl_seconds=60)
    token = signer.sign(url="https://v.douyinvod.com/a.mp4", kind="video", filename="video")
    assert signer.verify(token).kind == "video"
    with pytest.raises(VideoParserError) as tampered:
        signer.verify(f"{token[:-1]}x")
    assert tampered.value.code == "invalid_media_token"

    expired = MediaTokenService("test-secret-at-least-16", ttl_seconds=-1).sign(
        url="https://v.douyinvod.com/a.mp4",
        kind="video",
        filename="video",
    )
    with pytest.raises(VideoParserError):
        signer.verify(expired)


def test_media_proxy_forwards_range_and_download_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_range = ""

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_range
        seen_range = request.headers.get("range", "")
        return httpx.Response(
            206,
            content=b"video",
            headers={
                "content-type": "video/mp4",
                "content-range": "bytes 0-4/5",
                "accept-ranges": "bytes",
            },
            request=request,
        )

    async def skip_dns(_hostname: str) -> None:
        return None

    async def scenario() -> None:
        settings = Settings(VIDEO_MEDIA_SIGNING_SECRET="test-secret-at-least-16")
        signer = MediaTokenService(settings.video_media_signing_secret, ttl_seconds=60)
        proxy = MediaProxy(settings, signer)
        await proxy._client.aclose()
        proxy._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        token = signer.sign(
            url="https://v.douyinvod.com/a.mp4",
            kind="video",
            filename="test-video",
        )
        response = await proxy.response(
            token,
            download=True,
            range_header="bytes=0-4",
        )
        body = b"".join([chunk async for chunk in response.body_iterator])
        assert body == b"video"
        assert response.status_code == 206
        assert response.headers["content-disposition"].endswith('test-video.mp4"')
        await proxy._client.aclose()

    monkeypatch.setattr("app.domains.video_parser.media.ensure_public_dns", skip_dns)
    asyncio.run(scenario())
    assert seen_range == "bytes=0-4"


def test_media_proxy_keeps_unlisted_terminal_cdn_behind_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_hosts: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_hosts.append(request.url.host)
        if request.url.host == "aweme.snssdk.com":
            return httpx.Response(
                302,
                headers={"location": "https://v5.douyinvod.com/video.mp4"},
                request=request,
            )
        if request.url.host == "v5.douyinvod.com":
            return httpx.Response(
                302,
                headers={"location": "https://123.dynamic-cdn.test/video.mp4"},
                request=request,
            )
        return httpx.Response(
            206,
            content=b"video",
            headers={"content-type": "video/mp4", "content-range": "bytes 0-4/5"},
            request=request,
        )

    async def skip_dns(_hostname: str) -> None:
        return None

    async def scenario() -> None:
        settings = Settings(VIDEO_MEDIA_SIGNING_SECRET="test-secret-at-least-16")
        signer = MediaTokenService(settings.video_media_signing_secret, ttl_seconds=60)
        proxy = MediaProxy(settings, signer)
        await proxy._client.aclose()
        proxy._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        token = signer.sign(
            url="https://aweme.snssdk.com/aweme/v1/play/",
            kind="video",
            filename="video",
        )
        response = await proxy.response(token, download=False, range_header="bytes=0-4")
        body = b"".join([chunk async for chunk in response.body_iterator])
        assert response.status_code == 206
        assert body == b"video"
        await proxy._client.aclose()

    monkeypatch.setattr("app.domains.video_parser.media.ensure_public_dns", skip_dns)
    asyncio.run(scenario())
    assert seen_hosts == [
        "aweme.snssdk.com",
        "v5.douyinvod.com",
        "123.dynamic-cdn.test",
    ]
