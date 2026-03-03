from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    in_review = "in_review"
    completed = "completed"


class UserResponse(BaseModel):
    user_id: str
    user_email: str
    display_name: str | None = None
    created_at: datetime


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    project_description: str = Field(..., min_length=1, max_length=5000)


class DocumentUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    project_description: str | None = Field(None, min_length=1, max_length=5000)
    status: DocumentStatus | None = None


class DocumentResponse(BaseModel):
    document_id: str
    user_id: str
    title: str
    project_description: str
    status: str
    created_at: datetime
