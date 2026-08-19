from unittest.mock import AsyncMock

import pytest

from app.services.rate_limiter import ActiveJobLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_job_when_below_limit():
    redis_client = AsyncMock()
    redis_client.eval.return_value = 1

    limiter = ActiveJobLimiter(
        redis_client,
        limit=3,
        ttl=900
    )

    result = await limiter.acquire("user-1")

    assert result is True
    redis_client.eval.assert_awaited_once()


@pytest.mark.asyncio
async def test_rate_limiter_rejects_job_when_limit_reached():
    redis_client = AsyncMock()
    redis_client.eval.return_value = 0

    limiter = ActiveJobLimiter(
        redis_client,
        limit=3,
        ttl=900
    )

    result = await limiter.acquire("user-1")

    assert result is False