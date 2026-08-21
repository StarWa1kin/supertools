from typing import Any

from app.clients.safe_http import SafeHttpClient
from app.domains.video_parser.adapters.base import ParsedAsset, ParsedMedia
from app.domains.video_parser.adapters.utils import extract_assignment_json, first_url, walk_dicts
from app.domains.video_parser.errors import parse_error

XIAOHONGSHU_HOSTS = ("xiaohongshu.com", "xhslink.com", "xhslink.cn")
XIAOHONGSHU_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 "
        "Safari/537.36 Edg/129.0.0.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class XiaohongshuAdapter:
    def __init__(self, client: SafeHttpClient) -> None:
        self.client = client

    async def resolve(self, url: str) -> ParsedMedia:
        if url.startswith(("http://xhslink.com", "http://xhslink.cn")):
            url = f"https://{url.removeprefix('http://')}"
        response = await self.client.get(
            url,
            allowed_hosts=XIAOHONGSHU_HOSTS,
            headers=XIAOHONGSHU_HEADERS,
            referer_on_redirect=True,
        )
        state = extract_assignment_json(response.text, "window.__INITIAL_STATE__")
        note = self._find_note(state)
        if note is None:
            raise parse_error("小红书页面未返回公开笔记数据")

        user = note.get("user") if isinstance(note.get("user"), dict) else {}
        image_list = note.get("imageList") if isinstance(note.get("imageList"), list) else []
        image_urls = [url for image in image_list if (url := self._image_url(image))]
        video_url = self._video_url(note)

        if video_url:
            assets = [ParsedAsset(kind="video", url=video_url)]
        elif image_urls:
            assets = [ParsedAsset(kind="image", url=image_url) for image_url in image_urls]
        else:
            raise parse_error("该小红书笔记没有可用的视频或图片")

        title = note.get("title") or note.get("desc") or note.get("description") or "无标题笔记"
        author_name = user.get("nickName") or user.get("nickname") or user.get("name") or "未知作者"
        return ParsedMedia(
            platform="xiaohongshu",
            canonical_url=response.url,
            title=str(title),
            author_name=str(author_name),
            author_avatar_url=first_url(user.get("avatar") or user.get("avatarUrl")),
            cover_url=image_urls[0] if image_urls else None,
            duration_ms=self._duration_ms(note),
            assets=assets,
        )

    @staticmethod
    def _find_note(state: dict[str, Any] | None) -> dict[str, Any] | None:
        if not state:
            return None
        note_state = state.get("note")
        if isinstance(note_state, dict):
            note_id = note_state.get("currentNoteId")
            detail_map = note_state.get("noteDetailMap")
            if isinstance(detail_map, dict) and note_id in detail_map:
                entry = detail_map[note_id]
                if isinstance(entry, dict):
                    value = entry.get("note", entry)
                    if isinstance(value, dict):
                        return value

        # Older H5 pages used several different wrappers around the note payload.
        for path in (
            ("noteData", "data", "noteData"),
            ("note", "data"),
            ("noteDetail", "data"),
            ("data", "noteData"),
        ):
            value: object = state
            for key in path:
                value = value.get(key) if isinstance(value, dict) else None
            if isinstance(value, dict):
                return value

        for value in walk_dicts(state):
            if "imageList" in value and ("user" in value or "title" in value or "desc" in value):
                return value
        return None

    @staticmethod
    def _video_url(note: dict[str, Any]) -> str | None:
        video = note.get("video")
        if not isinstance(video, dict):
            return None
        media = video.get("media")
        stream = media.get("stream") if isinstance(media, dict) else None
        if not isinstance(stream, dict):
            return first_url(video)
        # Keep parity with the Node parser: prefer the first H.265 master stream,
        # then fall back to the first H.264 master stream.
        for codec in ("h265", "h264"):
            streams = stream.get(codec)
            if not isinstance(streams, list) or not streams:
                continue
            first = streams[0]
            if isinstance(first, dict):
                master_url = first.get("masterUrl")
                if isinstance(master_url, str) and master_url.startswith(("http://", "https://")):
                    return master_url
        return None

    @staticmethod
    def _image_url(image: object) -> str | None:
        if not isinstance(image, dict):
            return None
        for key in ("urlDefault", "url"):
            value = image.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        info_list = image.get("infoList")
        if isinstance(info_list, list) and info_list:
            return first_url(info_list[0])
        return None

    @staticmethod
    def _duration_ms(note: dict[str, Any]) -> int | None:
        video = note.get("video")
        if not isinstance(video, dict):
            return None
        try:
            duration = int(float(video.get("duration") or 0))
        except (TypeError, ValueError):
            return None
        if duration <= 0:
            return None
        return duration if duration > 1000 else duration * 1000
