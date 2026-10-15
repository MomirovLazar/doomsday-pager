from pydantic import BaseModel, Field, field_validator
from constants import IncidentType, IncidentPriority
class LoginRequest(BaseModel):
    username: str
    password: str

class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200, strict=True)
    description: str = Field(min_length=1, strict=True)

    @field_validator("title", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    type: IncidentType
    priority: IncidentPriority

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000, strict=True)

    @field_validator("content")
    @classmethod

    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Comment cannot be empty")

        return value
