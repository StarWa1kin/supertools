import asyncio
import base64
import binascii
import hashlib
import json
import os
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings, get_settings
from app.domains.codex_watch.schemas import CodexWatchConfig, CrawlerConfig, ReminderConfig


class CodexWatchConfigStore:
    _encrypted_secret_prefix = "enc:v1:"

    def __init__(
        self,
        data_dir: Path,
        default_config: CodexWatchConfig,
        encryption_key: str = "",
    ) -> None:
        self._config_path = data_dir / "config.json"
        self._default_config = default_config
        self._lock = asyncio.Lock()
        self._cipher = self._build_cipher(encryption_key)

    @staticmethod
    def _build_cipher(encryption_key: str) -> Fernet | None:
        if not encryption_key:
            return None
        key = base64.urlsafe_b64encode(hashlib.sha256(encryption_key.encode("utf-8")).digest())
        return Fernet(key)

    async def load(self) -> CodexWatchConfig:
        async with self._lock:
            return await asyncio.to_thread(self._read)

    async def save(self, config: CodexWatchConfig) -> CodexWatchConfig:
        # The admin API intentionally never returns the AppSecret. An empty value
        # therefore means "keep the existing secret", not "erase it".
        if not config.reminder.app_secret:
            current = await self.load()
            config = config.model_copy(
                update={
                    "reminder": config.reminder.model_copy(
                        update={"app_secret": current.reminder.app_secret}
                    )
                }
            )
        saved = config.model_copy(update={"updated_at": datetime.now(UTC)})
        async with self._lock:
            await asyncio.to_thread(self._write, saved)
        return saved

    def _read(self) -> CodexWatchConfig:
        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
            self._decrypt_reminder_secret(payload)
            return CodexWatchConfig.model_validate(payload)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return self._default_config.model_copy(deep=True)

    def _write(self, config: CodexWatchConfig) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._config_path.with_suffix(f".{os.getpid()}.tmp")
        payload = config.model_dump(mode="json", by_alias=True)
        self._encrypt_reminder_secret(payload)
        temporary.write_text(
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n", encoding="utf-8"
        )
        temporary.replace(self._config_path)

    def _encrypt_reminder_secret(self, payload: dict[str, object]) -> None:
        reminder = payload.get("reminder")
        if not isinstance(reminder, dict):
            return
        secret = reminder.get("appSecret")
        if not isinstance(secret, str) or not secret:
            return
        if self._cipher is None:
            raise OSError("未配置 REMINDER_SECRET_ENCRYPTION_KEY，拒绝以明文保存 AppSecret")
        reminder["appSecret"] = self._encrypted_secret_prefix + self._cipher.encrypt(
            secret.encode("utf-8")
        ).decode("utf-8")

    def _decrypt_reminder_secret(self, payload: object) -> None:
        if not isinstance(payload, dict):
            return
        reminder = payload.get("reminder")
        if not isinstance(reminder, dict):
            return
        secret = reminder.get("appSecret")
        if not isinstance(secret, str) or not secret.startswith(self._encrypted_secret_prefix):
            return
        if self._cipher is None:
            raise OSError("缺少 REMINDER_SECRET_ENCRYPTION_KEY，无法读取已加密的 AppSecret")
        token = secret.removeprefix(self._encrypted_secret_prefix)
        try:
            reminder["appSecret"] = self._cipher.decrypt(token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, binascii.Error) as exc:
            raise OSError(
                "无法解密已保存的 AppSecret，请检查 REMINDER_SECRET_ENCRYPTION_KEY"
            ) from exc


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
        reminder=ReminderConfig(),
    )


@lru_cache
def get_codex_watch_store() -> CodexWatchConfigStore:
    settings = get_settings()
    return CodexWatchConfigStore(
        settings.codex_watch_data_dir,
        build_default_config(settings),
        settings.reminder_secret_encryption_key,
    )
