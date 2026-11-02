import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

from app.domains.video_parser.errors import invalid_link, upstream_error

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
    "Mobile/15E148 Safari/604.1"
)


def normalize_public_url(url: str) -> str:
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise invalid_link() from exc

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise invalid_link("仅支持有效的 HTTP 或 HTTPS 分享链接")
    if parsed.username is not None or parsed.password is not None:
        raise invalid_link("分享链接不能包含登录凭据")
    if port is not None and port not in {80, 443}:
        raise invalid_link("分享链接端口不受支持")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
        raise invalid_link("链接指向了不允许访问的网络地址")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            # inet_aton also recognizes shortened, integer and hexadecimal IPv4.
            address = ipaddress.ip_address(socket.inet_aton(hostname))
        except OSError:
            address = None
    if address is not None and not _is_public_ip(str(address)):
        raise invalid_link("链接指向了不允许访问的网络地址")

    netloc = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None:
        netloc = f"{netloc}:{port}"
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
