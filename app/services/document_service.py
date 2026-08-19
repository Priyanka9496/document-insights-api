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