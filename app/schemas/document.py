from pydantic import BaseModel, Field, field_validator
from app.models.enums import DocumentStatus


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