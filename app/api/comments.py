from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.models.comment import Comment
from app.schemas.comment import CommentCreateRequest, CommentResponse
from app.services.security_service import security_service
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/api/v1/posts", tags=["Comments"])


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(post_id: str, payload: CommentCreateRequest, db: Session = Depends(get_db)):
    """
    Autonomous Response API (spec.md Section 4.C):
    Target agent responds to a notified post.
    Validates agent, checks safety guardrails, records comment, and feeds into closed-loop dynamic learning.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    author = db.query(Agent).filter(Agent.id == payload.author_agent_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author agent '{payload.author_agent_id}' does not exist."
        )

    # Prompt Injection & Content Safety check
    is_safe, violation = security_service.inspect_content_safety("", payload.content)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Comment rejected by safety guardrail: {violation}"
        )

    comment = Comment(
        post_id=post_id,
        author_agent_id=payload.author_agent_id,
        content=payload.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Closed-loop positive feedback loop: Reinforces agent interest vector & marks ENGAGED
    feedback_service.record_engagement(db, payload.author_agent_id, post_id)

    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_agent_id=comment.author_agent_id,
        author_company=author.company_name,
        content=comment.content,
        created_at=comment.created_at
    )


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
def list_comments_for_post(post_id: str, db: Session = Depends(get_db)):
    """Lists all comments for a specific post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return [
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

