import asyncio
import json
import os
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from app.core.config import Settings, get_settings
from app.domains.codex_watch.schemas import CodexWatchConfig, CrawlerConfig


class CodexWatchConfigStore:
    def __init__(self, data_dir: Path, default_config: CodexWatchConfig) -> None:
        self._config_path = data_dir / "config.json"
        self._default_config = default_config
        self._lock = asyncio.Lock()

    async def load(self) -> CodexWatchConfig:
        async with self._lock:
            return await asyncio.to_thread(self._read)

    async def save(self, config: CodexWatchConfig) -> CodexWatchConfig:
        saved = config.model_copy(update={"updated_at": datetime.now(UTC)})
        async with self._lock:
            await asyncio.to_thread(self._write, saved)
        return saved

    def _read(self) -> CodexWatchConfig:
        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
            return CodexWatchConfig.model_validate(payload)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return self._default_config.model_copy(deep=True)

    def _write(self, config: CodexWatchConfig) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._config_path.with_suffix(f".{os.getpid()}.tmp")
        payload = config.model_dump(mode="json", by_alias=True)
        temporary.write_text(
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n", encoding="utf-8"
        )
        temporary.replace(self._config_path)


def build_default_config(settings: Settings) -> CodexWatchConfig:
    return CodexWatchConfig(
        crawler=CrawlerConfig(
            account=settings.codex_watch_account,
            keywords=settings.codex_watch_keywords,
            schedule_enabled=True,
            interval_minutes=30,
            max_posts=20,
        ),
        tutorials=[],
        community=None,
    )


@lru_cache
def get_codex_watch_store() -> CodexWatchConfigStore:
    settings = get_settings()
    return CodexWatchConfigStore(
        settings.codex_watch_data_dir,
        build_default_config(settings),
    )
