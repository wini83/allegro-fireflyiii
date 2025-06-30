"""Allegro REST API helper module."""

import asyncio
import logging
from typing import Any

import aiohttp  # type: ignore[import]
import async_timeout  # type: ignore[import]

from const import ALLEGRO_API_URL
from get_order_result import GetOrdersResult
from get_user_info import GetUserInfoResult

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)


class AllegroApiClient:
    """Simplified Allegro API client."""

    def __init__(self, cookie: str, session: aiohttp.ClientSession) -> None:
        """Sample API Client."""
        self._cookie = cookie
        self._api_wrapper = ApiWrapper(session)

    def get_standard_header(self, api_ver: int = 1) -> dict[str, str]:
        """Return standard request header."""
        return {
            "Cookie": f"QXLSESSID={self._cookie}",
            "Accept": f"application/vnd.allegro.public.v{api_ver}+json",
            "Referer": "https://allegro.pl/",
        }

    async def get_orders(self) -> GetOrdersResult:
        """Get orders from api"""
        headers = self.get_standard_header(3)
        get_orders_response = await self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/myorder-api/myorders?limit=25",
            headers=headers,
        )
        return GetOrdersResult(get_orders_response)

    async def get_user_info(self) -> GetUserInfoResult:
        """Get info about current user"""
        headers = self.get_standard_header(2)
        get_orders_response = await self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/users",
            headers=headers,
        )
        return GetUserInfoResult(get_orders_response)


class ApiWrapper:
    """HTTP request helper."""

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def get(
        self, url: str, headers: dict | None = None, auth: Any | None = None
    ) -> Any:
        """Run HTTP GET request."""
        return await self.request("GET", url, headers=headers, auth=auth)

    async def post(
        self,
        url: str,
        data: Any | None = None,
        headers: dict | None = None,
        auth: Any | None = None,
    ) -> Any:
        """Run HTTP POST request."""
        return await self.request("POST", url, data=data, headers=headers, auth=auth)

    async def request(
        self,
        method: str,
        url: str,
        **request_kwargs: Any,
    ) -> Any:
        """Execute HTTP request and return response JSON."""
        headers = request_kwargs.pop("headers", None) or {}
        data = request_kwargs.pop("data", None)
        auth = request_kwargs.pop("auth", None)
        try:
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.request(
                    method,
                    url,
                    headers=headers,
                    data=data,
                    auth=auth,
                    **request_kwargs,
                ) as response:
                    return await response.json()
        except asyncio.TimeoutError as exc:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exc,
            )
            raise
