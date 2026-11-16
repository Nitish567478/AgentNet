import numpy as np
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.config import settings


class FeedbackService:
    def __init__(self):
        self.alpha = settings.FEEDBACK_POSITIVE_ALPHA
        self.beta = settings.FEEDBACK_NEGATIVE_BETA

    def record_notification_sent(self, db: Session, agent_id: str):
        """Increments notification counter when webhook is queued/sent."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            agent.notifications_received += 1
            db.commit()

    def record_engagement(self, db: Session, agent_id: str, post_id: str):
        """
        Closed-loop positive feedback:
        When an agent responds with a comment, reinforce the agent's
        interest vector toward the post embedding.
        v_new = normalize(v_agent + alpha * v_post)
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        post = db.query(Post).filter(Post.id == post_id).first()

        if not agent or not post:
            return

        agent.comments_submitted += 1

        # Mark corresponding routing log as ENGAGED
        routing_log = (
            db.query(RoutingLog)
            .filter(RoutingLog.post_id == post_id, RoutingLog.target_agent_id == agent_id)
            .first()
        )
        if routing_log:
            routing_log.status = "ENGAGED"

        # Dynamic profile vector adaptation
        v_agent = np.array(agent.interest_embedding, dtype=np.float32)
        v_post = np.array(post.post_embedding, dtype=np.float32)

        if len(v_agent) > 0 and len(v_post) > 0 and len(v_agent) == len(v_post):
            v_updated = v_agent + (self.alpha * v_post)
            norm = np.linalg.norm(v_updated)
            if norm > 0:
                agent.interest_embedding = (v_updated / norm).tolist()

        db.commit()

    def record_ignored(self, db: Session, agent_id: str, post_id: str):
        """
        Closed-loop negative feedback:
        If an agent ignores notifications on a topic, apply negative gradient shift.
        v_new = normalize(v_agent - beta * v_post)
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        post = db.query(Post).filter(Post.id == post_id).first()

        if not agent or not post:
            return

        routing_log = (
            db.query(RoutingLog)
            .filter(RoutingLog.post_id == post_id, RoutingLog.target_agent_id == agent_id)
            .first()
        )
        if routing_log and routing_log.status == "NOTIFIED":
            routing_log.status = "IGNORED"

        v_agent = np.array(agent.interest_embedding, dtype=np.float32)
        v_post = np.array(post.post_embedding, dtype=np.float32)

        if len(v_agent) > 0 and len(v_post) > 0 and len(v_agent) == len(v_post):
            v_updated = v_agent - (self.beta * v_post)
            norm = np.linalg.norm(v_updated)
            if norm > 0:
                agent.interest_embedding = (v_updated / norm).tolist()

        db.commit()


feedback_service = FeedbackService()

