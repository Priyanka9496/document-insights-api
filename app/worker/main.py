import asyncio
import json
import logging
import random

from app.config import get_settings
from app.database import create_mongo_client
from app.redis_client import create_redis_client
from app.repositories.document_repository import DocumentRepository
from app.services.rate_limiter import ActiveJobLimiter
from app.services.cache_service import SummaryCache
from app.services.inflight_lock import InFlightDocumentLock


settings = get_settings()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

logger = logging.getLogger(__name__)


def build_mock_summary(content):
    words = content.split()

    return {
        "overview": content[:200],
        "word_count": len(words),
        "key_points": [
            "Mock insight generated from document content"
        ]
    }


async def process_document(
    document,
    repository,
    rate_limiter,
    cache,
    inflight_lock
):
    user_id = document["user_id"]
    document_id = document["_id"]
    content_hash = document["content_hash"]

    try:
        processing_time = random.randint(
            settings.processing_min_seconds,
            settings.processing_max_seconds
        )

        logger.info(
            json.dumps({
                "event": "document_processing_started",
                "document_id": str(document_id),
                "user_id": user_id
            })
        )

        await asyncio.sleep(processing_time)

        if random.random() < settings.processing_failure_rate:
            raise RuntimeError(
                "Simulated processing failure"
            )

        summary = build_mock_summary(
            document["content"]
        )

        await repository.mark_completed(
            document_id,
            summary
        )

        await cache.set(
            content_hash,
            summary
        )

        logger.info(
            json.dumps({
                "event": "document_processing_completed",
                "document_id": str(document_id),
                "user_id": user_id,
                "processing_time_seconds": processing_time
            })
        )

    except Exception as error:
        logger.exception(
            json.dumps({
                "event": "document_processing_failed",
                "document_id": str(document_id),
                "user_id": user_id,
                "error": str(error)
            })
        )

        await repository.mark_failed(
            document_id,
            "Document processing failed"
        )

    finally:
        try:
            await rate_limiter.release(
                user_id
            )
        except Exception:
            logger.warning(
                "Failed to release active-job slot",
                exc_info=True
            )

        await inflight_lock.release(
            content_hash
        )


async def run_worker():
    mongo_client = create_mongo_client(
        settings.mongodb_url
    )

    database = mongo_client[
        settings.mongodb_database
    ]

    redis_client = create_redis_client(
        settings.redis_url
    )

    cache = SummaryCache(
        redis_client,
        settings.summary_cache_ttl_seconds
    )

    inflight_lock = InFlightDocumentLock(
        redis_client,
        settings.inflight_lock_ttl_seconds
    )

    repository = DocumentRepository(
        database["documents"]
    )

    rate_limiter = ActiveJobLimiter(
        redis_client,
        settings.max_active_jobs_per_user,
        settings.active_job_ttl_seconds
    )

    logger.info(
        json.dumps({
            "event": "worker_started"
        })
    )

    try:
        while True:
            document = await repository.claim_next_queued()

            if document is None:
                await asyncio.sleep(1)
                continue

            await process_document(
                document,
                repository,
                rate_limiter,
                cache,
                inflight_lock
            )

    finally:
        await redis_client.aclose()
        await mongo_client.close()


if __name__ == "__main__":
    asyncio.run(run_worker())