import hashlib


class RateLimitExceeded(Exception):
    pass


class DuplicateDocumentInProgress(Exception):
    pass


class DocumentService:

    def __init__(
        self,
        repository,
        rate_limiter,
        cache,
        inflight_lock
    ):
        self.repository = repository
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.inflight_lock = inflight_lock

    async def create_document(self, payload):
        content_hash = hashlib.sha256(
            payload.content.encode("utf-8")
        ).hexdigest()

        # 1. Check global summary cache.
        cached_summary = await self.cache.get(
            content_hash
        )

        if cached_summary is not None:
            document = await self.repository.create_completed(
                payload,
                content_hash,
                cached_summary.model_dump()
            )

            return document, True

        # 2. Prevent same content from being processed concurrently.
        lock_acquired = await self.inflight_lock.acquire(
            content_hash
        )

        if not lock_acquired:
            raise DuplicateDocumentInProgress()

        # 3. Apply per-user active-job limit.
        acquired = await self.rate_limiter.acquire(
            payload.user_id
        )

        if not acquired:
            await self.inflight_lock.release(
                content_hash
            )
            raise RateLimitExceeded()

        try:
            # 4. Store document as queued.
            document = await self.repository.create_queued(
                payload,
                content_hash
            )

            return document, False

        except Exception:
            # Roll back Redis state if Mongo insert fails.
            await self.rate_limiter.release(
                payload.user_id
            )

            await self.inflight_lock.release(
                content_hash
            )

            raise

    async def get_document(self, document_id):
        return await self.repository.get_by_id(
            document_id
        )

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