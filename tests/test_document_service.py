from unittest.mock import AsyncMock, Mock

import pytest
from bson import ObjectId

from app.schemas.document import DocumentCreate, Summary
from app.services.document_service import (
    DocumentService,
    RateLimitExceeded
)


@pytest.mark.asyncio
async def test_cache_hit_skips_rate_limiter():
    repository = Mock()
    repository.create_completed = AsyncMock(
        return_value={
            "_id": ObjectId(),
            "status": "completed",
            "summary": {
                "overview": "Cached summary",
                "word_count": 2,
                "key_points": ["Cached"]
            }
        }
    )

    rate_limiter = Mock()
    rate_limiter.acquire = AsyncMock()

    cache = Mock()
    cache.get = AsyncMock(
        return_value=Summary(
            overview="Cached summary",
            word_count=2,
            key_points=["Cached"]
        )
    )

    service = DocumentService(
        repository,
        rate_limiter,
        cache
    )

    payload = DocumentCreate(
        user_id="user-1",
        title="Test",
        content="Same content"
    )

    document, cached = await service.create_document(payload)

    assert cached is True
    assert document["status"] == "completed"

    rate_limiter.acquire.assert_not_awaited()


@pytest.mark.asyncio
async def test_rate_limit_rejects_new_document():
    repository = Mock()

    rate_limiter = Mock()
    rate_limiter.acquire = AsyncMock(return_value=False)

    cache = Mock()
    cache.get = AsyncMock(return_value=None)

    service = DocumentService(
        repository,
        rate_limiter,
        cache
    )

    payload = DocumentCreate(
        user_id="user-1",
        title="Test",
        content="New content"
    )

    with pytest.raises(RateLimitExceeded):
        await service.create_document(payload)