import asyncio
import socket
from pathlib import Path

import httpx
import pytest

from app.clients.safe_http import SafeHttpClient, ensure_public_dns
from app.core.config import SERVER_ROOT, Settings
from app.domains.video_parser.errors import VideoParserError
from app.domains.video_parser.media import MediaProxy, MediaTokenService
from app.domains.video_parser.service import VideoParserService, detect_platform

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


async def resolve_fixture(url: str, html_name: str):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture(html_name), request=request)

    http_client = SafeHttpClient(
        transport=httpx.MockTransport(handler),
        resolve_dns=False,
    )
    service = VideoParserService(http_client=http_client)
    try:
        return await service.resolve(url)
    finally:
        await service.close()


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://v.douyin.com/example", "douyin"),
        ("https://v.kuaishou.com/example", "kuaishou"),
        ("https://xhslink.com/example", "xiaohongshu"),
        ("https://xhslink.cn/o/4NDVCw2LfT7", "xiaohongshu"),
    ],
)
def test_detect_platform(url: str, platform: str) -> None:
    assert detect_platform(url) == platform


def test_detect_platform_rejects_lookalike_domain() -> None:
    assert detect_platform("https://douyin.com.example.org/video") is None


def test_douyin_video_fixture() -> None:
    result = asyncio.run(
        resolve_fixture(
            "https://www.douyin.com/video/7123456789012345678",
            "douyin_video.html",
        )
    )
    assert result.platform == "douyin"
    assert result.media_type == "video"
    assert result.title == "测试抖音视频"
    assert result.assets[0].source_url.startswith("https://aweme.snssdk.com/aweme/v1/play/")


def test_douyin_image_fixture() -> None:
    result = asyncio.run(
        resolve_fixture(
            "https://www.douyin.com/note/7123456789012345678",
            "douyin_images.html",
        )
    )
    assert result.media_type == "images"
    assert len(result.assets) == 2


def test_kuaishou_video_fixture() -> None:
    result = asyncio.run(
        resolve_fixture("https://www.kuaishou.com/short-video/test", "kuaishou_video.html")
    )
    assert result.platform == "kuaishou"
    assert result.duration_ms == 9000
    assert result.author.name == "快手作者"


def test_kuaishou_short_link_allows_corporate_redirect() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "v.kuaishou.com":
            return httpx.Response(
                302,
                headers={
                    "location": "https://v.m.chenzhongtech.com/fw/photo/test",
                },
                request=request,
            )
        return httpx.Response(200, text=fixture("kuaishou_video.html"), request=request)

    async def scenario():
        client = SafeHttpClient(transport=httpx.MockTransport(handler), resolve_dns=False)
        service = VideoParserService(http_client=client)
        try:
            return await service.resolve("https://v.kuaishou.com/test")
        finally:
            await service.close()

    result = asyncio.run(scenario())
    assert result.platform == "kuaishou"
    assert result.canonical_url == "https://v.m.chenzhongtech.com/fw/photo/test"
    assert [request.url.host for request in requests] == [
        "v.kuaishou.com",
        "v.m.chenzhongtech.com",
    ]


def test_kuaishou_supports_current_h5_initial_state() -> None:
    html = """<script>window.INIT_STATE = {
      "photo": {
        "caption": "新版快手作品",
        "duration": 7700,
        "mainMvUrls": [{"url": "https://v2.kwaicdn.com/video.mp4"}],
        "coverUrls": [{"url": "https://p1.kwimgs.com/cover.jpg"}],
        "userName": "新版快手作者",
        "headUrl": "https://p1.kwimgs.com/avatar.jpg"
      }
    }</script>"""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, request=request)

    async def scenario():
        client = SafeHttpClient(transport=httpx.MockTransport(handler), resolve_dns=False)
        service = VideoParserService(http_client=client)
        try:
            return await service.resolve("https://v.m.chenzhongtech.com/fw/photo/test")
        finally:
            await service.close()

    result = asyncio.run(scenario())
    assert result.title == "新版快手作品"
    assert result.author.name == "新版快手作者"
    assert result.duration_ms == 7700
    assert result.assets[0].source_url == "https://v2.kwaicdn.com/video.mp4"


def test_xiaohongshu_matches_node_parser_and_prefers_h265_video() -> None:
    result = asyncio.run(
        resolve_fixture("https://www.xiaohongshu.com/explore/test", "xiaohongshu_video.html")
    )
    assert result.media_type == "video"
    assert result.assets[0].source_url.endswith("video-h265.mp4")


def test_xiaohongshu_supports_legacy_note_and_info_list_image() -> None:
    html = """<html><script>window.__INITIAL_STATE__ = {
      "noteData":{"data":{"noteData":{"title":"旧版笔记","user":{"name":"作者"},
      "imageList":[{"infoList":[{"url":"https://sns-img.xhscdn.com/legacy.jpg"}]}]}}}
    };</script></html>"""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, request=request)

    async def scenario():
        client = SafeHttpClient(transport=httpx.MockTransport(handler), resolve_dns=False)
        service = VideoParserService(http_client=client)
        try:
            return await service.resolve("https://www.xiaohongshu.com/explore/test")
        finally:
            await service.close()

    result = asyncio.run(scenario())
    assert result.title == "旧版笔记"
    assert result.assets[0].source_url.endswith("legacy.jpg")


def test_xiaohongshu_uses_desktop_ua_and_redirect_referer() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                302,
                headers={"location": "https://www.xiaohongshu.com/explore/test"},
                request=request,
            )
        return httpx.Response(200, text=fixture("xiaohongshu_video.html"), request=request)

    async def scenario() -> None:
        client = SafeHttpClient(transport=httpx.MockTransport(handler), resolve_dns=False)
        service = VideoParserService(http_client=client)
        try:
            await service.resolve("https://xhslink.com/o/test")
        finally:
            await service.close()

    asyncio.run(scenario())
    assert "Chrome/129.0.0.0" in requests[0].headers["user-agent"]
    assert requests[1].headers["referer"] == "https://xhslink.com/o/test"


def test_xiaohongshu_image_fixture() -> None:
    result = asyncio.run(
        resolve_fixture("https://www.xiaohongshu.com/explore/test", "xiaohongshu_images.html")
    )
    assert result.media_type == "images"
    assert len(result.assets) == 2


def test_safe_client_rejects_cross_platform_redirect() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://example.org/private"},
            request=request,
        )

    async def scenario() -> None:
        client = SafeHttpClient(
            transport=httpx.MockTransport(handler),
            resolve_dns=False,
        )
        try:
            with pytest.raises(VideoParserError, match="域名"):
                await client.get("https://v.douyin.com/example", allowed_hosts=("douyin.com",))
        finally:
            await client.close()

    asyncio.run(scenario())


def test_safe_client_rejects_large_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 32, request=request)

    async def scenario() -> None:
        client = SafeHttpClient(
            transport=httpx.MockTransport(handler),
            max_response_bytes=16,
            resolve_dns=False,
        )
        try:
            with pytest.raises(VideoParserError) as exc_info:
                await client.get("https://v.douyin.com/example", allowed_hosts=("douyin.com",))
            assert exc_info.value.code == "response_too_large"
        finally:
            await client.close()

    asyncio.run(scenario())


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
        VIDEO_MEDIA_SIGNING_SECRET="test-secret-at-least-16",
        VIDEO_PARSER_RESOLVE_DNS=False,
    )
    service = VideoParserService(settings=settings)
    try:
        assert service.http_client.resolve_dns is False
        assert service.media_proxy.settings.video_parser_resolve_dns is False
        assert service.http_client._client._trust_env is False
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
