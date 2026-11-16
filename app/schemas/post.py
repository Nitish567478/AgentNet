from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.comment import CommentResponse


class PostCreateRequest(BaseModel):
    author_agent_id: str = Field(..., json_schema_extra={"example": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"})
    title: str = Field(..., json_schema_extra={"example": "Diwali Food Delivery Discount"})
    content: str = Field(
        ...,
        json_schema_extra={"example": "Swiggy offering flat 5% off on all delivery orders above ₹300 during Diwali week."}
    )
    expires_at: Optional[datetime] = None


class RoutingCandidateSummary(BaseModel):
    target_agent_id: str
    target_company_name: str
    vector_score: float
    rerank_score: float
    final_score: float
    status: str
    routing_reason: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    author_agent_id: str
    author_company: Optional[str] = None
    title: str
    content: str
    is_flagged: bool = False
    security_flag_reason: Optional[str] = None
    created_at: datetime
    comments: List[CommentResponse] = Field(default_factory=list)
    routing_summary: Optional[List[RoutingCandidateSummary]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
