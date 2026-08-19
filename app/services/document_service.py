import hashlib

class RateLimitExceeded(Exception):
    pass


class DocumentService:

    def __init__(self, repository, rate_limiter, cache):
        self.repository = repository
        self.rate_limiter = rate_limiter
        self.cache = cache

    async def create_document(self, payload):
        content_hash = hashlib.sha256(
            payload.content.encode("utf-8")
        ).hexdigest()

        cached_summary = await self.cache.get(
            payload.user_id,
            content_hash
        )

        if cached_summary is not None:
            document = await self.repository.create_completed(
                payload,
                content_hash,
                cached_summary.model_dump()
            )

            return document, True

        acquired = await self.rate_limiter.acquire(payload.user_id)

        if not acquired:
            raise RateLimitExceeded()

        try:
            document = await self.repository.create_queued(
                payload,
                content_hash
            )

            return document, False

        except Exception:
            await self.rate_limiter.release(payload.user_id)
            raise

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