from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class RoutingDecision(BaseModel):
    agent_id: str
    company_name: str
    industry: str
    stage1_passed: bool
    stage1_reason: Optional[str] = None
    vector_score: float
    rerank_score: float
    final_score: float
    notified: bool
    status: str
    reason: str


class RoutingReport(BaseModel):
    post_id: str
    post_title: str
    author_company: str
    total_registered_agents: int
    stage1_eligible_count: int
    stage2_top_k_count: int
    stage3_notified_count: int
    decisions: List[RoutingDecision]


class RoutingLogResponse(BaseModel):
    id: str
    post_id: str
    target_agent_id: str
    target_company_name: Optional[str] = None
    vector_score: float
    rerank_score: float
    final_score: float
    status: str
    routing_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
