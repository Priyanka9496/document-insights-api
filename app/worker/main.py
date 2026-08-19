import asyncio
import random

from app.config import get_settings
from app.database import create_mongo_client
from app.redis_client import create_redis_client
from app.repositories.document_repository import DocumentRepository
from app.services.rate_limiter import ActiveJobLimiter


settings = get_settings()


def build_mock_summary(content):
    words = content.split()

    return {
        "overview": content[:200],
        "word_count": len(words),
        "key_points": [
            "Mock insight generated from document content"
        ]
    }


async def process_document(document, repository, rate_limiter):
    user_id = document["user_id"]
    document_id = document["_id"]

    try:
        processing_time = random.randint(
            settings.processing_min_seconds,
            settings.processing_max_seconds
        )

        await asyncio.sleep(processing_time)

        if random.random() < settings.processing_failure_rate:
            raise RuntimeError("Simulated processing failure")

        summary = build_mock_summary(document["content"])

        await repository.mark_completed(
            document_id,
            summary
        )

    except Exception:
        await repository.mark_failed(
            document_id,
            "Document processing failed"
        )

    finally:
        await rate_limiter.release(user_id)

async def run_worker():
    mongo_client = create_mongo_client(settings.mongodb_url)
    database = mongo_client[settings.mongodb_database]

    redis_client = create_redis_client(settings.redis_url)

    repository = DocumentRepository(
        database["documents"]
    )

    rate_limiter = ActiveJobLimiter(
        redis_client,
        settings.max_active_jobs_per_user,
        settings.active_job_ttl_seconds
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
                rate_limiter
            )

    finally:
        await redis_client.aclose()
        await mongo_client.close()


if __name__ == "__main__":
    asyncio.run(run_worker())