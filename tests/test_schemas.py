import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentCreate


def test_document_rejects_blank_title():
    with pytest.raises(ValidationError):
        DocumentCreate(
            user_id="user-1",
            title="   ",
            content="Valid content"
        )


def test_document_accepts_valid_input():
    document = DocumentCreate(
        user_id="user-1",
        title="Test Document",
        content="Valid content"
    )

    assert document.user_id == "user-1"
    assert document.title == "Test Document"
    assert document.content == "Valid content"