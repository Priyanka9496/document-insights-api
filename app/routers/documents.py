from fastapi import APIRouter, Depends, Request, status

from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentCreateResponse
from app.services.document_service import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)


def get_document_service(request: Request):
    collection = request.app.state.database["documents"]

    repository = DocumentRepository(collection)

    return DocumentService(repository)


@router.post(
    "",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service)
):
    document = await service.create_document(payload)

    return {
        "document_id": str(document["_id"]),
        "status": document["status"]
    }