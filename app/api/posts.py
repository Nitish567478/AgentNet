import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.models.comment import Comment
from app.models.routing_log import RoutingLog
from app.schemas.post import PostCreateRequest, PostResponse, RoutingCandidateSummary
from app.schemas.comment import CommentResponse
from app.services.embedding_service import embedding_service
from app.services.routing_engine import routing_engine
from app.services.security_service import security_service
from app.services.webhook_dispatcher import webhook_dispatcher
from app.services.agent_simulator import agent_simulator
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/api/v1/posts", tags=["Posts"])


def _format_post_response(post: Post) -> PostResponse:
    """Helper to transform ORM Post into full Pydantic response."""
    comments_dto = [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            author_agent_id=c.author_agent_id,
            author_company=c.author.company_name if c.author else "Unknown",
            content=c.content,
            created_at=c.created_at
        )
        for c in post.comments
    ]

    routing_summaries = [
        RoutingCandidateSummary(
            target_agent_id=r.target_agent_id,
            target_company_name=r.target_agent.company_name if r.target_agent else "Unknown",
            vector_score=r.vector_score,
            rerank_score=r.rerank_score,
            final_score=r.final_score,
            status=r.status,
            routing_reason=r.routing_reason
        )
        for r in post.routing_logs
    ]

    return PostResponse(
        id=post.id,
        author_agent_id=post.author_agent_id,
        author_company=post.author.company_name if post.author else "Unknown",
        title=post.title,
        content=post.content,
        is_flagged=post.is_flagged,
        security_flag_reason=post.security_flag_reason,
        created_at=post.created_at,
        comments=comments_dto,
        routing_summary=routing_summaries
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Publishes a new business announcement or promotion.
    1. Validates author exists
    2. Runs security & prompt injection inspection
    3. Computes dense semantic embedding
    4. Executes 3-Tier Relevance Routing Engine (SQL Guardrail -> ANN Vector -> Reranker Judge)
    5. Dispatches HMAC-signed webhooks to qualified target agents
    """
    author = db.query(Agent).filter(Agent.id == payload.author_agent_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author agent '{payload.author_agent_id}' does not exist."
        )

    # 1. Prompt Injection & Content Safety Sanitizer (spec.md Section 6.B)
    is_safe, violation_reason = security_service.inspect_content_safety(payload.title, payload.content)

    # 2. Compute Dense Embedding
    embedding = embedding_service.get_embedding(f"{payload.title} {payload.content}")

    post = Post(
        author_agent_id=payload.author_agent_id,
        title=payload.title,
        content=payload.content,
        expires_at=payload.expires_at,
        is_flagged=not is_safe,
        security_flag_reason=violation_reason
    )
    post.post_embedding = embedding

    db.add(post)
    db.commit()
    db.refresh(post)

    # If post violates safety rules, halt routing to protect receiving agents
    if not is_safe:
        return _format_post_response(post)

    # 3. Multi-Stage Semantic Relevance Routing (spec.md Section 3)
    routing_results = routing_engine.route_post(db, post)

    # 4. Record logs and dispatch webhooks
    for result in routing_results:
        target_agent = result["agent"]
        log_entry = RoutingLog(
            post_id=post.id,
            target_agent_id=target_agent.id,
            stage1_passed=result["stage1_passed"],
            stage1_reason=result.get("stage1_reason"),
            vector_score=result["vector_score"],
            rerank_score=result["rerank_score"],
            final_score=result["final_score"],
            status=result["status"],
            routing_reason=result["reason"]
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # For notified agents, generate autonomous partnership replies and queue webhooks
        if result["status"] == "NOTIFIED":
            # 1. Synthesize autonomous agent partnership response
            try:
                response_text = agent_simulator.generate_autonomous_response(
                    target_agent,
                    {"title": post.title, "content": post.content, "author_company": author.company_name}
                )
                if response_text:
                    comment = Comment(
                        post_id=post.id,
                        author_agent_id=target_agent.id,
                        content=response_text
                    )
                    db.add(comment)
                    db.commit()
                    feedback_service.record_engagement(db, target_agent.id, post.id)
            except Exception as e:
                print(f"[create_post] Auto-response generation note: {e}")

            # 2. Asynchronously dispatch signed HMAC webhook
            webhook_payload = {
                "event": "post.published",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "post": {
                    "id": post.id,
                    "author_agent_id": post.author_agent_id,
                    "author_company": author.company_name,
                    "title": post.title,
                    "content": post.content
                },
                "routing_metadata": {
                    "vector_score": result["vector_score"],
                    "rerank_score": result["rerank_score"],
                    "final_score": result["final_score"],
                    "routing_reason": result["reason"]
                }
            }

            # Queue webhook delivery job asynchronously
            background_tasks.add_task(
                webhook_dispatcher.dispatch_webhook,
                post.id,
                target_agent.id,
                target_agent.webhook_url,
                target_agent.webhook_secret,
                webhook_payload,
                log_entry.id
            )

    db.refresh(post)
    return _format_post_response(post)


@router.get("", response_model=List[PostResponse])
def list_posts(db: Session = Depends(get_db)):
    """Retrieves all posts with nested comments and routing logs."""
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return [_format_post_response(p) for p in posts]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)):
    """Retrieves a single post and its complete routing inspection details."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _format_post_response(post)
