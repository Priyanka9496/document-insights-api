from datetime import UTC, datetime
from app.models.enums import DocumentStatus
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING, ReturnDocument


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

    async def claim_next_queued(self):
        now = datetime.now(UTC)

        return await self.collection.find_one_and_update(
            {"status": DocumentStatus.QUEUED.value},
            {
                "$set": {
                    "status": DocumentStatus.PROCESSING.value,
                    "processing_started_at": now,
                    "updated_at": now
                }
            },
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER
        )

    async def mark_completed(self, document_id, summary):
        now = datetime.now(UTC)

        await self.collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "status": DocumentStatus.COMPLETED.value,
                    "summary": summary,
                    "error": None,
                    "completed_at": now,
                    "updated_at": now
                }
            }
        )

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

    async def mark_failed(self, document_id, error_message):
        now = datetime.now(UTC)

        await self.collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "status": DocumentStatus.FAILED.value,
                    "error": error_message,
                    "updated_at": now
                }
            }
        )

    async def create_completed(self, payload, content_hash, summary):
        now = datetime.now(UTC)

        document = {
            "user_id": payload.user_id,
            "title": payload.title,
            "content": payload.content,
            "content_hash": content_hash,
            "status": DocumentStatus.COMPLETED.value,
            "summary": summary,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "processing_started_at": None,
            "completed_at": now
        }

        result = await self.collection.insert_one(document)

        document["_id"] = result.inserted_id

        return document