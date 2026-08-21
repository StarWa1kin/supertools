from typing import Literal

from pydantic import Field

from app.core.schemas import ApiModel


class VideoResolveRequest(ApiModel):
    url: str = Field(min_length=1, max_length=2048)


VideoPlatform = Literal["douyin", "kuaishou", "xiaohongshu"]
MediaKind = Literal["video", "image"]


class VideoAuthor(ApiModel):
    name: str = ""
    avatar_url: str | None = None


class VideoAsset(ApiModel):
    kind: MediaKind
    source_url: str
    preview_path: str
    download_path: str


class VideoResolveResult(ApiModel):
    platform: VideoPlatform
    media_type: Literal["video", "images"]
    canonical_url: str
    title: str
    author: VideoAuthor
    duration_ms: int | None = None
    cover_url: str | None = None
    assets: list[VideoAsset]
