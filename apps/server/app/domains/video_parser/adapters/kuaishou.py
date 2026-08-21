import html as html_module
import re

from app.clients.safe_http import SafeHttpClient
from app.domains.video_parser.adapters.base import ParsedAsset, ParsedMedia
from app.domains.video_parser.adapters.utils import extract_assignment_json, first_url, walk_dicts
from app.domains.video_parser.errors import parse_error

# Kuaishou's current public short links redirect through its corporate domain.
KUAISHOU_HOSTS = ("kuaishou.com", "kuaishoup.com", "gifshow.com", "chenzhongtech.com")
VIDEO_KEYS = ("photoUrl", "playUrl", "videoUrl", "mp4Url", "mainMvUrls")


class KuaishouAdapter:
    def __init__(self, client: SafeHttpClient) -> None:
        self.client = client

    async def resolve(self, url: str) -> ParsedMedia:
        response = await self.client.get(url, allowed_hosts=KUAISHOU_HOSTS)
        candidate = self._find_candidate(response.text)
        if candidate is None:
            raise parse_error("快手页面未返回公开作品数据")

        video_url = next(
            (first_url(candidate.get(key)) for key in VIDEO_KEYS if candidate.get(key)), None
        )
        if not video_url:
            raise parse_error("快手作品没有可用的视频地址")

        title = candidate.get("caption") or candidate.get("title") or "无标题作品"
        user = candidate.get("user") if isinstance(candidate.get("user"), dict) else {}
        author = (
            candidate.get("authorName")
            or candidate.get("name")
            or candidate.get("userName")
            or user.get("user_name")
            or user.get("userName")
            or user.get("name")
            or "未知作者"
        )
        cover = first_url(
            candidate.get("coverUrl")
            or candidate.get("cover")
            or candidate.get("poster")
            or candidate.get("thumbnail")
            or candidate.get("coverUrls")
        )
        avatar = first_url(
            candidate.get("headUrl")
            or candidate.get("avatar")
            or candidate.get("headUrls")
            or user.get("headurl")
            or user.get("headUrl")
            or user.get("headurls")
        )
        duration = self._duration_ms(candidate.get("duration"))
        return ParsedMedia(
            platform="kuaishou",
            canonical_url=response.url,
            title=str(title),
            author_name=str(author),
            author_avatar_url=avatar,
            cover_url=cover,
            duration_ms=duration,
            assets=[ParsedAsset(kind="video", url=video_url)],
        )

    def _find_candidate(self, html: str) -> dict[str, object] | None:
        for marker in (
            "window.__APOLLO_STATE__",
            "window.__INITIAL_STATE__",
            "window.INIT_STATE",
        ):
            state = extract_assignment_json(html, marker)
            if not state:
                continue
            for value in walk_dicts(state):
                if any(first_url(value.get(key)) for key in VIDEO_KEYS):
                    return value

        # Some public share pages expose the same stable fields as an inline JSON fragment.
        for key in VIDEO_KEYS:
            match = re.search(rf'"{key}"\s*:\s*"([^"]+)"', html)
            if match:
                candidate: dict[str, object] = {key: html_module.unescape(match.group(1))}
                self._copy_inline_field(html, candidate, "caption")
                self._copy_inline_field(html, candidate, "title")
                self._copy_inline_field(html, candidate, "coverUrl")
                self._copy_inline_field(html, candidate, "authorName")
                return candidate
        return None

    @staticmethod
    def _copy_inline_field(html: str, target: dict[str, object], key: str) -> None:
        match = re.search(rf'"{key}"\s*:\s*"([^"]*)"', html)
        if match:
            target[key] = html_module.unescape(match.group(1))

    @staticmethod
    def _duration_ms(value: object) -> int | None:
        try:
            duration = int(float(value or 0))
        except (TypeError, ValueError):
            return None
        if duration <= 0:
            return None
        return duration if duration > 1000 else duration * 1000
