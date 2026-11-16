import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RoutingLog(Base):
    __tablename__ = "routing_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    target_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    stage1_passed = Column(Boolean, default=True)
    stage1_reason = Column(String(255), nullable=True)

    vector_score = Column(Float, default=0.0)      # Stage 2 Cosine Similarity [0, 1]
    rerank_score = Column(Float, default=0.0)      # Stage 3 LLM / Reranker Score [0, 1]
    final_score = Column(Float, default=0.0)       # Combined Final Score

    # Status: NOTIFIED, ENGAGED, IGNORED, FAILED, FILTERED_OUT, SECURITY_BLOCKED
    status = Column(String(50), default="NOTIFIED", index=True)

    routing_reason = Column(Text, nullable=True)
    webhook_status_code = Column(Integer, nullable=True)
    webhook_response_body = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    post = relationship("Post", back_populates="routing_logs")
    target_agent = relationship("Agent", back_populates="routing_logs")

