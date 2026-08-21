import asyncio
import json
import os
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.domains.codex_watch.schemas import ReminderConfig, WatchPost
from app.domains.codex_watch.source import CodexResetSource
from app.domains.codex_watch.store import get_codex_watch_store

WECHAT_API = "https://api.weixin.qq.com"


class WechatApiError(RuntimeError):
    def __init__(self, message: str, errcode: int | None = None) -> None:
        super().__init__(message)
        self.errcode = errcode


class ReminderSubscription(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    openid: str
    template_id: str
    subscribed_at: datetime
    remaining_deliveries: int = Field(default=1, ge=0, le=100)
    last_sent_event_id: str | None = None


class ReminderState(BaseModel):
    subscriptions: list[ReminderSubscription] = Field(default_factory=list)


class ReminderStore:
    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "reminders.json"
        self._lock = asyncio.Lock()

    async def subscribe(self, openid: str, template_id: str) -> ReminderSubscription:
        async with self._lock:
            state = await asyncio.to_thread(self._read)
            existing = next(
                (
                    item
                    for item in state.subscriptions
                    if item.openid == openid and item.template_id == template_id
                ),
                None,
            )
            if existing:
                existing.subscribed_at = datetime.now(UTC)
                existing.remaining_deliveries = min(existing.remaining_deliveries + 1, 100)
            else:
                existing = ReminderSubscription(
                    openid=openid,
                    template_id=template_id,
                    subscribed_at=datetime.now(UTC),
                )
                state.subscriptions.append(existing)
            await asyncio.to_thread(self._write, state)
            return existing.model_copy()

    async def active_for(self, event: WatchPost) -> list[ReminderSubscription]:
        async with self._lock:
            state = await asyncio.to_thread(self._read)
            return [
                item.model_copy()
                for item in state.subscriptions
                if item.remaining_deliveries > 0
                and item.subscribed_at < event.published_at
                and item.last_sent_event_id != event.id
            ]

    async def list_subscriptions(self) -> list[ReminderSubscription]:
        async with self._lock:
            state = await asyncio.to_thread(self._read)
            return [item.model_copy() for item in state.subscriptions]

    async def get_by_id(self, subscription_id: str) -> ReminderSubscription | None:
        async with self._lock:
            state = await asyncio.to_thread(self._read)
            subscription = next(
                (item for item in state.subscriptions if item.id == subscription_id),
                None,
            )
            return subscription.model_copy() if subscription else None

    async def mark_sent(self, openid: str, template_id: str, event_id: str) -> None:
        async with self._lock:
            state = await asyncio.to_thread(self._read)
            for item in state.subscriptions:
                if item.openid == openid and item.template_id == template_id:
                    item.remaining_deliveries = max(0, item.remaining_deliveries - 1)
                    item.last_sent_event_id = event_id
                    break
            await asyncio.to_thread(self._write, state)

    def _read(self) -> ReminderState:
        try:
            payload = self._path.read_text(encoding="utf-8")
            state = ReminderState.model_validate_json(payload)
            # Persist generated IDs for subscriptions saved before the admin test
            # screen was introduced; otherwise their IDs would change on every read.
            raw_subscriptions = json.loads(payload).get("subscriptions", [])
            if any("id" not in item for item in raw_subscriptions if isinstance(item, dict)):
                self._write(state)
            return state
        except (FileNotFoundError, ValueError):
            return ReminderState()

    def _write(self, state: ReminderState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self._path)


class WechatClient:
    def __init__(
        self, settings: ReminderConfig, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.settings = settings
        self._transport = transport
        self._access_token = ""
        self._access_token_expires_at = datetime.min.replace(tzinfo=UTC)
        self._token_lock = asyncio.Lock()

    async def exchange_code(self, code: str) -> str:
        payload = await self._request(
            "GET",
            "/sns/jscode2session",
            params={
                "appid": self.settings.app_id,
                "secret": self.settings.app_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        openid = payload.get("openid")
        if not isinstance(openid, str) or not openid:
            raise WechatApiError("微信登录未返回用户标识", payload.get("errcode"))
        return openid

    async def send_reset(
        self,
        subscription: ReminderSubscription,
        event: WatchPost,
        *,
        is_test: bool = False,
    ) -> None:
        token = await self._get_access_token()
        settings = self.settings
        await self._request(
            "POST",
            "/cgi-bin/message/subscribe/send",
            params={"access_token": token},
            json={
                "touser": subscription.openid,
                "template_id": subscription.template_id,
                "page": settings.page,
                "miniprogram_state": "formal",
                "lang": "zh_CN",
                "data": {
                    settings.status_key: {
                        "value": "【测试】Codex 全局额度已重置"
                        if is_test
                        else "Codex 全局额度已重置"
                    },
                    settings.time_key: {
                        "value": event.published_at.astimezone().strftime("%Y-%m-%d %H:%M")
                    },
                    settings.remark_key: {
                        "value": "这是管理员发起的测试消息" if is_test else "打开小程序查看适用范围"
                    },
                },
            },
        )

    async def _get_access_token(self) -> str:
        async with self._token_lock:
            if self._access_token and datetime.now(UTC) < self._access_token_expires_at:
                return self._access_token
            payload = await self._request(
                "GET",
                "/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": self.settings.app_id,
                    "secret": self.settings.app_secret,
                },
            )
            token = payload.get("access_token")
            if not isinstance(token, str) or not token:
                raise WechatApiError("微信访问令牌获取失败", payload.get("errcode"))
            expires_in = int(payload.get("expires_in", 7200))
            self._access_token = token
            self._access_token_expires_at = datetime.now(UTC) + timedelta(
                seconds=max(60, expires_in - 300)
            )
            return token

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=WECHAT_API,
            timeout=httpx.Timeout(10, connect=5),
            transport=self._transport,
        ) as client:
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, dict):
            raise WechatApiError("微信接口响应格式错误")
        errcode = payload.get("errcode", 0)
        if errcode not in (None, 0):
            raise WechatApiError(str(payload.get("errmsg") or "微信接口调用失败"), int(errcode))
        return payload


def reminder_is_configured(settings: ReminderConfig) -> bool:
    return bool(
        settings.enabled
        and settings.app_id
        and settings.app_secret
        and settings.template_id
    )


@lru_cache
def get_reminder_store() -> ReminderStore:
    return ReminderStore(get_settings().codex_watch_data_dir)


async def dispatch_confirmed_reset(event: WatchPost) -> int:
    config = await get_codex_watch_store().load()
    if not reminder_is_configured(config.reminder):
        return 0
    store = get_reminder_store()
    client = WechatClient(config.reminder)
    sent = 0
    for subscription in await store.active_for(event):
        try:
            await client.send_reset(subscription, event)
        except (httpx.HTTPError, WechatApiError):
            continue
        await store.mark_sent(subscription.openid, subscription.template_id, event.id)
        sent += 1
    return sent


async def dispatch_test_reset(subscription_id: str) -> ReminderSubscription | None:
    """Send one real, explicitly requested test message to a single subscription.

    A WeChat subscription message authorization is one-time.  The test therefore
    follows the same send-and-consume semantics as a production reset alert.
    """
    config = await get_codex_watch_store().load()
    if not reminder_is_configured(config.reminder):
        return None
    store = get_reminder_store()
    subscription = await store.get_by_id(subscription_id)
    if subscription is None or subscription.remaining_deliveries <= 0:
        return None

    event = WatchPost(
        id=f"admin-test-{uuid4().hex}",
        text="Admin requested Codex reset reminder test",
        url="https://codex-reset.com",
        published_at=datetime.now(UTC),
        confidence="official",
        matched_keywords=["test"],
        event_type="reset",
    )
    await WechatClient(config.reminder).send_reset(subscription, event, is_test=True)
    await store.mark_sent(subscription.openid, subscription.template_id, event.id)
    return await store.get_by_id(subscription_id)


def latest_confirmed_reset(posts: list[WatchPost]) -> WatchPost | None:
    candidates = [
        post
        for post in posts
        if post.confidence == "official"
        and post.event_type in {"reset", "promo"}
        and not post.preview
        and post.verification_status != "rejected"
    ]
    return max(candidates, key=lambda post: post.published_at, default=None)


async def _monitor_loop() -> None:
    settings = get_settings()
    source = CodexResetSource(
        settings.codex_watch_source_url,
        settings.codex_watch_source_timeout_seconds,
    )
    while True:
        config = await get_codex_watch_store().load()
        if config.crawler.schedule_enabled and reminder_is_configured(config.reminder):
            try:
                posts, _, _ = await source.fetch(config.crawler.keywords)
                event = latest_confirmed_reset(posts)
                if event:
                    await dispatch_confirmed_reset(event)
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                pass
        await asyncio.sleep(max(60, config.crawler.interval_minutes * 60))


_monitor_task: asyncio.Task[None] | None = None


def start_reminder_monitor() -> None:
    global _monitor_task
    if _monitor_task is None:
        _monitor_task = asyncio.create_task(_monitor_loop(), name="codex-reset-reminders")


async def stop_reminder_monitor() -> None:
    global _monitor_task
    if _monitor_task is None:
        return
    _monitor_task.cancel()
    with suppress(asyncio.CancelledError):
        await _monitor_task
    _monitor_task = None
