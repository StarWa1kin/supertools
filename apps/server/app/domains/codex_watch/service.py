import httpx

from app.core.config import get_settings
from app.domains.codex_watch.schemas import PublicCodexWatchConfig, WatchPostList
from app.domains.codex_watch.source import CodexResetSource
from app.domains.codex_watch.store import CodexWatchConfigStore


class CodexWatchService:
    """Coordinates collection and filtering once a public data source is configured."""

    def __init__(self, store: CodexWatchConfigStore) -> None:
        self.store = store

    async def list_posts(self) -> WatchPostList:
        config = await self.store.load()
        settings = get_settings()
        source = CodexResetSource(
            settings.codex_watch_source_url,
            settings.codex_watch_source_timeout_seconds,
        )
        try:
            items, forecast, updated_at = await source.fetch(config.crawler.keywords)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return WatchPostList(
                items=[],
                monitored_account=config.crawler.account,
                source_url=settings.codex_watch_source_url,
                source_error=True,
            )
        return WatchPostList(
            items=items[: config.crawler.max_posts],
            monitored_account=config.crawler.account,
            forecast=forecast,
            source_url=settings.codex_watch_source_url,
            source_updated_at=updated_at,
        )

    async def get_public_config(self) -> PublicCodexWatchConfig:
        config = await self.store.load()
        community = config.community if config.community and config.community.qr_code else None
        reminder_enabled = bool(
            config.reminder.enabled and config.reminder.template_id
        )
        return PublicCodexWatchConfig(
            tutorials=config.tutorials,
            community=community,
            reminder_enabled=reminder_enabled,
            reminder_template_id=(config.reminder.template_id if reminder_enabled else None),
        )
