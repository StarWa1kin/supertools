import asyncio
from datetime import datetime
from statistics import median
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from app.domains.codex_watch.schemas import ResetForecast, WatchPost

MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def _confidence(event: dict[str, Any]) -> str:
    if event.get("reset_verification_status") == "rejected":
        return "inferred"
    if event.get("source") == "archive" and event.get("confidence") == "high":
        return "official"
    return "third_party"


def _keywords(event: dict[str, Any], configured: list[str]) -> list[str]:
    haystack = " ".join(
        str(event.get(key, "")) for key in ("summary", "type", "group", "reason_tags")
    ).lower()
    return [keyword for keyword in configured if keyword.lower() in haystack]


def parse_timeline(payload: dict[str, Any], keywords: list[str]) -> list[WatchPost]:
    posts: list[WatchPost] = []
    for event in payload.get("events", []):
        if not isinstance(event, dict) or not event.get("id"):
            continue
        published_at = event.get("announced_at") or event.get("effective_at")
        if not published_at or not event.get("url") or not event.get("summary"):
            continue
        window = event.get("official_window") or {}
        posts.append(
            WatchPost(
                id=str(event["id"]),
                text=str(event["summary"]),
                url=event["url"],
                published_at=published_at,
                confidence=_confidence(event),
                matched_keywords=_keywords(event, keywords),
                event_type=str(event.get("type") or "reset"),
                verification_status=event.get("reset_verification_status"),
                source_label=event.get("source_label"),
                official_window_end_at=window.get("end_at") if isinstance(window, dict) else None,
                preview=bool(event.get("preview")),
            )
        )
    return posts


def _localized_text(tweet: dict[str, Any]) -> str | None:
    for key in ("translated_text", "translation", "text_zh", "localized_text"):
        value = tweet.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    translations = tweet.get("translations")
    if isinstance(translations, dict):
        value = translations.get("zh") or translations.get("zh-CN")
        if isinstance(value, str) and value.strip():
            return value.strip()
    text = tweet.get("text")
    if isinstance(text, str) and any("\u4e00" <= char <= "\u9fff" for char in text):
        return text.strip()
    return None


def parse_feed(
    payload: dict[str, Any],
    timeline_posts: list[WatchPost],
    keywords: list[str],
) -> list[WatchPost]:
    """Merge the localized live feed with timeline verification evidence."""
    evidence = {post.id: post for post in timeline_posts}
    posts: list[WatchPost] = []
    for tweet in payload.get("tweets", []):
        if not isinstance(tweet, dict) or not tweet.get("id"):
            continue
        tweet_id = str(tweet["id"])
        verified = evidence.get(tweet_id)
        localized = _localized_text(tweet)
        raw_text = tweet.get("original_text") or tweet.get("text")
        # The locale=zh endpoint may localize `text` in place.
        if localized is None and payload.get("locale") in {"zh", "zh-CN"}:
            localized = str(tweet.get("text") or "").strip() or None
        if not raw_text or not tweet.get("url") or not tweet.get("at"):
            continue
        event = {
            "summary": raw_text,
            "type": tweet.get("kind"),
            "group": tweet.get("tibo_lane"),
        }
        posts.append(
            WatchPost(
                id=tweet_id,
                text=verified.text if verified else str(raw_text),
                translated_text=localized,
                url=tweet["url"],
                published_at=tweet["at"],
                confidence=(
                    verified.confidence
                    if verified
                    else "third_party"
                    if tweet.get("explicit_reset_claim")
                    else "inferred"
                ),
                matched_keywords=_keywords(event, keywords),
                event_type=verified.event_type if verified else str(tweet.get("kind") or "other"),
                verification_status=verified.verification_status if verified else None,
                source_label=verified.source_label if verified else "Tibo live feed",
                official_window_end_at=(verified.official_window_end_at if verified else None),
                is_reply=bool(tweet.get("is_reply")),
                preview=verified.preview if verified else False,
            )
        )
    return posts


def _timeline_stats(
    timeline: dict[str, Any] | None,
) -> tuple[int, float | None, float | None, float | None]:
    if not timeline:
        return 0, None, None, None
    dates: list[datetime] = []
    for event in timeline.get("events", []):
        if not isinstance(event, dict):
            continue
        is_verified = event.get("source") == "archive" and event.get("confidence") == "high"
        if not is_verified or event.get("type") not in {"reset", "promo"}:
            continue
        value = event.get("effective_at") or event.get("announced_at")
        if value:
            dates.append(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    dates.sort()
    intervals = [
        (right - left).total_seconds() / 86400
        for left, right in zip(dates, dates[1:], strict=False)
    ]
    updated_value = timeline.get("updated_at")
    updated_at = (
        datetime.fromisoformat(str(updated_value).replace("Z", "+00:00"))
        if updated_value
        else datetime.now().astimezone()
    )
    recent_dates = [date for date in dates if (updated_at - date).total_seconds() <= 30 * 86400]
    recent_intervals = [
        (right - left).total_seconds() / 86400
        for left, right in zip(recent_dates, recent_dates[1:], strict=False)
    ]
    return (
        len(dates),
        round(median(intervals), 1) if intervals else None,
        round(median(recent_intervals), 1) if recent_intervals else None,
        round(max(intervals), 1) if intervals else None,
    )


def parse_forecast(
    payload: dict[str, Any], timeline: dict[str, Any] | None = None
) -> ResetForecast:
    probabilities = payload.get("probabilities") or {}
    cadence = payload.get("cadence") or {}
    window = payload.get("time_window") or {}
    model = payload.get("model") or {}
    verified_count, all_median, recent_median, longest_wait = _timeline_stats(timeline)
    return ResetForecast(
        updated_at=payload["updated_at"],
        last_reset_at=payload.get("last_reset_at"),
        probability_24h=int(probabilities.get("rounded_24h", 0)),
        probability_48h=int(probabilities.get("rounded_48h", 0)),
        confidence=payload.get("confidence", "low"),
        common_window=window.get("label"),
        recent_median_days=cadence.get("recent_median_days"),
        weighted_mean_days=cadence.get("weighted_mean_days"),
        accelerating=bool(cadence.get("accelerating")),
        age_days=payload.get("age_days"),
        recent_sample=cadence.get("recent_sample"),
        verified_reset_count=verified_count,
        all_time_median_days=all_median,
        recent_30d_median_days=recent_median,
        longest_wait_days=longest_wait,
        model_version=model.get("version"),
    )


class CodexResetSource:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" or parsed.hostname != "codex-reset.com":
            raise ValueError("Codex 情报源必须使用 https://codex-reset.com")
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5))

    async def _get_json(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=False,
            headers={"Accept": "application/json", "User-Agent": "Supertools-CodexWatch/1.0"},
        ) as client:
            response = await client.get(urljoin(self.base_url, path.lstrip("/")))
            response.raise_for_status()
            if len(response.content) > MAX_RESPONSE_BYTES:
                raise ValueError("Codex 情报源响应过大")
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Codex 情报源响应格式错误")
            return payload

    async def fetch(self, keywords: list[str]) -> tuple[list[WatchPost], ResetForecast, datetime]:
        timeline, feed, forecast = await asyncio.gather(
            self._get_json("api/timeline"),
            self._get_json("api/feed?_fresh=1&locale=zh"),
            self._get_json("api/forecast"),
        )
        updated_at = datetime.fromisoformat(str(timeline["updated_at"]).replace("Z", "+00:00"))
        timeline_posts = parse_timeline(timeline, keywords)
        live_posts = parse_feed(feed, timeline_posts, keywords)
        live_ids = {post.id for post in live_posts}
        merged = live_posts + [post for post in timeline_posts if post.id not in live_ids]
        merged.sort(key=lambda post: post.published_at, reverse=True)
        return merged, parse_forecast(forecast, timeline), updated_at
