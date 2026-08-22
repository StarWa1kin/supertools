from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.admin.auth import require_admin
from app.admin.schemas import (
    AdminCodexWatchConfig,
    ReminderSubscriptionSummary,
    ReminderTestResponse,
)
from app.domains.codex_watch.reminders import (
    ReminderSubscription,
    WechatApiError,
    dispatch_test_reset,
    get_reminder_store,
    reminder_is_configured,
)
from app.domains.codex_watch.schemas import CodexWatchConfig
from app.domains.codex_watch.store import CodexWatchConfigStore, get_codex_watch_store

router = APIRouter()


def subscription_summary(
    subscription: ReminderSubscription,
    current_template_id: str = "",
) -> ReminderSubscriptionSummary:
    # Keep OpenID out of the admin response, logs, and browser storage.
    suffix = subscription.openid[-4:] if len(subscription.openid) >= 4 else "****"
    return ReminderSubscriptionSummary(
        id=subscription.id,
        openid_masked=f"用户 ····{suffix}",
        template_id=subscription.template_id,
        subscribed_at=subscription.subscribed_at,
        remaining_deliveries=subscription.remaining_deliveries,
        last_sent_event_id=subscription.last_sent_event_id,
        is_current_template=subscription.template_id == current_template_id,
    )


def protect_reminder_secret(
    config: CodexWatchConfig, store: CodexWatchConfigStore
) -> AdminCodexWatchConfig:
    payload = config.model_dump()
    payload["reminder"]["app_secret"] = store.encrypt_secret_for_client(
        config.reminder.app_secret
    )
    payload["reminder_secret_configured"] = bool(config.reminder.app_secret)
    return AdminCodexWatchConfig.model_validate(payload)


@router.get("/config", response_model=AdminCodexWatchConfig)
async def get_config(
    store: Annotated[CodexWatchConfigStore, Depends(get_codex_watch_store)],
    _admin: Annotated[str, Depends(require_admin)],
) -> AdminCodexWatchConfig:
    try:
        return protect_reminder_secret(await store.load(), store)
    except OSError as exc:
        raise HTTPException(status_code=503, detail="服务端配置暂时无法读取，请稍后重试") from exc


@router.put("/config", response_model=AdminCodexWatchConfig)
async def update_config(
    config: CodexWatchConfig,
    store: Annotated[CodexWatchConfigStore, Depends(get_codex_watch_store)],
    _admin: Annotated[str, Depends(require_admin)],
) -> AdminCodexWatchConfig:
    try:
        current = await store.load()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="服务端配置暂时无法读取，请稍后重试") from exc
    if config.reminder.enabled:
        missing: list[str] = []
        if not config.reminder.app_id:
            missing.append("小程序 AppID")
        if not config.reminder.app_secret and not current.reminder.app_secret:
            missing.append("小程序 AppSecret")
        if not config.reminder.template_id:
            missing.append("订阅消息模板 ID")
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"微信提醒配置不完整，请填写：{'、'.join(missing)}",
            )
    try:
        return protect_reminder_secret(await store.save(config), store)
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail="服务端配置暂时无法保存，请检查 REMINDER_SECRET_ENCRYPTION_KEY",
        ) from exc


@router.get("/reminder-subscriptions", response_model=list[ReminderSubscriptionSummary])
async def list_reminder_subscriptions(
    _admin: Annotated[str, Depends(require_admin)],
) -> list[ReminderSubscriptionSummary]:
    try:
        config = await get_codex_watch_store().load()
        subscriptions = await get_reminder_store().list_subscriptions()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="订阅记录暂时无法读取，请稍后重试") from exc
    return [
        subscription_summary(item, config.reminder.template_id)
        for item in subscriptions
    ]


@router.post("/reminder-subscriptions/{subscription_id}/test", response_model=ReminderTestResponse)
async def test_reminder_subscription(
    subscription_id: str,
    _admin: Annotated[str, Depends(require_admin)],
) -> ReminderTestResponse:
    try:
        config = await get_codex_watch_store().load()
        subscription = await get_reminder_store().get_by_id(subscription_id)
    except OSError as exc:
        raise HTTPException(status_code=503, detail="订阅记录暂时无法读取，请稍后重试") from exc
    if not reminder_is_configured(config.reminder):
        raise HTTPException(
            status_code=409,
            detail="微信提醒配置不完整，请先到“提醒配置”补全并保存",
        )
    if subscription is None:
        raise HTTPException(status_code=404, detail="该订阅记录不存在，请刷新列表后重试")
    if subscription.template_id != config.reminder.template_id:
        raise HTTPException(
            status_code=409,
            detail="该订阅使用的是旧模板，请让用户重新订阅当前模板",
        )
    if subscription.remaining_deliveries <= 0:
        raise HTTPException(status_code=409, detail="该用户的订阅授权次数已用完，请让用户重新订阅")
    try:
        sent_subscription = await dispatch_test_reset(subscription_id)
    except (WechatApiError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail="测试推送失败，请检查微信配置") from exc
    if sent_subscription is None:
        raise HTTPException(status_code=409, detail="订阅状态已变化，请刷新列表后重试")
    return ReminderTestResponse(
        subscription=subscription_summary(sent_subscription, config.reminder.template_id)
    )
