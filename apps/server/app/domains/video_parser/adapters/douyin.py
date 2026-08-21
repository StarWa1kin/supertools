import re

from app.clients.safe_http import SafeHttpClient
from app.domains.video_parser.adapters.base import ParsedAsset, ParsedMedia
from app.domains.video_parser.adapters.utils import extract_assignment_json, first_url, walk_dicts
from app.domains.video_parser.errors import parse_error

DOUYIN_HOSTS = ("douyin.com", "iesdouyin.com")


class DouyinAdapter:
    def __init__(self, client: SafeHttpClient) -> None:
        self.client = client

    async def resolve(self, url: str) -> ParsedMedia:
        response = await self.client.get(url, allowed_hosts=DOUYIN_HOSTS)
        state = extract_assignment_json(response.text, "window._ROUTER_DATA")
        ttwid = self._extract_ttwid(response.headers.get_list("set-cookie"))

        content_type, video_id = self._extract_content_id(response.url, response.text)
        if not video_id:
            raise parse_error("无法从抖音分享链接中识别作品 ID")
        if not re.fullmatch(r"\d{17,19}", video_id):
            raise parse_error("抖音作品 ID 格式不正确")

        item = self._find_item(state)
        if item is None:
            share_url = f"https://www.iesdouyin.com/share/{content_type}/{video_id}"
            headers = {"Cookie": ttwid} if ttwid else None
            response = await self.client.get(
                share_url,
                allowed_hosts=DOUYIN_HOSTS,
                headers=headers,
            )
            state = extract_assignment_json(response.text, "window._ROUTER_DATA")
            item = self._find_item(state)
        if item is None:
            raise parse_error("抖音页面未返回公开作品数据")

        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        video = item.get("video") if isinstance(item.get("video"), dict) else {}
        images = item.get("images") if isinstance(item.get("images"), list) else []
        image_urls = [url for image in images if (url := first_url(image))]
        play_url = first_url(video.get("play_addr"))
        duration_ms = self._as_int(video.get("duration"))
        aweme_type = self._as_int(item.get("aweme_type"))
        is_image_post = aweme_type in {1, 2} or not play_url or duration_ms <= 0

        if is_image_post and image_urls:
            assets = [ParsedAsset(kind="image", url=image_url) for image_url in image_urls]
        elif play_url:
            assets = [ParsedAsset(kind="video", url=play_url.replace("playwm", "play"))]
        else:
            raise parse_error("该抖音作品没有可用的视频或图片")

        cover_url = first_url(video.get("cover")) or (image_urls[0] if image_urls else None)
        return ParsedMedia(
            platform="douyin",
            canonical_url=response.url,
            title=str(item.get("desc") or "无标题作品"),
            author_name=str(author.get("nickname") or "未知作者"),
            author_avatar_url=first_url(author.get("avatar_medium")),
            cover_url=cover_url,
            duration_ms=duration_ms or None,
            assets=assets,
        )

    @staticmethod
    def _find_item(state: dict[str, object] | None) -> dict[str, object] | None:
        if not state:
            return None
        for value in walk_dicts(state):
            item_list = value.get("item_list")
            if isinstance(item_list, list) and item_list and isinstance(item_list[0], dict):
                item = item_list[0]
                if "video" in item or "images" in item:
                    return item
        return None

    @staticmethod
    def _extract_content_id(url: str, html: str) -> tuple[str, str | None]:
        for content_type in ("video", "note", "story"):
            match = re.search(rf"/{content_type}/(\d+)", url)
            if match:
                return ("note" if content_type == "note" else "video", match.group(1))
        match = re.search(r"/share/(video|note)/(\d+)", html)
        if match:
            return match.group(1), match.group(2)
        match = re.search(r"\b(\d{17,19})\b", url)
        return "video", match.group(1) if match else None

    @staticmethod
    def _extract_ttwid(cookies: list[str]) -> str:
        for cookie in cookies:
            match = re.search(r"(?:^|[,;]\s*)ttwid=([^;,]+)", cookie)
            if match:
                return f"ttwid={match.group(1)}"
        return ""

    @staticmethod
    def _as_int(value: object) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
