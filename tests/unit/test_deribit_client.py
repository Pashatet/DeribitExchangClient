from decimal import Decimal
from unittest.mock import patch

import aiohttp
import pytest

from app.deribit_client import DeribitAPIError, DeribitClient


class FakeResponse:
    def __init__(self, payload: object, status_error: Exception | None = None) -> None:
        self.payload = payload
        self.status_error = status_error

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_error is not None:
            raise self.status_error

    async def json(self) -> object:
        return self.payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.closed = False
        self.request: tuple[str, dict[str, str]] | None = None

    def get(self, path: str, *, params: dict[str, str]) -> FakeResponse:
        self.request = (path, params)
        return self.response

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_get_index_price_returns_decimal_and_calls_public_endpoint() -> None:
    session = FakeSession(FakeResponse({"result": {"index_price": 67234.125}}))

    with patch("app.deribit_client.aiohttp.ClientSession", return_value=session):
        async with DeribitClient("https://deribit.example/api/v2", timeout_seconds=3) as client:
            price = await client.get_index_price("btc_usd")

    assert price == Decimal("67234.125")
    assert session.request == (
        "https://deribit.example/api/v2/public/get_index_price",
        {"index_name": "btc_usd"},
    )
    assert session.closed


@pytest.mark.asyncio
async def test_get_index_price_rejects_unsupported_index() -> None:
    client = DeribitClient("https://deribit.example/api/v2")

    with pytest.raises(ValueError, match="Unsupported index"):
        await client.get_index_price("btc_usdc")


@pytest.mark.asyncio
async def test_get_index_price_raises_for_deribit_api_error() -> None:
    session = FakeSession(FakeResponse({"error": {"message": "Index not found"}}))

    with patch("app.deribit_client.aiohttp.ClientSession", return_value=session):
        async with DeribitClient("https://deribit.example/api/v2") as client:
            with pytest.raises(DeribitAPIError, match="Index not found"):
                await client.get_index_price("eth_usd")


@pytest.mark.asyncio
async def test_get_index_price_rejects_invalid_price() -> None:
    session = FakeSession(FakeResponse({"result": {"index_price": 0}}))

    with patch("app.deribit_client.aiohttp.ClientSession", return_value=session):
        async with DeribitClient("https://deribit.example/api/v2") as client:
            with pytest.raises(DeribitAPIError, match="invalid index price"):
                await client.get_index_price("eth_usd")


@pytest.mark.asyncio
async def test_get_index_price_propagates_http_errors() -> None:
    http_error = aiohttp.ClientConnectionError("Service unavailable")
    session = FakeSession(FakeResponse({}, status_error=http_error))

    with patch("app.deribit_client.aiohttp.ClientSession", return_value=session):
        async with DeribitClient("https://deribit.example/api/v2") as client:
            with pytest.raises(aiohttp.ClientConnectionError):
                await client.get_index_price("btc_usd")
