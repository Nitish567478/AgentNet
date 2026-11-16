from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.models.comment import Comment
from app.models.routing_log import RoutingLog
from app.schemas.routing import RoutingLogResponse

router = APIRouter(prefix="/api/v1", tags=["Routing & Analytics"])


@router.get("/routing-logs", response_model=List[RoutingLogResponse])
def list_routing_logs(
    post_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """Retrieves multi-stage routing audit logs, scores, and delivery statuses."""
    query = db.query(RoutingLog)
    if post_id:
        query = query.filter(RoutingLog.post_id == post_id)
    if status:
        query = query.filter(RoutingLog.status == status)

    logs = query.order_by(RoutingLog.created_at.desc()).limit(limit).all()

    return [
        RoutingLogResponse(
            id=log.id,
            post_id=log.post_id,
            target_agent_id=log.target_agent_id,
            target_company_name=log.target_agent.company_name if log.target_agent else "Unknown",
            vector_score=log.vector_score,
            rerank_score=log.rerank_score,
            final_score=log.final_score,
            status=log.status,
            routing_reason=log.routing_reason,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.get("/analytics")
def get_platform_analytics(db: Session = Depends(get_db)):
    """Computes real-time platform metrics, routing efficiency, and engagement stats."""
    total_agents = db.query(Agent).count()
    total_posts = db.query(Post).count()
    total_comments = db.query(Comment).count()
    total_logs = db.query(RoutingLog).count()

    notified_count = db.query(RoutingLog).filter(RoutingLog.status.in_(["NOTIFIED", "ENGAGED"])).count()
    engaged_count = db.query(RoutingLog).filter(RoutingLog.status == "ENGAGED").count()
    filtered_stage1 = db.query(RoutingLog).filter(RoutingLog.stage1_passed == False).count()
    dropped_stage3 = db.query(RoutingLog).filter(RoutingLog.status == "DROPPED").count()

    engagement_rate = round(engaged_count / notified_count, 4) if notified_count > 0 else 0.0

    agents = db.query(Agent).all()
    agent_stats = [
        {
            "id": a.id,
            "company_name": a.company_name,
            "industry": a.industry_category,
            "trust_score": a.trust_score,
            "notifications_received": a.notifications_received,
            "comments_submitted": a.comments_submitted,
            "engagement_rate": a.engagement_rate
        }
        for a in agents
    ]

    return {
        "overview": {
            "total_agents": total_agents,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_routing_evaluations": total_logs,
            "notifications_dispatched": notified_count,
            "successful_engagements": engaged_count,
            "overall_engagement_rate": engagement_rate
        },
        "funnel_metrics": {
            "stage1_filtered_out": filtered_stage1,
            "stage3_dropped_below_threshold": dropped_stage3,
            "stage3_notified_and_queued": notified_count
        },
        "agents": agent_stats
    }

