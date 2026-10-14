from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceRecord(Base):
    __tablename__ = "price_records"
    __table_args__ = (
        CheckConstraint("ticker IN ('btc_usd', 'eth_usd')", name="ck_price_records_ticker"),
        Index("ix_price_records_ticker_timestamp", "ticker", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
