from datetime import date as Date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.prices.models import PriceRecord
from app.prices.schemas import PriceRead
from app.prices.service import PriceService


router = APIRouter(prefix="/prices", tags=["prices"])
Ticker = Literal["btc_usd", "eth_usd"]


async def get_price_service() -> PriceService:
    return PriceService()


@router.get("", response_model=list[PriceRead], summary="Get all saved prices for a ticker")
async def get_prices(
    ticker: Ticker = Query(..., description="Index ticker: btc_usd or eth_usd"),
    db: AsyncSession = Depends(get_db),
    price_service: PriceService = Depends(get_price_service),
) -> list[PriceRecord]:
    return await price_service.get_prices(db, ticker)


@router.get("/latest", response_model=PriceRead, summary="Get the latest saved price for a ticker")
async def get_latest_price(
    ticker: Ticker = Query(..., description="Index ticker: btc_usd or eth_usd"),
    db: AsyncSession = Depends(get_db),
    price_service: PriceService = Depends(get_price_service),
) -> PriceRecord:
    record = await price_service.get_latest_price(db, ticker)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No price records found for {ticker}")
    return record


@router.get("/by-date", response_model=list[PriceRead], summary="Get a ticker's prices for a UTC date")
async def get_prices_by_date(
    ticker: Ticker = Query(..., description="Index ticker: btc_usd or eth_usd"),
    date: Date = Query(..., description="UTC calendar date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
    price_service: PriceService = Depends(get_price_service),
) -> list[PriceRecord]:
    return await price_service.get_prices_by_date(db, ticker, date)
