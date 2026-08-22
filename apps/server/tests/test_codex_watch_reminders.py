import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from app.domains.codex_watch.reminders import ReminderStore, WechatClient, latest_confirmed_reset
from app.domains.codex_watch.schemas import (
    CodexWatchConfig,
    CrawlerConfig,
    ReminderConfig,
    WatchPost,
)
from app.domains.codex_watch.service import CodexWatchService
from app.domains.codex_watch.store import CodexWatchConfigStore


def make_post(**updates: object) -> WatchPost:
    values: dict[str, object] = {
        "id": "reset-1",
        "text": "Usage limits reset",
        "url": "https://x.com/thsottiaux/status/reset-1",
        "published_at": datetime.now(UTC) + timedelta(minutes=1),
        "confidence": "official",
        "matched_keywords": ["reset"],
        "event_type": "reset",
    }
    values.update(updates)
    return WatchPost.model_validate(values)


def test_subscription_is_consumed_after_mark_sent(tmp_path: Path) -> None:
    async def scenario() -> None:
        store = ReminderStore(tmp_path)
        subscription = await store.subscribe("openid-1", "template-1")
        event = make_post()

        assert subscription.remaining_deliveries == 1
        assert len(await store.active_for(event)) == 1

        await store.mark_sent("openid-1", "template-1", event.id)

        assert await store.active_for(event) == []

    asyncio.run(scenario())


def test_legacy_subscription_gets_a_stable_id_for_admin_testing(tmp_path: Path) -> None:
    (tmp_path / "reminders.json").write_text(
        """{
  "subscriptions": [{
    "openid": "openid-legacy",
    "template_id": "template-1",
    "subscribed_at": "2026-08-20T00:00:00Z"
  }]
}""",
        encoding="utf-8",
    )

    async def scenario() -> None:
        store = ReminderStore(tmp_path)
        first = (await store.list_subscriptions())[0]
        second = (await store.list_subscriptions())[0]

        assert first.id == second.id
        assert (await store.get_by_id(first.id)) is not None

    asyncio.run(scenario())


def test_latest_confirmed_reset_rejects_previews_and_unverified_posts() -> None:
    result = latest_confirmed_reset(
        [
            make_post(id="preview", preview=True),
            make_post(id="third-party", confidence="third_party"),
            make_post(id="confirmed", published_at=datetime.now(UTC)),
        ]
    )

    assert result is not None
    assert result.id == "confirmed"


def test_empty_secret_preserves_the_existing_reminder_secret(tmp_path: Path) -> None:
    async def scenario() -> None:
        store = CodexWatchConfigStore(
            tmp_path,
            CodexWatchConfig(crawler=CrawlerConfig(account="tibo", keywords=["reset"])),
            encryption_key="test-encryption-key",
        )
        await store.save(
            CodexWatchConfig(
                crawler=CrawlerConfig(account="tibo", keywords=["reset"]),
                reminder=ReminderConfig(app_secret="kept-secret"),
            )
        )
        saved = await store.save(
            CodexWatchConfig(
                crawler=CrawlerConfig(account="tibo", keywords=["reset"]),
                reminder=ReminderConfig(enabled=True),
            )
        )

        assert saved.reminder.enabled is True
        assert saved.reminder.app_secret == "kept-secret"

    asyncio.run(scenario())


def test_app_secret_is_encrypted_at_rest_and_decrypted_when_loaded(tmp_path: Path) -> None:
    async def scenario() -> None:
        default = CodexWatchConfig(crawler=CrawlerConfig(account="tibo", keywords=["reset"]))
        store = CodexWatchConfigStore(tmp_path, default, encryption_key="test-encryption-key")
        config = CodexWatchConfig(
            crawler=CrawlerConfig(account="tibo", keywords=["reset"]),
            reminder=ReminderConfig(app_secret="wechat-secret"),
        )

        await store.save(config)
        raw = (tmp_path / "config.json").read_text(encoding="utf-8")

        assert "wechat-secret" not in raw
        assert "enc:v1:" in raw
        assert (await store.load()).reminder.app_secret == "wechat-secret"

    asyncio.run(scenario())


def test_public_config_hides_reminders_when_the_app_secret_is_missing(tmp_path: Path) -> None:
    async def scenario() -> None:
        store = CodexWatchConfigStore(
            tmp_path,
            CodexWatchConfig(crawler=CrawlerConfig(account="tibo", keywords=["reset"])),
            encryption_key="test-encryption-key",
        )
        await store.save(
            CodexWatchConfig(
                crawler=CrawlerConfig(account="tibo", keywords=["reset"]),
                reminder=ReminderConfig(
                    enabled=True,
                    app_id="wx-test",
                    template_id="template-1",
                ),
            )
        )

        public_config = await CodexWatchService(store).get_public_config()

        assert public_config.reminder_enabled is False
        assert public_config.reminder_template_id is None

    asyncio.run(scenario())


def test_wechat_client_exchanges_code_and_sends_message(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/sns/jscode2session":
            return httpx.Response(200, json={"openid": "openid-1"})
        if request.url.path == "/cgi-bin/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 7200})
        return httpx.Response(200, json={"errcode": 0, "errmsg": "ok"})

    settings = ReminderConfig(
        enabled=True,
        app_id="app-id",
        app_secret="app-secret",
        template_id="template-1",
    )

    async def scenario() -> str:
        client = WechatClient(settings, transport=httpx.MockTransport(handler))
        openid = await client.exchange_code("login-code")
        subscription = await ReminderStore(tmp_path).subscribe(openid, "template-1")

        await client.send_reset(subscription, make_post())
        return openid

    openid = asyncio.run(scenario())
    assert openid == "openid-1"
    assert [request.url.path for request in requests] == [
        "/sns/jscode2session",
        "/cgi-bin/token",
        "/cgi-bin/message/subscribe/send",
    ]
