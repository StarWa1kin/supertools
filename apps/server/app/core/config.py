import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(tempfile.gettempdir()) / "supertools"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # The API may be started from the repository root during H5 development.
        # Keep the environment file anchored to the server project so its local
        # networking safeguards are not silently replaced by defaults.
        env_file=SERVER_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", alias="APP_ENV")
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        alias="APP_CORS_ORIGINS",
    )
    codex_watch_account: str = Field(default="tibo", alias="CODEX_WATCH_ACCOUNT")
    codex_watch_keywords: list[str] = Field(
        default=["codex", "quota", "limit", "reset"],
        alias="CODEX_WATCH_KEYWORDS",
    )
    codex_watch_data_dir: Path = Field(
        default=DEFAULT_DATA_ROOT / "codex-watch",
        alias="CODEX_WATCH_DATA_DIR",
    )
    codex_watch_source_url: str = Field(
        default="https://codex-reset.com",
        alias="CODEX_WATCH_SOURCE_URL",
    )
    codex_watch_source_timeout_seconds: float = Field(
        default=8.0,
        alias="CODEX_WATCH_SOURCE_TIMEOUT_SECONDS",
        gt=0,
        le=30,
    )
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="come2u", alias="ADMIN_PASSWORD")
    admin_token_secret: str = Field(
        default="dev-admin-token-secret-change-me",
        alias="ADMIN_TOKEN_SECRET",
        min_length=16,
    )
    admin_token_ttl_seconds: int = Field(
        default=12 * 60 * 60,
        alias="ADMIN_TOKEN_TTL_SECONDS",
        ge=300,
        le=7 * 24 * 60 * 60,
    )
    request_log_data_dir: Path = Field(
        default=DEFAULT_DATA_ROOT / "request-logs",
        alias="REQUEST_LOG_DATA_DIR",
    )
    request_log_max_entries: int = Field(
        default=5000,
        alias="REQUEST_LOG_MAX_ENTRIES",
        ge=100,
        le=100_000,
    )
    request_log_trust_proxy_headers: bool = Field(
        default=False,
        alias="REQUEST_LOG_TRUST_PROXY_HEADERS",
    )
    deploy_service_url: str = Field(default="", alias="DEPLOY_SERVICE_URL")
    deploy_service_token: str = Field(default="", alias="DEPLOY_SERVICE_TOKEN")
    video_parser_timeout_seconds: float = Field(
        default=15.0,
        alias="VIDEO_PARSER_TIMEOUT_SECONDS",
        gt=0,
        le=60,
    )
    video_parser_max_redirects: int = Field(
        default=5,
        alias="VIDEO_PARSER_MAX_REDIRECTS",
        ge=0,
        le=10,
    )
    video_parser_max_response_bytes: int = Field(
        default=5 * 1024 * 1024,
        alias="VIDEO_PARSER_MAX_RESPONSE_BYTES",
        ge=1024,
    )
    video_parser_concurrency: int = Field(
        default=10,
        alias="VIDEO_PARSER_CONCURRENCY",
        ge=1,
        le=100,
    )
    video_parser_resolve_dns: bool = Field(
        default=True,
        alias="VIDEO_PARSER_RESOLVE_DNS",
    )
    video_media_token_ttl_seconds: int = Field(
        default=15 * 60,
        alias="VIDEO_MEDIA_TOKEN_TTL_SECONDS",
        ge=60,
        le=24 * 60 * 60,
    )
    video_media_signing_secret: str = Field(
        default="dev-only-change-me",
        alias="VIDEO_MEDIA_SIGNING_SECRET",
        min_length=16,
    )
    video_media_max_video_bytes: int = Field(
        default=200 * 1024 * 1024,
        alias="VIDEO_MEDIA_MAX_VIDEO_BYTES",
        ge=1024,
    )
    video_media_max_image_bytes: int = Field(
        default=20 * 1024 * 1024,
        alias="VIDEO_MEDIA_MAX_IMAGE_BYTES",
        ge=1024,
    )
    video_media_allowed_hosts: list[str] = Field(
        default=[
            "douyinvod.com",
            "douyinpic.com",
            "aweme.snssdk.com",
            "bytecdn.cn",
            "zjcdn.com",
            "kwimgs.com",
            "kwaicdn.com",
            "kuaishou.com",
            "xhscdn.com",
        ],
        alias="VIDEO_MEDIA_ALLOWED_HOSTS",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
