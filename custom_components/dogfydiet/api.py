from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, GUEST_TOKEN

_LOGGER = logging.getLogger(__name__)


class DogfyDietApiError(Exception):
    pass


class DogfyDietAuthError(DogfyDietApiError):
    pass


class DogfyDietApi:
    def __init__(self, session: aiohttp.ClientSession, refresh_token: str) -> None:
        self._session = session
        self._refresh_token = refresh_token
        self._access_token: str | None = None

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    async def _ensure_token(self) -> None:
        if self._access_token:
            return
        await self._refresh_session()

    async def _refresh_session(self) -> None:
        url = f"{API_BASE_URL}/auth/refreshsession"
        headers = {"Authorization": f"Bearer {GUEST_TOKEN}"}
        try:
            async with self._session.post(
                url,
                headers=headers,
                json={"refreshToken": self._refresh_token},
            ) as resp:
                if resp.status == 401:
                    raise DogfyDietAuthError("Refresh token expired or invalid")
                resp.raise_for_status()
                data = await resp.json()
                self._access_token = data["token"]
                if new_rt := data.get("refreshToken"):
                    self._refresh_token = new_rt
        except aiohttp.ClientError as err:
            raise DogfyDietApiError(f"Error refreshing session: {err}") from err

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_token()
        url = f"{API_BASE_URL}{path}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            async with self._session.request(
                method, url, headers=headers, **kwargs
            ) as resp:
                if resp.status == 401:
                    self._access_token = None
                    await self._refresh_session()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.request(
                        method, url, headers=headers, **kwargs
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise DogfyDietApiError(f"API request failed: {err}") from err

    async def get_self(self) -> dict[str, Any]:
        return await self._request("GET", "/self")

    async def get_orders(self) -> dict[str, Any]:
        return await self._request("GET", "/self/orders")

    @staticmethod
    async def validate_refresh_token(
        session: aiohttp.ClientSession, refresh_token: str
    ) -> dict[str, Any]:
        url = f"{API_BASE_URL}/auth/refreshsession"
        headers = {"Authorization": f"Bearer {GUEST_TOKEN}"}
        async with session.post(
            url, headers=headers, json={"refreshToken": refresh_token}
        ) as resp:
            if resp.status == 401:
                raise DogfyDietAuthError("Invalid refresh token")
            resp.raise_for_status()
            return await resp.json()
