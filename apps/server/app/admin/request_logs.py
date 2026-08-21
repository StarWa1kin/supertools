import sqlite3
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings, get_settings


class RequestLogStore:
    def __init__(self, data_dir: Path, max_entries: int) -> None:
        self._path = data_dir / "requests.sqlite3"
        self._max_entries = max_entries
        data_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requested_at TEXT NOT NULL,
                    client_ip TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    user_agent TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_request_logs_requested_at "
                "ON request_logs(requested_at DESC)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def add(
        self,
        *,
        client_ip: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: int,
        user_agent: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO request_logs
                (requested_at, client_ip, method, path, status_code, duration_ms, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(UTC).isoformat(),
                    client_ip[:64],
                    method[:12],
                    path[:500],
                    status_code,
                    duration_ms,
                    user_agent[:300],
                ),
            )
            connection.execute(
                """
                DELETE FROM request_logs
                WHERE id NOT IN (
                    SELECT id FROM request_logs ORDER BY id DESC LIMIT ?
                )
                """,
                (self._max_entries,),
            )

    def list(
        self,
        *,
        limit: int,
        offset: int,
        status: int | None,
        path: str | None,
    ) -> tuple[int, list[dict[str, object]]]:
        clauses: list[str] = []
        values: list[object] = []
        if status is not None:
            clauses.append("status_code = ?")
            values.append(status)
        if path:
            clauses.append("path LIKE ?")
            values.append(f"%{path}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) FROM request_logs {where}", values
            ).fetchone()[0]
            rows = connection.execute(
                f"SELECT * FROM request_logs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                [*values, limit, offset],
            ).fetchall()
        return total, [dict(row) for row in rows]


def get_request_log_store(settings: Settings | None = None) -> RequestLogStore:
    configured = settings or get_settings()
    return RequestLogStore(configured.request_log_data_dir, configured.request_log_max_entries)


def iter_request_log_store(
    settings: Settings | None = None,
) -> Generator[RequestLogStore, None, None]:
    yield get_request_log_store(settings)
