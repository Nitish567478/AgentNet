from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.agent import Agent
from app.schemas.agent import AgentRegisterRequest, AgentUpdateRequest, AgentResponse
from app.services.embedding_service import embedding_service

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


@router.post("/register", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def register_agent(payload: AgentRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new autonomous enterprise agent.
    Computes initial dense interest embedding from the agent's interest manifesto.
    """
    # Check if company already registered
    existing = db.query(Agent).filter(Agent.company_name == payload.company_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent for company '{payload.company_name}' already exists (ID: {existing.id})"
        )

    # Compute dense embedding
    embedding = embedding_service.get_embedding(payload.interest_manifesto)

    agent = Agent(
        company_name=payload.company_name,
        industry_category=payload.industry_category,
        webhook_url=payload.webhook_url,
        interest_manifesto=payload.interest_manifesto,
        blocked_industries=payload.blocked_industries or []
    )
    agent.interest_embedding = embedding

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


@router.get("", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    """Lists all registered enterprise agents and their health/trust scores."""
    agents = db.query(Agent).order_by(Agent.company_name.asc()).all()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Retrieves single agent metadata and performance metrics."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, payload: AgentUpdateRequest, db: Session = Depends(get_db)):
    """Updates agent interest manifesto, webhook URL, or active status."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if payload.company_name:
        agent.company_name = payload.company_name
    if payload.industry_category:
        agent.industry_category = payload.industry_category
    if payload.webhook_url:
        agent.webhook_url = payload.webhook_url
    if payload.blocked_industries is not None:
        agent.blocked_industries = payload.blocked_industries
    if payload.is_active is not None:
        agent.is_active = payload.is_active
    if payload.interest_manifesto:
        agent.interest_manifesto = payload.interest_manifesto
        agent.interest_embedding = embedding_service.get_embedding(payload.interest_manifesto)

    db.commit()
    db.refresh(agent)
    return agent

