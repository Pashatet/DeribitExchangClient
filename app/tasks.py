import asyncio

import aiohttp
from sqlalchemy.exc import SQLAlchemyError

from app.celery_app import celery_app
from app.database import async_session_maker, engine
from app.deribit_client import DeribitAPIError
from app.prices.service import PriceService


@celery_app.task(
    name="app.tasks.collect_index_prices",
    autoretry_for=(aiohttp.ClientError, TimeoutError, DeribitAPIError, SQLAlchemyError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def collect_index_prices_task() -> list[dict[str, str | int]]:
    # Celery's standard worker calls sync task functions, so bridge into asyncio here.
    async def run_and_dispose() -> list[dict[str, str | int]]:
        try:
            return await PriceService(session_factory=async_session_maker).collect_index_prices()
        finally:
            # The asyncio.run loop closes after this task. Dispose loop-bound pooled
            # connections so a later task can safely use a fresh event loop.
            await engine.dispose()

    return asyncio.run(run_and_dispose())
