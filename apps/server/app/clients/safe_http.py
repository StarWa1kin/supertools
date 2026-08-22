import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from app.domains.video_parser.errors import VideoParserError, invalid_link, upstream_error

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
    "Mobile/15E148 Safari/604.1"
)


def host_matches(hostname: str, allowed: str) -> bool:
    hostname = hostname.lower().rstrip(".")
    allowed = allowed.lower().lstrip(".").rstrip(".")
    return hostname == allowed or hostname.endswith(f".{allowed}")


def normalize_public_url(url: str, allowed_hosts: tuple[str, ...] | list[str]) -> str:
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise invalid_link() from exc

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise invalid_link("仅支持有效的 HTTP 或 HTTPS 分享链接")
    if parsed.username or parsed.password:
        raise invalid_link("分享链接不能包含登录凭据")
    if port is not None and port not in {80, 443}:
        raise invalid_link("分享链接端口不受支持")
    if not any(host_matches(hostname, host) for host in allowed_hosts):
        raise invalid_link("链接域名不属于所选平台")

    netloc = hostname
    if port is not None:
        netloc = f"{hostname}:{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path or "/", parsed.query, ""))


def _is_public_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def ensure_public_dns(hostname: str) -> None:
    try:
        records = await asyncio.to_thread(socket.getaddrinfo, hostname, None)
    except socket.gaierror as exc:
        raise upstream_error("平台域名暂时无法解析") from exc
    addresses = {record[4][0] for record in records}
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise invalid_link("链接指向了不允许访问的网络地址")


@dataclass(slots=True)
class FetchedResponse:
    url: str
    status_code: int
    headers: httpx.Headers
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


class SafeHttpClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 15,
        max_redirects: int = 5,
        max_response_bytes: int = 5 * 1024 * 1024,
        concurrency: int = 10,
        transport: httpx.AsyncBaseTransport | None = None,
        resolve_dns: bool = True,
    ) -> None:
        self.max_redirects = max_redirects
        self.max_response_bytes = max_response_bytes
        self.resolve_dns = resolve_dns
        self._semaphore = asyncio.Semaphore(concurrency)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5)),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            headers={
                "User-Agent": MOBILE_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get(
        self,
        url: str,
        *,
        allowed_hosts: tuple[str, ...] | list[str],
        headers: dict[str, str] | None = None,
        referer_on_redirect: bool = False,
    ) -> FetchedResponse:
        current = normalize_public_url(url, allowed_hosts)
        request_headers = dict(headers or {})
        async with self._semaphore:
            for redirect_count in range(self.max_redirects + 1):
                parsed = urlsplit(current)
                if self.resolve_dns:
                    await ensure_public_dns(parsed.hostname or "")

                response = await self._request_with_retry(current, headers=request_headers)
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    await response.aclose()
                    if not location or redirect_count >= self.max_redirects:
                        raise upstream_error("平台短链重定向次数过多")
                    previous = current
                    current = normalize_public_url(urljoin(current, location), allowed_hosts)
                    if referer_on_redirect:
                        request_headers["Referer"] = previous
                    continue

                if response.status_code >= 400:
                    await response.aclose()
                    if response.status_code in {401, 403, 404}:
                        raise VideoParserError(
                            "content_unavailable",
                            "内容不存在、不可公开访问或已被平台限制",
                            422,
                        )
                    raise upstream_error(f"平台返回异常状态（{response.status_code}）")

                content = await self._read_limited(response)
                return FetchedResponse(
                    url=str(response.url),
                    status_code=response.status_code,
                    headers=response.headers,
                    content=content,
                )
        raise upstream_error()

    async def _request_with_retry(
        self,
        url: str,
        *,
        headers: dict[str, str] | None,
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                request = self._client.build_request("GET", url, headers=headers)
                response = await self._client.send(request, stream=True)
                if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                    await response.aclose()
                    await asyncio.sleep(0.15)
                    continue
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt == 0:
                    await asyncio.sleep(0.15)
        if isinstance(last_error, httpx.TimeoutException):
            raise VideoParserError("upstream_timeout", "平台响应超时，请稍后重试", 504)
        raise upstream_error("暂时无法连接视频平台") from last_error

    async def _read_limited(self, response: httpx.Response) -> bytes:
        length = response.headers.get("content-length")
        if length and length.isdigit() and int(length) > self.max_response_bytes:
            await response.aclose()
            raise VideoParserError("response_too_large", "平台页面响应过大", 502)

        chunks: list[bytes] = []
        total = 0
        try:
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > self.max_response_bytes:
                    raise VideoParserError("response_too_large", "平台页面响应过大", 502)
                chunks.append(chunk)
        finally:
            await response.aclose()
        return b"".join(chunks)
