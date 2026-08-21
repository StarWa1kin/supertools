"""Platform-specific public link adapters."""

from app.domains.video_parser.adapters.douyin import DouyinAdapter
from app.domains.video_parser.adapters.kuaishou import KuaishouAdapter
from app.domains.video_parser.adapters.xiaohongshu import XiaohongshuAdapter

__all__ = ["DouyinAdapter", "KuaishouAdapter", "XiaohongshuAdapter"]
