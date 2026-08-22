import base64
import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
from starlette.responses import Response, StreamingResponse

from app.clients.safe_http import MOBILE_USER_AGENT, ensure_public_dns, normalize_public_url
from app.core.config import Settings
from app.domains.video_parser.errors import VideoParserError, upstream_error
from app.domains.video_parser.schemas import MediaKind


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True, slots=True)
class MediaTokenPayload:
    url: str
    kind: MediaKind
    filename: str
    expires_at: int


class MediaTokenService:
    def __init__(self, secret: str, ttl_seconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._ttl_seconds = ttl_seconds

    def sign(self, *, url: str, kind: MediaKind, filename: str) -> str:
        payload = json.dumps(
            {
                "url": url,
                "kind": kind,
                "filename": filename,
                "exp": int(time.time()) + self._ttl_seconds,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8")
        encoded = _encode(payload)
        signature = _encode(
            hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).digest()
        )
        return f"{encoded}.{signature}"

    def verify(self, token: str) -> MediaTokenPayload:
        try:
            encoded, supplied_signature = token.split(".", 1)
            expected_signature = _encode(
                hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise ValueError
            payload = json.loads(_decode(encoded))
            expires_at = int(payload["exp"])
            kind = payload["kind"]
            if kind not in {"video", "image"} or expires_at < int(time.time()):
                raise ValueError
            return MediaTokenPayload(
                url=str(payload["url"]),
                kind=kind,
                filename=str(payload.get("filename") or "media"),
                expires_at=expires_at,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise VideoParserError(
                "invalid_media_token", "媒体地址已失效，请重新解析", 410
            ) from exc


class MediaProxy:
    def __init__(self, settings: Settings, token_service: MediaTokenService) -> None:
        self.settings = settings
        self.token_service = token_service
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30, connect=5),
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": MOBILE_USER_AGENT, "Accept": "*/*"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def response(
        self,
        token: str,
        *,
        download: bool,
        range_header: str | None,
    ) -> Response:
        payload = self.token_service.verify(token)
        response = await self._open(payload.url, range_header=range_header)
        limit = (
            self.settings.video_media_max_video_bytes
            if payload.kind == "video"
            else self.settings.video_media_max_image_bytes
        )
        try:
            self._validate_size(response, limit)
            self._validate_content_type(response, payload.kind)
        except VideoParserError:
            await response.aclose()
            raise

        headers: dict[str, str] = {}
        for name in ("content-length", "content-range", "accept-ranges", "etag", "last-modified"):
            value = response.headers.get(name)
            if value:
                headers[name] = value
        if download:
            extension = self._extension(response.headers.get("content-type", ""), payload.kind)
            filename = self._safe_filename(payload.filename, extension)
            headers["content-disposition"] = f'attachment; filename="{filename}"'
        headers["cache-control"] = "private, max-age=300"
        return StreamingResponse(
            self._iter_limited(response, limit),
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/octet-stream"),
            headers=headers,
        )

    async def _open(self, url: str, *, range_header: str | None) -> httpx.Response:
        current = normalize_public_url(url, self.settings.video_media_allowed_hosts)
        headers = {"Range": range_header} if range_header else None
        for redirect_count in range(self.settings.video_parser_max_redirects + 1):
            if self.settings.video_parser_resolve_dns:
                await ensure_public_dns(urlsplit(current).hostname or "")
            request = self._client.build_request("GET", current, headers=headers)
            try:
                response = await self._client.send(request, stream=True)
            except httpx.TimeoutException as exc:
                raise VideoParserError("media_timeout", "媒体服务器响应超时", 504) from exc
            except httpx.NetworkError as exc:
                raise upstream_error("暂时无法连接媒体服务器") from exc
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                await response.aclose()
                if not location or redirect_count >= self.settings.video_parser_max_redirects:
                    raise upstream_error("媒体重定向次数过多")
                target = urljoin(current, location)
                target_parts = urlsplit(target)
                target_host = target_parts.hostname or ""
                if target_parts.scheme != "https" or not target_host:
                    raise upstream_error("平台媒体跳转地址不安全")
                # Media providers commonly redirect to short-lived, dynamically named
                # CDN hosts. Keep following those redirects on the server so WeChat only
                # needs our API domain in its request/downloadFile/video allowlists.
                current = normalize_public_url(target, [target_host])
                continue
            if response.status_code not in {200, 206}:
                await response.aclose()
                if response.status_code == 416:
                    raise VideoParserError("invalid_range", "请求的媒体范围无效", 416)
                raise upstream_error(f"媒体服务器返回异常状态（{response.status_code}）")
            return response
        raise upstream_error("媒体重定向次数过多")

    @staticmethod
    def _validate_size(response: httpx.Response, limit: int) -> None:
        content_range = response.headers.get("content-range", "")
        match = re.search(r"/(\d+)$", content_range)
        if match and int(match.group(1)) > limit:
            raise VideoParserError("media_too_large", "媒体文件超过允许大小", 413)
        content_length = response.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > limit:
            raise VideoParserError("media_too_large", "媒体文件超过允许大小", 413)

    @staticmethod
    def _validate_content_type(response: httpx.Response, kind: MediaKind) -> None:
        content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
        allowed = content_type.startswith(f"{kind}/") or content_type in {
            "application/octet-stream",
            "binary/octet-stream",
        }
        if not allowed:
            raise VideoParserError("invalid_media_type", "平台返回的媒体类型不受支持", 502)

    @staticmethod
    async def _iter_limited(response: httpx.Response, limit: int):
        total = 0
        try:
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > limit:
                    break
                yield chunk
        finally:
            await response.aclose()

    @staticmethod
    def _extension(content_type: str, kind: MediaKind) -> str:
        content_type = content_type.split(";", 1)[0].lower()
        return {
            "video/mp4": ".mp4",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(content_type, ".mp4" if kind == "video" else ".jpg")

    @staticmethod
    def _safe_filename(value: str, extension: str) -> str:
        stem = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")[:48] or "media"
        return f"{stem}{extension}"
