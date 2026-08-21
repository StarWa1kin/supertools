from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.admin.auth import require_admin
from app.admin.schemas import ReminderSubscriptionSummary, ReminderTestResponse
from app.domains.codex_watch.reminders import (
    ReminderSubscription,
    WechatApiError,
    dispatch_test_reset,
    get_reminder_store,
)
from app.domains.codex_watch.schemas import CodexWatchConfig
from app.domains.codex_watch.store import CodexWatchConfigStore, get_codex_watch_store

router = APIRouter()


def subscription_summary(subscription: ReminderSubscription) -> ReminderSubscriptionSummary:
    # Keep OpenID out of the admin response, logs, and browser storage.
    suffix = subscription.openid[-4:] if len(subscription.openid) >= 4 else "****"
    return ReminderSubscriptionSummary(
        id=subscription.id,
        openid_masked=f"用户 ····{suffix}",
        template_id=subscription.template_id,
        subscribed_at=subscription.subscribed_at,
        remaining_deliveries=subscription.remaining_deliveries,
        last_sent_event_id=subscription.last_sent_event_id,
    )


def redact_reminder_secret(config: CodexWatchConfig) -> CodexWatchConfig:
    reminder = config.reminder.model_copy(update={"app_secret": ""})
    return config.model_copy(update={"reminder": reminder})


@router.get("/config", response_model=CodexWatchConfig)
async def get_config(
    store: Annotated[CodexWatchConfigStore, Depends(get_codex_watch_store)],
    _admin: Annotated[str, Depends(require_admin)],
) -> CodexWatchConfig:
    return redact_reminder_secret(await store.load())


@router.put("/config", response_model=CodexWatchConfig)
async def update_config(
    config: CodexWatchConfig,
    store: Annotated[CodexWatchConfigStore, Depends(get_codex_watch_store)],
    _admin: Annotated[str, Depends(require_admin)],
) -> CodexWatchConfig:
    return redact_reminder_secret(await store.save(config))


@router.get("/reminder-subscriptions", response_model=list[ReminderSubscriptionSummary])
async def list_reminder_subscriptions(
    _admin: Annotated[str, Depends(require_admin)],
) -> list[ReminderSubscriptionSummary]:
    subscriptions = await get_reminder_store().list_subscriptions()
    return [subscription_summary(item) for item in subscriptions]


@router.post("/reminder-subscriptions/{subscription_id}/test", response_model=ReminderTestResponse)
async def test_reminder_subscription(
    subscription_id: str,
    _admin: Annotated[str, Depends(require_admin)],
) -> ReminderTestResponse:
    try:
        subscription = await dispatch_test_reset(subscription_id)
    except (WechatApiError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail="测试推送失败，请检查微信配置") from exc
    if subscription is None:
        raise HTTPException(status_code=409, detail="该订阅不存在或可用推送次数已用完")
    return ReminderTestResponse(subscription=subscription_summary(subscription))
