from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.domains.codex_watch.reminders import (
    WechatApiError,
    WechatClient,
    get_reminder_store,
    reminder_is_configured,
)
from app.domains.codex_watch.schemas import (
    PublicCodexWatchConfig,
    ResetReminderSubscriptionRequest,
    ResetReminderSubscriptionResponse,
    WatchPostList,
)
from app.domains.codex_watch.service import CodexWatchService
from app.domains.codex_watch.store import CodexWatchConfigStore, get_codex_watch_store

router = APIRouter()


@router.get("/posts", response_model=WatchPostList)
async def list_posts(
    store: Annotated[CodexWatchConfigStore, Depends(get_codex_watch_store)],
) -> WatchPostList:
    return await CodexWatchService(store).list_posts()


@router.get("/config", response_model=PublicCodexWatchConfig)
async def get_public_config(
    store: Annotated[CodexWatchConfigStore, Depends(get_codex_watch_store)],
) -> PublicCodexWatchConfig:
    return await CodexWatchService(store).get_public_config()


@router.post("/subscriptions", response_model=ResetReminderSubscriptionResponse)
async def subscribe_reset_reminder(
    payload: ResetReminderSubscriptionRequest,
) -> ResetReminderSubscriptionResponse:
    try:
        config = await get_codex_watch_store().load()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="提醒配置暂时无法读取，请稍后重试") from exc
    if not reminder_is_configured(config.reminder):
        raise HTTPException(status_code=503, detail="微信重置提醒尚未配置")
    if payload.template_id != config.reminder.template_id:
        raise HTTPException(status_code=400, detail="订阅消息模板不匹配")
    try:
        openid = await WechatClient(config.reminder).exchange_code(payload.code)
    except WechatApiError as exc:
        raise HTTPException(
            status_code=502,
            detail="微信登录校验失败，请在微信中重新打开小程序后再试",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="暂时无法连接微信服务，请稍后重试") from exc
    try:
        subscription = await get_reminder_store().subscribe(openid, payload.template_id)
    except OSError as exc:
        raise HTTPException(status_code=503, detail="订阅记录暂时无法保存，请稍后重试") from exc
    return ResetReminderSubscriptionResponse(
        subscribed=True,
        remaining_deliveries=subscription.remaining_deliveries,
    )


@router.get("/subscriptions", include_in_schema=False)
async def subscriptions_require_post() -> None:
    raise HTTPException(
        status_code=405,
        detail="此地址仅支持订阅提交，不能直接打开。请在微信小程序中点击“订阅重置提醒”。",
    )
