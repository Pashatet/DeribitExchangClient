from datetime import date
from decimal import Decimal

import pytest

from app.prices.dao import PriceDAO
from app.prices.models import PriceRecord
from app.prices.service import PriceService


class FakeDatabaseSession:
    def __init__(self) -> None:
        self.records: list[object] = []

    def add_all(self, records: list[object]) -> None:
        self.records.extend(records)

    async def flush(self) -> None:
        return None


class FakeTransaction:
    def __init__(self, session: FakeDatabaseSession) -> None:
        self.session = session

    async def __aenter__(self) -> FakeDatabaseSession:
        return self.session

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSessionFactory:
    def __init__(self, session: FakeDatabaseSession) -> None:
        self.session = session

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self.session)


class FakeDeribitClient:
    def __init__(self) -> None:
        self.requested_tickers: list[str] = []

    async def __aenter__(self) -> "FakeDeribitClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get_index_price(self, ticker: str) -> Decimal:
        self.requested_tickers.append(ticker)
        return {
            "btc_usd": Decimal("65000.25"),
            "eth_usd": Decimal("3200.75"),
        }[ticker]


class PeriodCapturingDAO:
    def __init__(self) -> None:
        self.period: tuple[str, int, int] | None = None

    async def get_prices_in_period(
        self,
        session,
        ticker: str,
        start_timestamp: int,
        end_timestamp: int,
    ) -> list[object]:
        self.period = (ticker, start_timestamp, end_timestamp)
        return []


@pytest.mark.asyncio
async def test_collect_index_prices_fetches_and_saves_both_tickers() -> None:
    session = FakeDatabaseSession()
    client = FakeDeribitClient()
    service = PriceService(
        dao=PriceDAO(),
        session_factory=FakeSessionFactory(session),  # type: ignore[arg-type]
        client_factory=lambda: client,  # type: ignore[arg-type]
    )

    result = await service.collect_index_prices()

    assert client.requested_tickers == ["btc_usd", "eth_usd"]
    assert all(isinstance(record, PriceRecord) for record in session.records)
    assert [record.ticker for record in session.records] == ["btc_usd", "eth_usd"]
    assert [record.price for record in session.records] == [
        Decimal("65000.25"),
        Decimal("3200.75"),
    ]
    assert all(record.timestamp == result[0]["timestamp"] for record in session.records)
    assert result[0]["price"] == "65000.25"
    assert result[1]["price"] == "3200.75"


@pytest.mark.asyncio
async def test_get_prices_by_date_uses_utc_day_bounds() -> None:
    dao = PeriodCapturingDAO()
    service = PriceService(dao=dao)  # type: ignore[arg-type]

    result = await service.get_prices_by_date(object(), "btc_usd", date(1970, 1, 1))  # type: ignore[arg-type]

    assert result == []
    assert dao.period == ("btc_usd", 0, 86_400)
