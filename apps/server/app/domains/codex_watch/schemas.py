from datetime import datetime
from typing import Literal

from pydantic import Field, HttpUrl, field_validator

from app.core.schemas import ApiModel


class WatchPost(ApiModel):
    id: str
    text: str
    translated_text: str | None = None
    url: HttpUrl
    published_at: datetime
    confidence: Literal["official", "third_party", "inferred"]
    matched_keywords: list[str]
    event_type: str = "reset"
    verification_status: str | None = None
    source_label: str | None = None
    official_window_end_at: datetime | None = None
    is_reply: bool = False
    preview: bool = False


class ResetForecast(ApiModel):
    updated_at: datetime
    last_reset_at: datetime | None = None
    probability_24h: int = Field(ge=0, le=100)
    probability_48h: int = Field(ge=0, le=100)
    confidence: Literal["low", "medium", "high"]
    common_window: str | None = None
    recent_median_days: float | None = None
    weighted_mean_days: float | None = None
    accelerating: bool = False
    age_days: float | None = None
    recent_sample: int | None = None
    verified_reset_count: int = 0
    all_time_median_days: float | None = None
    recent_30d_median_days: float | None = None
    longest_wait_days: float | None = None
    model_version: str | None = None


class WatchPostList(ApiModel):
    items: list[WatchPost]
    monitored_account: str
    forecast: ResetForecast | None = None
    source_url: HttpUrl | None = None
    source_updated_at: datetime | None = None
    source_error: bool = False


class CrawlerConfig(ApiModel):
    account: str = Field(min_length=1, max_length=50)
    keywords: list[str] = Field(min_length=1, max_length=30)
    schedule_enabled: bool = True
    interval_minutes: int = Field(default=30, ge=5, le=10080)
    max_posts: int = Field(default=20, ge=1, le=100)

    @field_validator("account")
    @classmethod
    def normalize_account(cls, value: str) -> str:
        account = value.strip().lstrip("@").lower()
        if not account:
            raise ValueError("监控账号不能为空")
        return account

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, values: list[str]) -> list[str]:
        result = list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))
        if not result:
            raise ValueError("至少配置一个关键词")
        return result


class TutorialConfig(ApiModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=160)
    url: HttpUrl


class CommunityConfig(ApiModel):
    title: str = Field(default="AI 技术交流群", min_length=1, max_length=40)
    description: str = Field(default="", max_length=160)
    qr_code: str = Field(default="", max_length=3_000_000)

    @field_validator("qr_code")
    @classmethod
    def validate_qr_code(cls, value: str) -> str:
        qr_code = value.strip()
        if not qr_code:
            return ""
        if qr_code.startswith("data:image/") or qr_code.startswith(("https://", "http://")):
            return qr_code
        raise ValueError("二维码必须是图片或 http(s) 地址")


class ReminderConfig(ApiModel):
    enabled: bool = False
    app_id: str = Field(default="", max_length=128)
    # Ciphertext is longer than the plaintext accepted by the admin form.
    app_secret: str = Field(default="", max_length=1024)
    template_id: str = Field(default="", max_length=256)
    page: str = Field(default="pages/codex-watch/index", max_length=256)
    status_key: str = Field(default="thing1", max_length=64)
    time_key: str = Field(default="time3", max_length=64)
    remark_key: str = Field(default="thing5", max_length=64)


class CodexWatchConfig(ApiModel):
    crawler: CrawlerConfig
    tutorials: list[TutorialConfig] = Field(default_factory=list, max_length=20)
    community: CommunityConfig | None = None
    reminder: ReminderConfig = Field(default_factory=ReminderConfig)
    updated_at: datetime | None = None


class PublicCodexWatchConfig(ApiModel):
    tutorials: list[TutorialConfig]
    community: CommunityConfig | None
    reminder_enabled: bool = False
    reminder_template_id: str | None = None


class ResetReminderSubscriptionRequest(ApiModel):
    code: str = Field(min_length=1, max_length=256)
    template_id: str = Field(min_length=1, max_length=256)


class ResetReminderSubscriptionResponse(ApiModel):
    subscribed: bool
    remaining_deliveries: int
