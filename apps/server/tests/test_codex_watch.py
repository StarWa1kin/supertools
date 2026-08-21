from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_codex_watch_returns_configured_account() -> None:
    response = client.get("/api/v1/codex-watch/posts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["monitoredAccount"] == "tibo"
    assert isinstance(payload["items"], list)
    assert payload["sourceUrl"] == "https://codex-reset.com/"
