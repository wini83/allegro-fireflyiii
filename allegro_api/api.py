"""Allegro REST API helper module."""

import logging
from typing import Any

import requests

from allegro_api.const import ALLEGRO_API_URL
from allegro_api.get_order_result import GetOrdersResult
from allegro_api.get_user_info import GetUserInfoResult

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)


class AllegroApiClient:
    """Simplified Allegro API client."""

    def __init__(self, cookie: str, session: requests.Session) -> None:
        """Create client bound to existing :class:`requests.Session`."""
        self._cookie = cookie
        self._api_wrapper = ApiWrapper(session)

    def get_standard_header(self, api_ver: int = 1) -> dict[str, str]:
        """Return standard request header."""
        return {
            "Cookie": f"QXLSESSID={self._cookie}",
            "Accept": f"application/vnd.allegro.public.v{api_ver}+json",
            "Referer": "https://allegro.pl/",
        }

    def get_orders(self) -> GetOrdersResult:
        """Get orders from API."""
        headers = self.get_standard_header(3)
        get_orders_response = self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/myorder-api/myorders?limit=25",
            headers=headers,
        )
        return GetOrdersResult(get_orders_response)

    def get_user_info(self) -> GetUserInfoResult:
        """Get info about current user."""
        headers = self.get_standard_header(2)
        get_orders_response = self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/users",
            headers=headers,
        )
        return GetUserInfoResult(get_orders_response)


class ApiWrapper:
    """HTTP request helper."""

    def __init__(self, session: requests.Session) -> None:
        self._session = session

    def get(
        self, url: str, headers: dict[str, str] | None = None, auth: Any | None = None
    ) -> Any:
        """Run HTTP GET request."""
        return self.request("GET", url, headers=headers, auth=auth)

    def post(
        self,
        url: str,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
        auth: Any | None = None,
    ) -> Any:
        """Run HTTP POST request."""
        return self.request("POST", url, data=data, headers=headers, auth=auth)

    def request(
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
            response = self._session.request(
                method,
                url,
                headers=headers,
                data=data,
                auth=auth,
                timeout=TIMEOUT,
                **request_kwargs,
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout as exc:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exc,
            )
            raise
