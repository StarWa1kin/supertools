import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.domains.codex_watch import reminders
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


def test_client_encrypted_app_secret_can_be_saved_again(tmp_path: Path) -> None:
    async def scenario() -> None:
        default = CodexWatchConfig(crawler=CrawlerConfig(account="tibo", keywords=["reset"]))
        store = CodexWatchConfigStore(tmp_path, default, encryption_key="test-encryption-key")
        encrypted = store.encrypt_secret_for_client("wechat-secret")

        await store.save(
            CodexWatchConfig(
                crawler=CrawlerConfig(account="tibo", keywords=["reset"]),
                reminder=ReminderConfig(app_secret=encrypted),
            )
        )

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


def test_resubscribing_keeps_the_time_of_unused_authorizations(tmp_path: Path) -> None:
    async def scenario() -> None:
        store = ReminderStore(tmp_path)
        first = await store.subscribe("openid-1", "template-1")
        event = make_post(published_at=datetime.now(UTC))
        # Tapping subscribe again after the reset was announced must not hide it.
        second = await store.subscribe("openid-1", "template-1")

        assert second.subscribed_at == first.subscribed_at
        assert second.remaining_deliveries == 2
        assert len(await store.active_for(event)) == 1

    asyncio.run(scenario())


def test_resubscribing_after_all_authorizations_are_used_restarts_the_clock(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        store = ReminderStore(tmp_path)
        first = await store.subscribe("openid-1", "template-1")
        await store.mark_sent("openid-1", "template-1", "reset-1")
        second = await store.subscribe("openid-1", "template-1")

        assert second.subscribed_at > first.subscribed_at

    asyncio.run(scenario())


def test_latest_confirmed_reset_ignores_stale_events() -> None:
    now = datetime.now(UTC)

    assert latest_confirmed_reset([make_post(published_at=now - timedelta(days=5))], now) is None
    fresh = latest_confirmed_reset([make_post(published_at=now - timedelta(hours=2))], now)
    assert fresh is not None


def configured_store(tmp_path: Path) -> CodexWatchConfigStore:
    return CodexWatchConfigStore(
        tmp_path,
        CodexWatchConfig(
            crawler=CrawlerConfig(account="tibo", keywords=["reset"]),
            reminder=ReminderConfig(
                enabled=True,
                app_id="app-id",
                app_secret="app-secret",
                template_id="template-1",
            ),
        ),
    )


def test_dispatch_drops_subscriptions_wechat_reports_as_unauthorized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cgi-bin/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 7200})
        return httpx.Response(200, json={"errcode": 43101, "errmsg": "user refuse to accept"})

    reminder_store = ReminderStore(tmp_path)
    monkeypatch.setattr(reminders, "get_codex_watch_store", lambda: configured_store(tmp_path))
    monkeypatch.setattr(reminders, "get_reminder_store", lambda: reminder_store)
    monkeypatch.setattr(
        reminders,
        "WechatClient",
        lambda settings: WechatClient(settings, transport=httpx.MockTransport(handler)),
    )

    async def scenario() -> None:
        await reminder_store.subscribe("openid-1", "template-1")
        sent = await reminders.dispatch_confirmed_reset(make_post())

        assert sent == 0
        assert (await reminder_store.list_subscriptions())[0].remaining_deliveries == 0

    asyncio.run(scenario())


def test_monitor_loop_survives_unexpected_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    # An OSError (e.g. an unreadable config) used to end the task for good.
    sleeps = 0

    async def fake_sleep(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps >= 2:
            raise asyncio.CancelledError

    class BrokenStore:
        async def load(self) -> None:
            raise OSError("config temporarily unreadable")

    monkeypatch.setattr(reminders, "get_codex_watch_store", lambda: BrokenStore())
    monkeypatch.setattr(reminders.asyncio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(reminders._monitor_loop())
    assert sleeps == 2
