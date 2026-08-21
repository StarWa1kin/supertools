from datetime import datetime
from typing import Literal

from pydantic import Field

from app.core.schemas import ApiModel
from app.domains.codex_watch.schemas import CodexWatchConfig


class AdminLoginRequest(ApiModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class AdminSession(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    username: str


class AdminCodexWatchConfig(CodexWatchConfig):
    reminder_secret_configured: bool = False


class ReminderSubscriptionSummary(ApiModel):
    id: str
    openid_masked: str
    template_id: str
    subscribed_at: datetime
    remaining_deliveries: int
    last_sent_event_id: str | None = None
    is_current_template: bool = False


class ReminderTestResponse(ApiModel):
    subscription: ReminderSubscriptionSummary


class RequestLogEntry(ApiModel):
    id: int
    requested_at: datetime
    client_ip: str
    method: str
    path: str
    status_code: int
    duration_ms: int
    user_agent: str


class RequestLogPage(ApiModel):
    total: int
    items: list[RequestLogEntry]
