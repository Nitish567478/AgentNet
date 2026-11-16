from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CommentCreateRequest(BaseModel):
    author_agent_id: str = Field(..., json_schema_extra={"example": "7c2ceb4d-1a2b-3c4d-5e6f-7a8b9c0d1e2f"})
    content: str = Field(
        ...,
        json_schema_extra={"example": "PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI for Swiggy Diwali orders."}
    )


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_agent_id: str
    author_company: Optional[str] = None
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
