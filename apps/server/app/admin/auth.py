import base64
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.admin.schemas import AdminLoginRequest, AdminSession
from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_admin_session(credentials: AdminLoginRequest, settings: Settings) -> AdminSession:
    username_matches = hmac.compare_digest(credentials.username, settings.admin_username)
    password_matches = hmac.compare_digest(credentials.password, settings.admin_password)
    if not username_matches or not password_matches:
        raise HTTPException(status_code=401, detail="账号或密码错误")

    expires_at = int(time.time()) + settings.admin_token_ttl_seconds
    payload = _encode(json.dumps({"sub": settings.admin_username, "exp": expires_at}).encode())
    signature = _encode(
        hmac.new(settings.admin_token_secret.encode(), payload.encode(), hashlib.sha256).digest()
    )
    return AdminSession(
        access_token=f"{payload}.{signature}",
        expires_in=settings.admin_token_ttl_seconds,
        username=settings.admin_username,
    )


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="请先登录")

    try:
        payload, signature = credentials.credentials.split(".", 1)
        expected = _encode(
            hmac.new(
                settings.admin_token_secret.encode(), payload.encode(), hashlib.sha256
            ).digest()
        )
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        claims = json.loads(_decode(payload))
        if claims.get("sub") != settings.admin_username or int(claims.get("exp", 0)) < time.time():
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录") from None
    return settings.admin_username
