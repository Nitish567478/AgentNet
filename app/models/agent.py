import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False, index=True)
    industry_category = Column(String(100), nullable=False, index=True)
    webhook_url = Column(Text, nullable=False)
    webhook_secret = Column(String(255), nullable=False, default=lambda: uuid.uuid4().hex)
    interest_manifesto = Column(Text, nullable=False)
    
    # Store embedding as JSON serialized float array for database portability (SQLite / Postgres)
    _interest_embedding = Column("interest_embedding", Text, nullable=True)

    trust_score = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    _blocked_industries = Column("blocked_industries", Text, default="[]")

    # Feedback metrics
    notifications_received = Column(Integer, default=0)
    comments_submitted = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    routing_logs = relationship("RoutingLog", back_populates="target_agent", cascade="all, delete-orphan")

    @property
    def interest_embedding(self):
        if self._interest_embedding:
            try:
                return json.loads(self._interest_embedding)
            except Exception:
                return []
        return []

    @interest_embedding.setter
    def interest_embedding(self, value):
        if value is None:
            self._interest_embedding = None
        else:
            self._interest_embedding = json.dumps(value)

    @property
    def blocked_industries(self):
        if self._blocked_industries:
            try:
                return json.loads(self._blocked_industries)
            except Exception:
                return []
        return []

    @blocked_industries.setter
    def blocked_industries(self, value):
        if value is None:
            self._blocked_industries = "[]"
        else:
            self._blocked_industries = json.dumps(value)

    @property
    def engagement_rate(self) -> float:
        if self.notifications_received == 0:
            return 0.0
        return round(self.comments_submitted / self.notifications_received, 4)

