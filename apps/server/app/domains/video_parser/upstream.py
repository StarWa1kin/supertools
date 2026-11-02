"""Translate the independent media-parser API into our existing media contract."""

import asyncio
import json
from dataclasses import dataclass, field

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.domains.video_parser.errors import VideoParserError, parse_error, upstream_error
from app.domains.video_parser.schemas import MediaKind, VideoPlatform

PLATFORM_IDS: dict[str, str] = {
    "抖音": "douyin",
    "快手": "kuaishou",
    "小红书": "xiaohongshu",
}


@dataclass(slots=True)
class ParsedAsset:
    kind: MediaKind
    url: str


@dataclass(slots=True)
class ParsedMedia:
    platform: VideoPlatform
    canonical_url: str
    title: str = ""
    author_name: str = ""
    author_avatar_url: str | None = None
    cover_url: str | None = None
    duration_ms: int | None = None
    assets: list[ParsedAsset] = field(default_factory=list)


class UpstreamAuthor(BaseModel):
    nickname: str | None = None
    avatar: str | None = None


class UpstreamImage(BaseModel):
    url: str | None = None


class UpstreamMedia(BaseModel):
    platform: VideoPlatform
    title: str | None = None
    desc: str | None = None
    video_url: str | None = None
    video_list: list[str] = Field(default_factory=list)
    image_list: list[str | UpstreamImage] = Field(default_factory=list)
    cover_url: str | None = None
    author: UpstreamAuthor | None = None
    is_preview: bool = False


class UpstreamResponse(BaseModel):
    retcode: int
    succ: bool
    error_code: str | None = None
    data: UpstreamMedia | None = None


class MediaParserClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._semaphore = asyncio.Semaphore(settings.video_parser_concurrency)
        headers = {"Accept": "application/json", "User-Agent": "Supertools/0.1"}
        api_key = settings.media_parser_api_key.get_secret_value()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.media_parser_timeout_seconds, connect=5),
            follow_redirects=False,
            trust_env=False,
            headers=headers,
            limits=httpx.Limits(max_connections=settings.video_parser_concurrency),
        )
        self._endpoint = f"{str(settings.media_parser_base_url).rstrip('/')}/api/v1/parse"

    async def close(self) -> None:
        await self._client.aclose()

    async def resolve(self, url: str) -> ParsedMedia:
        try:
            # Do not retry automatically: authenticated calls may consume upstream credits.
            async with (
                asyncio.timeout(self.settings.media_parser_timeout_seconds),
                self._semaphore,
                self._client.stream("POST", self._endpoint, json={"url": url}) as res,
            ):
                if res.status_code != 200:
                    self._raise_error(res.status_code)
                body = bytearray()
                async for chunk in res.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > self.settings.video_parser_max_response_bytes:
                        raise upstream_error("解析服务返回的数据过大")
            result = UpstreamResponse.model_validate(json.loads(body))
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise VideoParserError("upstream_timeout", "解析服务响应超时，请稍后重试", 504) from exc
        except httpx.HTTPError as exc:
            raise upstream_error("连接解析服务失败，请确认本地 media-parser 已启动") from exc
        except ValueError as exc:
            raise upstream_error("解析服务返回的数据格式异常") from exc

        if not result.succ or result.retcode != 200:
            self._raise_error(result.retcode, result.error_code)
        data = result.data
        if data is None:
            raise upstream_error("解析服务未返回媒体数据")
        if data.is_preview:
            raise VideoParserError("content_unavailable", "该内容仅开放预览，暂不支持下载", 422)

        videos = list(
            dict.fromkeys(
                value.strip()
                for value in [data.video_url, *data.video_list]
                if value and value.strip()
            )
        )
        images = [image if isinstance(image, str) else image.url for image in data.image_list]
        assets = (
            [ParsedAsset(kind="video", url=value) for value in videos]
            if videos
            else [
                ParsedAsset(kind="image", url=value.strip())
                for value in images
                if value and value.strip()
            ]
        )
        if not assets:
            raise parse_error("解析服务未返回可用的视频或图片")
        author = data.author or UpstreamAuthor()
        return ParsedMedia(
            platform=PLATFORM_IDS.get(data.platform, data.platform),
            canonical_url=url,
            title=data.title or data.desc or "",
            author_name=author.nickname or "",
            author_avatar_url=author.avatar,
            cover_url=data.cover_url,
            assets=assets,
        )

    @staticmethod
    def _raise_error(status: int, code: str | None = None) -> None:
        if status == 429:
            raise VideoParserError("rate_limited", "解析请求过于频繁，请稍后重试", 429)
        if status in {408, 504} or code == "PARSE_TIMEOUT":
            raise VideoParserError("upstream_timeout", "解析服务响应超时，请稍后重试", 504)
        if status in {401, 402, 403}:
            raise VideoParserError("parser_unavailable", "解析服务鉴权或额度配置异常", 503)
        if status in {400, 404, 422}:
            raise VideoParserError(
                "content_unavailable", "内容不可公开访问、平台要求登录或暂未返回可用媒体", 422
            )
        if status == 503:
            raise VideoParserError("parser_unavailable", "解析服务暂时不可用，请稍后重试", 503)
        raise upstream_error("解析服务处理失败，请稍后重试")
