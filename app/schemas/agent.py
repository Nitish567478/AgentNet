from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class AgentRegisterRequest(BaseModel):
    company_name: str = Field(..., json_schema_extra={"example": "PhonePe"})
    industry_category: str = Field(..., json_schema_extra={"example": "Payments & Fintech"})
    webhook_url: str = Field(..., json_schema_extra={"example": "http://127.0.0.1:8000/mock-webhooks/phonepe"})
    interest_manifesto: str = Field(
        ...,
        json_schema_extra={"example": "Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, and merchant cashback opportunities."}
    )
    blocked_industries: Optional[List[str]] = Field(default_factory=list)


class AgentUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    industry_category: Optional[str] = None
    webhook_url: Optional[str] = None
    interest_manifesto: Optional[str] = None
    blocked_industries: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    id: str
    company_name: str
    industry_category: str
    webhook_url: str
    webhook_secret: str
    interest_manifesto: str
    trust_score: float
    is_active: bool
    notifications_received: int
    comments_submitted: int
    engagement_rate: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
