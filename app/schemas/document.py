from pydantic import BaseModel, Field, field_validator
from app.models.enums import DocumentStatus
from datetime import datetime
from typing import Optional, List


class Summary(BaseModel):
    overview: str
    word_count: int
    key_points: List[str]


class DocumentCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)

    @field_validator("user_id", "title", "content")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class DocumentCreateResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    summary: Optional[Summary] = None
    cached: bool = False


class DocumentStatusResponse(BaseModel):
    document_id: str
    user_id: str
    title: str
    status: DocumentStatus
    summary: Optional[Summary] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DocumentListItem(BaseModel):
    document_id: str
    title: str
    status: DocumentStatus
    created_at: datetime


class PaginatedDocuments(BaseModel):
    items: List[DocumentListItem]
    page: int
    page_size: int
    total: int
