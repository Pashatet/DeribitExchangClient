from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


DATABASE_PARAMS = {"poolclass": NullPool} if settings.MODE == "TEST" else {}
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    **DATABASE_PARAMS,
)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
