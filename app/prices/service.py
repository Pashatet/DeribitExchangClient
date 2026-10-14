import asyncio
import logging
import time
from collections.abc import Callable
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.deribit_client import DeribitClient
from app.prices.dao import PriceDAO
from app.prices.models import PriceRecord


class PriceService:
    TICKERS = ("btc_usd", "eth_usd")

    def __init__(
        self,
        dao: PriceDAO | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        client_factory: Callable[[], DeribitClient] | None = None,
    ) -> None:
        self._dao = dao if dao is not None else PriceDAO()
        self._session_factory = session_factory
        self._client_factory = client_factory if client_factory is not None else DeribitClient

    async def get_prices(self, session: AsyncSession, ticker: str) -> list[PriceRecord]:
        return await self._dao.get_prices_by_ticker(session, ticker)

    async def get_latest_price(
        self,
        session: AsyncSession,
        ticker: str,
    ) -> PriceRecord | None:
        return await self._dao.get_latest_price_by_ticker(session, ticker)

    async def get_prices_by_date(
        self,
        session: AsyncSession,
        ticker: str,
        requested_date: date,
    ) -> list[PriceRecord]:
        start = datetime.combine(requested_date, datetime_time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        return await self._dao.get_prices_in_period(
            session,
            ticker,
            int(start.timestamp()),
            int(end.timestamp()),
        )

    async def collect_index_prices(self) -> list[dict[str, str | int]]:
        if self._session_factory is None:
            raise RuntimeError("A database session factory is required to collect prices")

        async with self._client_factory() as client:
            prices: list[tuple[str, Decimal]] = list(
                zip(
                    self.TICKERS,
                    await asyncio.gather(
                        *(client.get_index_price(ticker) for ticker in self.TICKERS)
                    ),
                    strict=True,
                )
            )

        captured_at = int(time.time())
        async with self._session_factory.begin() as session:
            await self._dao.add_price_records(session, prices, captured_at)

        logging.getLogger(__name__).info(
            "Saved Deribit index prices for %s",
            ", ".join(self.TICKERS),
        )
        return [
            {"ticker": ticker, "price": str(price), "timestamp": captured_at}
            for ticker, price in prices
        ]
