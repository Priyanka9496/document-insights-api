from fastapi import APIRouter, Depends, Query, Request

from app.models.enums import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import PaginatedDocuments
from app.services.document_service import DocumentService


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


def get_document_service(request: Request):
    collection = request.app.state.database["documents"]
    repository = DocumentRepository(collection)

    return DocumentService(repository)


@router.get(
    "/{user_id}/documents",
    response_model=PaginatedDocuments
)
async def list_user_documents(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: DocumentStatus = None,
    service: DocumentService = Depends(get_document_service)
):
    documents, total = await service.list_user_documents(
        user_id,
        page,
        page_size,
        status
    )

    items = []

    for document in documents:
        items.append(
            {
                "document_id": str(document["_id"]),
                "title": document["title"],
                "status": document["status"],
                "created_at": document["created_at"]
            }
        )

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total
    }