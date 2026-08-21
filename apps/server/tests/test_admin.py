from pathlib import Path

from fastapi.testclient import TestClient

from app.admin.deployment import get_deployment_service
from app.admin.request_logs import RequestLogStore, iter_request_log_store
from app.core.config import get_settings
from app.domains.codex_watch.store import (
    CodexWatchConfigStore,
    build_default_config,
    get_codex_watch_store,
)
from app.main import app

client = TestClient(app)


def test_admin_login_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "账号或密码错误"


def test_admin_config_requires_login() -> None:
    response = client.get("/api/v1/admin/codex-watch/config")

    assert response.status_code == 401


def test_admin_deployment_requires_login() -> None:
    response = client.post("/api/v1/admin/deployment/server")

    assert response.status_code == 401


def test_admin_request_logs_are_protected_and_filterable(tmp_path: Path) -> None:
    store = RequestLogStore(tmp_path, max_entries=100)
    store.add(
        client_ip="203.0.113.8",
        method="POST",
        path="/api/v1/video-parser/resolve",
        status_code=200,
        duration_ms=42,
        user_agent="pytest",
    )
    app.dependency_overrides[iter_request_log_store] = lambda: store
    try:
        rejected = client.get("/api/v1/admin/request-logs")
        assert rejected.status_code == 401

        session = client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "come2u"},
        )
        response = client.get(
            "/api/v1/admin/request-logs?status=200&path=video-parser",
            headers={"Authorization": f"Bearer {session.json()['accessToken']}"},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["clientIp"] == "203.0.113.8"
        assert response.json()["items"][0]["durationMs"] == 42
    finally:
        app.dependency_overrides.clear()


def test_admin_can_start_and_read_deployment() -> None:
    class FakeDeploymentService:
        async def start(self, target: str) -> dict[str, object]:
            return {
                "status": "running",
                "target": target,
                "startedAt": "2026-08-20T10:00:00Z",
                "log": "",
            }

        async def status(self) -> dict[str, object]:
            return {"status": "succeeded", "finishedAt": "2026-08-20T10:01:00Z", "log": "ok"}

    app.dependency_overrides[get_deployment_service] = lambda: FakeDeploymentService()
    try:
        session = client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "come2u"},
        )
        headers = {"Authorization": f"Bearer {session.json()['accessToken']}"}

        started = client.post("/api/v1/admin/deployment/server", headers=headers)
        status = client.get("/api/v1/admin/deployment/status", headers=headers)

        assert started.status_code == 200
        assert started.json()["status"] == "running"
        assert started.json()["target"] == "server"
        assert status.json()["status"] == "succeeded"
        assert status.json()["log"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_admin_config_is_persisted_and_filtered_for_public_clients(tmp_path: Path) -> None:
    store = CodexWatchConfigStore(tmp_path, build_default_config(get_settings()))
    app.dependency_overrides[get_codex_watch_store] = lambda: store
    try:
        session = client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "come2u"},
        )
        token = session.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "crawler": {
                "account": "@thsottiaux",
                "keywords": ["Codex", "reset", "codex"],
                "scheduleEnabled": True,
                "intervalMinutes": 15,
                "maxPosts": 12,
            },
            "tutorials": [
                {
                    "id": "tutorial-1",
                    "title": "Codex 快速上手",
                    "description": "从第一次任务开始",
                    "url": "https://example.com/codex",
                }
            ],
            "community": {
                "title": "AI 技术交流群",
                "description": "交流 AI 实战",
                "qrCode": "",
            },
            "updatedAt": None,
        }

        saved = client.put("/api/v1/admin/codex-watch/config", json=payload, headers=headers)
        assert saved.status_code == 200
        assert saved.json()["crawler"]["account"] == "thsottiaux"
        assert saved.json()["crawler"]["keywords"] == ["codex", "reset"]
        assert saved.json()["updatedAt"] is not None

        reloaded = client.get("/api/v1/admin/codex-watch/config", headers=headers)
        assert reloaded.json()["crawler"]["intervalMinutes"] == 15
        assert (tmp_path / "config.json").exists()

        public_config = client.get("/api/v1/codex-watch/config")
        assert public_config.status_code == 200
        assert len(public_config.json()["tutorials"]) == 1
        assert public_config.json()["community"] is None

        payload["community"]["qrCode"] = "data:image/png;base64,Y29kZXg="
        client.put("/api/v1/admin/codex-watch/config", json=payload, headers=headers)
        public_config = client.get("/api/v1/codex-watch/config")
        assert public_config.json()["community"]["title"] == "AI 技术交流群"
    finally:
        app.dependency_overrides.clear()


def test_admin_config_enforces_reference_crawler_limits(tmp_path: Path) -> None:
    store = CodexWatchConfigStore(tmp_path, build_default_config(get_settings()))
    app.dependency_overrides[get_codex_watch_store] = lambda: store
    try:
        session = client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "come2u"},
        )
        headers = {"Authorization": f"Bearer {session.json()['accessToken']}"}
        config = client.get("/api/v1/admin/codex-watch/config", headers=headers).json()
        config["crawler"]["intervalMinutes"] = 4

        response = client.put("/api/v1/admin/codex-watch/config", json=config, headers=headers)

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
