from fastapi import Request

from app.config import get_settings
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.services.rate_limiter import ActiveJobLimiter
from app.services.cache_service import SummaryCache


def get_document_service(request: Request):
    settings = get_settings()

    collection = request.app.state.database["documents"]

    repository = DocumentRepository(collection)

    rate_limiter = ActiveJobLimiter(
        request.app.state.redis,
        settings.max_active_jobs_per_user,
        settings.active_job_ttl_seconds
    )

    cache = SummaryCache(
        request.app.state.redis,
        settings.summary_cache_ttl_seconds
    )

    return DocumentService(
        repository,
        rate_limiter,
        cache
    )
