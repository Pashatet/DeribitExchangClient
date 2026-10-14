import json
from decimal import Decimal, InvalidOperation
from typing import Any

import aiohttp

from app.config import settings


class DeribitAPIError(RuntimeError):
    """Raised when Deribit returns an invalid response or an API error."""


class DeribitClient:
    SUPPORTED_INDEXES = frozenset({"btc_usd", "eth_usd"})

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        configured_base_url = base_url or settings.DERIBIT_BASE_URL
        self._base_url = f"{configured_base_url.rstrip('/')}/"
        self._timeout_seconds = (
            settings.DERIBIT_TIMEOUT if timeout_seconds is None else timeout_seconds
        )
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "DeribitClient":
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout_seconds),
            )
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def get_index_price(self, index_name: str) -> Decimal:
        if index_name not in self.SUPPORTED_INDEXES:
            raise ValueError(f"Unsupported index: {index_name}")

        if self._session is None or self._session.closed:
            raise RuntimeError("Use DeribitClient inside an async context manager")

        async with self._session.get(
            f"{self._base_url}public/get_index_price",
            params={"index_name": index_name},
        ) as response:
            response.raise_for_status()
            try:
                payload: Any = await response.json()
            except (aiohttp.ContentTypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise DeribitAPIError("Deribit returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise DeribitAPIError("Deribit returned an invalid response")

        error = payload.get("error")
        if error:
            message = (
                error.get("message", "unknown API error")
                if isinstance(error, dict)
                else str(error)
            )
            raise DeribitAPIError(f"Deribit API error: {message}")

        result = payload.get("result")
        if not isinstance(result, dict) or "index_price" not in result:
            raise DeribitAPIError("Deribit response does not contain result.index_price")

        try:
            price = Decimal(str(result["index_price"]))
        except (InvalidOperation, ValueError) as exc:
            raise DeribitAPIError("Deribit returned a non-numeric index price") from exc

        if not price.is_finite() or price <= 0:
            raise DeribitAPIError("Deribit returned an invalid index price")

        return price
