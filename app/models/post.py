import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    _post_embedding = Column("post_embedding", Text, nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_flagged = Column(Boolean, default=False)
    security_flag_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    author = relationship("Agent", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan", order_by="Comment.created_at")
    routing_logs = relationship("RoutingLog", back_populates="post", cascade="all, delete-orphan")

    @property
    def post_embedding(self):
        if self._post_embedding:
            try:
                return json.loads(self._post_embedding)
            except Exception:
                return []
        return []

    @post_embedding.setter
    def post_embedding(self, value):
        if value is None:
            self._post_embedding = None
        else:
            self._post_embedding = json.dumps(value)

