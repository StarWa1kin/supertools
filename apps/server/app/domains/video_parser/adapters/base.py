from dataclasses import dataclass, field
from typing import Protocol

from app.domains.video_parser.schemas import MediaKind, VideoPlatform


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


class VideoPlatformAdapter(Protocol):
    async def resolve(self, url: str) -> ParsedMedia: ...
