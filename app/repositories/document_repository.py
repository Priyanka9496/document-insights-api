from datetime import UTC, datetime
from app.models.enums import DocumentStatus
from app.schemas.document import DocumentCreate
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING


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

    async def get_by_id(self, document_id):
        try:
            object_id = ObjectId(document_id)
        except InvalidId:
            return None

        return await self.collection.find_one(
            {"_id": object_id}
        )

    async def list_by_user(self, user_id, page, page_size, status=None):
        query = {"user_id": user_id}

        if status is not None:
            query["status"] = status.value

        skip = (page - 1) * page_size

        cursor = (
            self.collection
            .find(query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(page_size)
        )

        documents = await cursor.to_list(length=page_size)

        total = await self.collection.count_documents(query)

        return documents, total