from fastapi import APIRouter, Depends, status, HTTPException

from app.dependencies import get_document_service
from app.schemas.document import (
    DocumentCreate,
    DocumentCreateResponse,
    DocumentStatusResponse
)
from app.services.document_service import (
    DocumentService,
    RateLimitExceeded,
    DuplicateDocumentInProgress
)
from app.services.rate_limiter import RateLimiterUnavailable
from app.services.inflight_lock import InFlightLockUnavailable


router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)


@router.post(
    "",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Identical document already processing"},
        429: {"description": "Too many active documents"},
        503: {"description": "Processing service unavailable"}
    }
)
async def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service)
):
    try:
        document, cached = await service.create_document(payload)

    except DuplicateDocumentInProgress:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identical document is already being processed"
        )

    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum active document limit reached"
        )

    except RateLimiterUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service temporarily unavailable"
        )

    except InFlightLockUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document processing lock service is temporarily unavailable"
        )

    return {
        "document_id": str(document["_id"]),
        "status": document["status"],
        "summary": document["summary"],
        "cached": cached
    }


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    responses={
        404: {"description": "Document not found"}
    }
)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    document = await service.get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return {
        "document_id": str(document["_id"]),
        "user_id": document["user_id"],
        "title": document["title"],
        "status": document["status"],
        "summary": document["summary"],
        "error": document["error"],
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
        "processing_started_at": document["processing_started_at"],
        "completed_at": document["completed_at"]
    }
