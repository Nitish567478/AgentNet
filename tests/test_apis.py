import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import BackgroundTasks
from app.database import Base
from app.models.agent import Agent
from app.schemas.agent import AgentRegisterRequest
from app.schemas.post import PostCreateRequest
from app.schemas.comment import CommentCreateRequest
from app.api.agents import register_agent, list_agents
from app.api.posts import create_post, list_posts
from app.api.comments import create_comment


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


def test_agent_registration_and_listing(db_session):
    # Register an agent
    reg_req = AgentRegisterRequest(
        company_name="TestCorp",
        industry_category="Payments & Fintech",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/testcorp",
        interest_manifesto="Fintech payment processing, card integrations and merchant cashback."
    )
    agent = register_agent(reg_req, db_session)
    assert agent.company_name == "TestCorp"
    assert agent.webhook_secret is not None
    assert agent.trust_score == 1.0

    # List agents
    all_agents = list_agents(db_session)
    assert any(a.company_name == "TestCorp" for a in all_agents)


def test_post_creation_and_autonomous_comment(db_session):
    # Register author
    author = register_agent(AgentRegisterRequest(
        company_name="SwiggyTest",
        industry_category="Food & Dining",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/swiggy",
        interest_manifesto="Food delivery and discounts."
    ), db_session)

    # Register partner
    partner = register_agent(AgentRegisterRequest(
        company_name="PhonePeTest",
        industry_category="Payments & Fintech",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/phonepe",
        interest_manifesto="Cashback on food delivery and festival discount promotions."
    ), db_session)

    # Create post with empty BackgroundTasks (unit test isolation)
    bg = BackgroundTasks()
    post_req = PostCreateRequest(
        author_agent_id=author.id,
        title="Diwali Food Offer",
        content="Special 5% discount on food orders during festival."
    )
    post_resp = create_post(post_req, bg, db_session)
    assert post_resp.title == "Diwali Food Offer"
    assert post_resp.author_company == "SwiggyTest"

    # Add comment (autonomous response)
    comment_req = CommentCreateRequest(
        author_agent_id=partner.id,
        content="PhonePe will provide extra 50 cashback for these orders."
    )
    comment_resp = create_comment(post_resp.id, comment_req, db_session)
    assert comment_resp.author_company == "PhonePeTest"
    assert "cashback" in comment_resp.content
