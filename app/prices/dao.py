from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.prices.models import PriceRecord


class PriceDAO:
    async def add_price_records(
        self,
        session: AsyncSession,
        prices: Sequence[tuple[str, Decimal]],
        timestamp: int,
    ) -> list[PriceRecord]:
        records = [
            PriceRecord(ticker=ticker, price=price, timestamp=timestamp)
            for ticker, price in prices
        ]
        session.add_all(records)
        await session.flush()
        return records

    async def get_prices_by_ticker(
        self,
        session: AsyncSession,
        ticker: str,
    ) -> list[PriceRecord]:
        statement = (
            select(PriceRecord)
            .where(PriceRecord.ticker == ticker)
            .order_by(PriceRecord.timestamp.asc(), PriceRecord.id.asc())
        )
        result = await session.scalars(statement)
        return list(result.all())

    async def get_latest_price_by_ticker(
        self,
        session: AsyncSession,
        ticker: str,
    ) -> PriceRecord | None:
        statement = (
            select(PriceRecord)
            .where(PriceRecord.ticker == ticker)
            .order_by(PriceRecord.timestamp.desc(), PriceRecord.id.desc())
            .limit(1)
        )
        return await session.scalar(statement)

    async def get_prices_in_period(
        self,
        session: AsyncSession,
        ticker: str,
        start_timestamp: int,
        end_timestamp: int,
    ) -> list[PriceRecord]:
        statement = (
            select(PriceRecord)
            .where(
                PriceRecord.ticker == ticker,
                PriceRecord.timestamp >= start_timestamp,
                PriceRecord.timestamp < end_timestamp,
            )
            .order_by(PriceRecord.timestamp.asc(), PriceRecord.id.asc())
        )
        result = await session.scalars(statement)
        return list(result.all())
