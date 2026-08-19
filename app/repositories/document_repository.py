from datetime import UTC, datetime

from app.models.enums import DocumentStatus
from app.schemas.document import DocumentCreate


class DocumentRepository:

    def __init__(self, collection):
        self.collection = collection

    async def create_queued(self, payload, content_hash):

        now = datetime.now(UTC)

        document = {
            "user_id": payload.user_id,
            "title": payload.title,
            "content": payload.content,
            "content_hash": content_hash,
            "status": DocumentStatus.QUEUED.value,
            "summary": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "processing_started_at": None,
            "completed_at": None
        }

        result = await self.collection.insert_one(document)

        document["_id"] = result.inserted_id

        return document