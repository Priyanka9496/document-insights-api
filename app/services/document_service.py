import hashlib


class DocumentService:

    def __init__(self, repository):
        self.repository = repository

    async def create_document(self, payload):
        content_hash = hashlib.sha256(
            payload.content.encode("utf-8")
        ).hexdigest()

        return await self.repository.create_queued(
            payload,
            content_hash
        )

    async def get_document(self, document_id):
        return await self.repository.get_by_id(document_id)

    async def list_user_documents(
            self,
            user_id,
            page,
            page_size,
            status=None
    ):
        return await self.repository.list_by_user(
            user_id,
            page,
            page_size,
            status
        )