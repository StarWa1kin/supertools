from typing import Annotated

import httpx
from fastapi import Depends, HTTPException

from app.core.config import Settings, get_settings


class DeploymentService:
    def __init__(self, settings: Settings) -> None:
        self._url = settings.deploy_service_url.rstrip("/")
        self._token = settings.deploy_service_token

    async def _request(self, method: str, path: str) -> dict[str, object]:
        if not self._url or not self._token:
            raise HTTPException(status_code=503, detail="一键部署服务尚未配置")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.request(
                    method,
                    f"{self._url}{path}",
                    headers={"Authorization": f"Bearer {self._token}"},
                )
        except httpx.HTTPError as error:
            raise HTTPException(status_code=502, detail="无法连接部署服务") from error
        detail = self._error_detail(response)
        if response.status_code == 401:
            raise HTTPException(
                status_code=502, detail="部署服务鉴权失败，请检查 DEPLOY_SERVICE_TOKEN"
            )
        if response.status_code == 409:
            raise HTTPException(status_code=409, detail=detail or "已有部署任务正在执行")
        if response.is_error:
            raise HTTPException(
                status_code=502,
                detail=f"部署服务返回异常：{detail}" if detail else "部署服务返回异常",
            )
        try:
            payload = response.json()
        except ValueError as error:
            raise HTTPException(status_code=502, detail="部署服务返回了无效响应") from error
        if not isinstance(payload, dict):
            raise HTTPException(status_code=502, detail="部署服务返回了无效响应")
        return payload

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip()[:300]
        if isinstance(payload, dict) and isinstance(payload.get("detail"), str):
            return payload["detail"][:300]
        return ""

    async def status(self) -> dict[str, object]:
        if not self._url or not self._token:
            return {
                "status": "unavailable",
                "startedAt": None,
                "finishedAt": None,
                "log": "部署服务未配置，请检查 DEPLOY_SERVICE_URL 和 DEPLOY_SERVICE_TOKEN。",
            }
        return await self._request("GET", "/status")

    async def start(self, target: str) -> dict[str, object]:
        if target not in {"server", "admin"}:
            raise ValueError(f"Unsupported deployment target: {target}")
        return await self._request("POST", f"/deploy/{target}")


def get_deployment_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DeploymentService:
    return DeploymentService(settings)
