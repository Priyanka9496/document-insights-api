from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_document_service
from app.main import app


@pytest.fixture
def mock_service():
    service = AsyncMock()

    app.dependency_overrides[get_document_service] = lambda: service

    yield service

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_document_returns_201(mock_service):
    document_id = ObjectId()

    mock_service.create_document.return_value = (
        {
            "_id": document_id,
            "status": "queued",
            "summary": None
        },
        False
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/documents",
            json={
                "user_id": "user-1",
                "title": "Test Document",
                "content": "Valid content"
            }
        )

    assert response.status_code == 201
    assert response.json()["status"] == "queued"
    assert response.json()["cached"] is False


@pytest.mark.asyncio
async def test_get_unknown_document_returns_404(mock_service):
    mock_service.get_document.return_value = None

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.get(
            "/documents/507f1f77bcf86cd799439011"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Document not found"
    }


@pytest.mark.asyncio
async def test_create_document_rejects_invalid_input(mock_service):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/documents",
            json={
                "user_id": "user-1",
                "title": "   ",
                "content": "Valid content"
            }
        )

    assert response.status_code == 422