import hashlib
import logging
from functools import lru_cache
from urllib.parse import urlsplit

from app.clients.safe_http import SafeHttpClient, host_matches, normalize_public_url
from app.core.config import Settings, get_settings
from app.domains.video_parser.adapters import DouyinAdapter, KuaishouAdapter, XiaohongshuAdapter
from app.domains.video_parser.adapters.base import ParsedMedia, VideoPlatformAdapter
from app.domains.video_parser.errors import VideoParserError, invalid_link, parse_error
from app.domains.video_parser.media import MediaProxy, MediaTokenService
from app.domains.video_parser.schemas import (
    VideoAsset,
    VideoAuthor,
    VideoPlatform,
    VideoResolveResult,
)

logger = logging.getLogger(__name__)

PLATFORM_HOSTS: dict[VideoPlatform, tuple[str, ...]] = {
    "douyin": ("douyin.com", "iesdouyin.com"),
    "kuaishou": ("kuaishou.com", "kuaishoup.com", "gifshow.com", "chenzhongtech.com"),
    "xiaohongshu": ("xiaohongshu.com", "xhslink.com", "xhslink.cn"),
}


def detect_platform(url: str) -> VideoPlatform | None:
    try:
        hostname = (urlsplit(url.strip()).hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    for platform, allowed_hosts in PLATFORM_HOSTS.items():
        if any(host_matches(hostname, allowed) for allowed in allowed_hosts):
            return platform
    return None


class VideoParserService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        http_client: SafeHttpClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if (
            self.settings.environment == "production"
            and self.settings.video_media_signing_secret == "dev-only-change-me"
        ):
            raise RuntimeError("VIDEO_MEDIA_SIGNING_SECRET must be configured in production")
        self.http_client = http_client or SafeHttpClient(
            timeout_seconds=self.settings.video_parser_timeout_seconds,
            max_redirects=self.settings.video_parser_max_redirects,
            max_response_bytes=self.settings.video_parser_max_response_bytes,
            concurrency=self.settings.video_parser_concurrency,
            resolve_dns=self.settings.video_parser_resolve_dns,
        )
        self.token_service = MediaTokenService(
            self.settings.video_media_signing_secret,
            self.settings.video_media_token_ttl_seconds,
        )
        self.media_proxy = MediaProxy(self.settings, self.token_service)
        self.adapters: dict[VideoPlatform, VideoPlatformAdapter] = {
            "douyin": DouyinAdapter(self.http_client),
            "kuaishou": KuaishouAdapter(self.http_client),
            "xiaohongshu": XiaohongshuAdapter(self.http_client),
        }

    async def resolve(self, url: str) -> VideoResolveResult:
        platform = detect_platform(url)
        if platform is None:
            raise invalid_link("目前仅支持抖音、快手和小红书公开分享链接")
        normalized_url = normalize_public_url(url, PLATFORM_HOSTS[platform])
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()[:12]
        try:
            parsed = await self.adapters[platform].resolve(normalized_url)
            return self._to_result(parsed)
        except VideoParserError as exc:
            logger.warning(
                "video parse failed platform=%s code=%s url_hash=%s",
                platform,
                exc.code,
                url_hash,
            )
            raise

    async def close(self) -> None:
        await self.http_client.close()
        await self.media_proxy.close()

    def _to_result(self, parsed: ParsedMedia) -> VideoResolveResult:
        if not parsed.assets:
            raise parse_error("平台没有返回可用媒体")
        media_type = "video" if parsed.assets[0].kind == "video" else "images"
        assets: list[VideoAsset] = []
        for index, asset in enumerate(parsed.assets, start=1):
            try:
                source_url = normalize_public_url(
                    asset.url, self.settings.video_media_allowed_hosts
                )
            except VideoParserError as exc:
                raise VideoParserError(
                    "unsupported_media_host",
                    "平台返回了尚未允许的媒体域名",
                    502,
                ) from exc
            token = self.token_service.sign(
                url=source_url,
                kind=asset.kind,
                filename=f"{parsed.platform}-{index}",
            )
            preview_path = f"/api/v1/video-parser/media?token={token}"
            assets.append(
                VideoAsset(
                    kind=asset.kind,
                    source_url=source_url,
                    preview_path=preview_path,
                    download_path=f"{preview_path}&download=true",
                )
            )

        cover_url = self._preview_path(parsed.cover_url, "cover")
        avatar_url = self._preview_path(parsed.author_avatar_url, "avatar")
        return VideoResolveResult(
            platform=parsed.platform,
            media_type=media_type,
            canonical_url=parsed.canonical_url,
            title=parsed.title.strip() or "无标题作品",
            author=VideoAuthor(
                name=parsed.author_name.strip() or "未知作者", avatar_url=avatar_url
            ),
            duration_ms=parsed.duration_ms,
            cover_url=cover_url,
            assets=assets,
        )

    def _preview_path(self, source_url: str | None, name: str) -> str | None:
        if not source_url:
            return None
        try:
            normalized = normalize_public_url(source_url, self.settings.video_media_allowed_hosts)
        except VideoParserError:
            return None
        token = self.token_service.sign(url=normalized, kind="image", filename=name)
        return f"/api/v1/video-parser/media?token={token}"


@lru_cache
def get_video_parser_service() -> VideoParserService:
    return VideoParserService()


async def close_video_parser_service() -> None:
    if get_video_parser_service.cache_info().currsize:
        await get_video_parser_service().close()
        get_video_parser_service.cache_clear()
