import asyncio
import json
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.clients.safe_http import normalize_public_url
from app.core.config import Settings
from app.domains.video_parser.errors import VideoParserError
from app.domains.video_parser.service import VideoParserService


def parser_settings(**overrides: Any) -> Settings:
    return Settings(
        _env_file=None,
        VIDEO_PARSER_BACKEND="media_parser",
        MEDIA_PARSER_API_KEY="fixture-key",
        VIDEO_MEDIA_SIGNING_SECRET="fixture-signing-secret",
        **{"VIDEO_PARSER_RESOLVE_DNS": False, **overrides},
    )


def upstream_body(platform: str = "视频号", **overrides: Any) -> dict[str, Any]:
    return {
        "retcode": 200,
        "succ": True,
        "data": {
            "platform": platform,
            "title": "公开作品",
            "video_url": "https://new-cdn.example/video.mp4",
            "cover_url": "https://new-cdn.example/cover.jpg",
            "author": {"nickname": "作者", "avatar": "https://avatar.example/a.jpg"},
            **overrides,
        },
    }


@asynccontextmanager
async def mocked_service(
    body: dict[str, Any], *, status: int = 200, settings: Settings | None = None
) -> AsyncIterator[tuple[VideoParserService, list[httpx.Request]]]:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, json=body, request=request)

    service = VideoParserService(settings=settings or parser_settings())
    assert service.upstream is not None
    await service.upstream._client.aclose()
    service.upstream._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer fixture-key"},
    )
    try:
        yield service, requests
    finally:
        await service.close()


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://weixin.qq.com/sph/example", "视频号"),
        ("https://b23.tv/example", "哔哩哔哩"),
        ("https://new-platform.example/post", "Future Provider"),
        ("https://v.douyin.com/example", "Upstream Platform"),
    ],
)
def test_upstream_identifies_platform_and_supplies_new_media_hosts(url: str, platform: str) -> None:
    async def scenario() -> None:
        async with mocked_service(upstream_body(platform)) as (service, requests):
            result = await service.resolve(url)
            assert result.platform == platform
            assert result.model_dump(by_alias=True)["platform"] == platform
            assert result.assets[0].source_url == "https://new-cdn.example/video.mp4"
            assert result.cover_url and result.author.avatar_url
            for path in [result.assets[0].preview_path, result.cover_url, result.author.avatar_url]:
                token = parse_qs(urlsplit(path).query)["token"][0]
                assert service.token_service.verify(token).url.startswith("https://")
            assert len(requests) == 1
            assert requests[0].url.path == "/api/v1/parse"
            assert json.loads(requests[0].content) == {"url": url}

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("name", "identifier"), [("抖音", "douyin"), ("快手", "kuaishou"), ("小红书", "xiaohongshu")]
)
def test_existing_platform_identifiers_stay_compatible(name: str, identifier: str) -> None:
    async def scenario() -> None:
        async with mocked_service(upstream_body(name)) as (service, _):
            result = await service.resolve("https://public.example/post")
            assert result.platform == identifier

    asyncio.run(scenario())


def test_configured_key_is_sent_to_upstream() -> None:
    async def scenario() -> None:
        service = VideoParserService(settings=parser_settings())
        try:
            assert service.upstream is not None
            assert service.upstream._client.headers["authorization"] == "Bearer fixture-key"
        finally:
            await service.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "url",
    [
        "not a URL",
        "file:///etc/hosts",
        "ftp://public.example/video",
        "https://user:password@public.example/post",
        "https://@public.example/post",
        "https://public.example:9000/post",
        "http://localhost/post",
        "http://host.local/post",
        "http://127.0.0.1/post",
        "http://127.1/post",
        "http://2130706433/post",
        "http://0x7f000001/post",
        "http://10.0.0.1/post",
        "http://169.254.169.254/post",
        "http://[::1]/post",
        "http://[fd00::1]/post",
    ],
)
def test_invalid_and_private_inputs_never_reach_upstream(url: str) -> None:
    async def scenario() -> None:
        async with mocked_service(upstream_body()) as (service, requests):
            with pytest.raises(VideoParserError) as error:
                await service.resolve(url)
            assert error.value.code == "invalid_link"
            assert not requests

    asyncio.run(scenario())


def test_generic_input_dns_is_checked_before_upstream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0))],
    )

    async def scenario() -> None:
        async with mocked_service(
            upstream_body(), settings=parser_settings(VIDEO_PARSER_RESOLVE_DNS=True)
        ) as (service, requests):
            with pytest.raises(VideoParserError) as error:
                await service.resolve("https://public.example/post")
            assert error.value.code == "invalid_link"
            assert not requests

    asyncio.run(scenario())


@pytest.mark.parametrize("status", [401, 402, 403, 429, 504])
def test_upstream_errors_are_not_retried_or_hidden(status: int) -> None:
    async def scenario() -> None:
        async with mocked_service({}, status=status) as (service, requests):
            with pytest.raises(VideoParserError) as error:
                await service.resolve("https://public.example/post")
            assert error.value.status_code == (503 if status in {401, 402, 403} else status)
            assert len(requests) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("platform", ["", "   ", "x" * 101])
def test_upstream_platform_field_is_still_validated(platform: str) -> None:
    async def scenario() -> None:
        async with mocked_service(upstream_body(platform)) as (service, _):
            with pytest.raises(VideoParserError) as error:
                await service.resolve("https://public.example/post")
            assert error.value.status_code == 502

    asyncio.run(scenario())


@pytest.mark.parametrize("url", ["http://127.0.0.1/video.mp4", "file:///video.mp4"])
def test_private_or_invalid_upstream_media_is_not_signed(url: str) -> None:
    async def scenario() -> None:
        async with mocked_service(upstream_body(video_url=url)) as (service, _):
            with pytest.raises(VideoParserError) as error:
                await service.resolve("https://public.example/post")
            assert error.value.code == "unsupported_media_host"

    asyncio.run(scenario())


def test_preview_only_content_is_still_rejected() -> None:
    async def scenario() -> None:
        async with mocked_service(upstream_body(is_preview=True)) as (service, _):
            with pytest.raises(VideoParserError) as error:
                await service.resolve("https://public.example/post")
            assert error.value.code == "content_unavailable"

    asyncio.run(scenario())


def test_unlisted_media_host_is_proxied_with_dns_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    checked: list[str] = []

    async def check_dns(hostname: str) -> None:
        checked.append(hostname)

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"video", headers={"content-type": "video/mp4"})

    monkeypatch.setattr("app.domains.video_parser.media.ensure_public_dns", check_dns)

    async def scenario() -> None:
        async with mocked_service(upstream_body()) as (service, _):
            result = await service.resolve("https://public.example/post")
            service.settings.video_parser_resolve_dns = True
            await service.media_proxy._client.aclose()
            service.media_proxy._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            token = parse_qs(urlsplit(result.assets[0].preview_path).query)["token"][0]
            response = await service.media_proxy.response(token, download=True, range_header=None)
            assert b"".join([part async for part in response.body_iterator]) == b"video"
            assert response.status_code == 200

    asyncio.run(scenario())
    assert checked == ["new-cdn.example"]


def test_media_redirect_to_private_host_is_blocked() -> None:
    seen: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.host)
        return httpx.Response(302, headers={"location": "https://127.0.0.1/private"})

    async def scenario() -> None:
        async with mocked_service(upstream_body()) as (service, _):
            await service.media_proxy._client.aclose()
            service.media_proxy._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            token = service.token_service.sign(
                url="https://new-cdn.example/video.mp4", kind="video", filename="media"
            )
            with pytest.raises(VideoParserError) as error:
                await service.media_proxy.response(token, download=False, range_header=None)
            assert error.value.code == "invalid_link"

    asyncio.run(scenario())
    assert seen == ["new-cdn.example"]


def test_native_mode_still_requires_supported_platform_and_media_host() -> None:
    async def scenario() -> None:
        settings = Settings(_env_file=None, VIDEO_PARSER_BACKEND="native")
        service = VideoParserService(settings=settings)
        try:
            with pytest.raises(VideoParserError) as error:
                await service.resolve("https://weixin.qq.com/sph/example")
            assert error.value.code == "invalid_link"
            token = service.token_service.sign(
                url="https://new-cdn.example/video.mp4", kind="video", filename="media"
            )
            with pytest.raises(VideoParserError):
                await service.media_proxy.response(token, download=False, range_header=None)
        finally:
            await service.close()

    asyncio.run(scenario())


def test_public_ipv6_url_keeps_brackets() -> None:
    assert normalize_public_url("https://[2606:4700:4700::1111]/post") == (
        "https://[2606:4700:4700::1111]/post"
    )


def test_new_media_host_resolving_to_private_network_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0))],
    )
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=b"video", headers={"content-type": "video/mp4"})

    async def scenario() -> None:
        async with mocked_service(upstream_body()) as (service, _):
            result = await service.resolve("https://public.example/post")
            service.settings.video_parser_resolve_dns = True
            await service.media_proxy._client.aclose()
            service.media_proxy._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            token = parse_qs(urlsplit(result.assets[0].preview_path).query)["token"][0]
            with pytest.raises(VideoParserError) as error:
                await service.media_proxy.response(token, download=False, range_header=None)
            assert error.value.code == "invalid_link"
            assert not requests

    asyncio.run(scenario())


def test_resolve_endpoint_returns_new_platform_without_enum_rejection() -> None:
    from app.domains.video_parser.service import get_video_parser_service
    from app.main import app

    async def scenario() -> None:
        async with mocked_service(upstream_body()) as (service, requests):
            app.dependency_overrides[get_video_parser_service] = lambda: service
            try:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/video-parser/resolve",
                        json={"url": "https://weixin.qq.com/sph/example"},
                    )
                assert response.status_code == 200
                assert response.json()["platform"] == "视频号"
                assert len(requests) == 1
            finally:
                app.dependency_overrides.pop(get_video_parser_service, None)

    asyncio.run(scenario())
