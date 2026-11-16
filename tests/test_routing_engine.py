import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.agent import Agent
from app.models.post import Post
from app.services.embedding_service import embedding_service
from app.services.routing_engine import routing_engine


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test agents matching 2spec.md and spec.md
    swiggy = Agent(
        company_name="Swiggy",
        industry_category="Food & Dining",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/swiggy",
        interest_manifesto="Food delivery festive discounts and restaurant promotions."
    )
    swiggy.interest_embedding = embedding_service.get_embedding(swiggy.interest_manifesto)

    phonepe = Agent(
        company_name="PhonePe",
        industry_category="Payments & Fintech",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/phonepe",
        interest_manifesto="Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, and merchant cashback opportunities."
    )
    phonepe.interest_embedding = embedding_service.get_embedding(phonepe.interest_manifesto)

    hdfc = Agent(
        company_name="HDFC Bank",
        industry_category="Banking & Financial Services",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/hdfc-bank",
        interest_manifesto="Card payment tie-ups, credit card festive cashback deals, instant discount promotions on dining."
    )
    hdfc.interest_embedding = embedding_service.get_embedding(hdfc.interest_manifesto)

    bajaj = Agent(
        company_name="Bajaj Auto",
        industry_category="Automotive & Mobility",
        webhook_url="http://127.0.0.1:8000/mock-webhooks/bajaj-auto",
        interest_manifesto="Two-wheeler manufacturing, motorcycle fleet sales, EV battery technology."
    )
    bajaj.interest_embedding = embedding_service.get_embedding(bajaj.interest_manifesto)

    session.add_all([swiggy, phonepe, hdfc, bajaj])
    session.commit()

    yield session
    session.close()


def test_diwali_routing_benchmark(test_db):
    """
    Validates spec.md & 2spec.md Benchmark:
    Swiggy posts: '5% off all deliveries on Diwali.'
    Platform notifies PhonePe and HDFC Bank (S_final >= 0.75).
    Platform does NOT notify Bajaj Auto.
    """
    swiggy = test_db.query(Agent).filter(Agent.company_name == "Swiggy").first()

    post = Post(
        author_agent_id=swiggy.id,
        title="Diwali Food Delivery Discount",
        content="Swiggy offering flat 5% off on all delivery orders above 300 during Diwali week."
    )
    post.post_embedding = embedding_service.get_embedding(f"{post.title} {post.content}")
    test_db.add(post)
    test_db.commit()

    results = routing_engine.route_post(test_db, post)

    notified = [r["agent"].company_name for r in results if r["status"] == "NOTIFIED"]
    dropped = [r["agent"].company_name for r in results if r["status"] == "DROPPED"]
    filtered = [r["agent"].company_name for r in results if r["status"] == "FILTERED_OUT"]

    assert "Swiggy" in filtered, "Author must be filtered out in Stage 1"
    assert "PhonePe" in notified, "PhonePe must be notified"
    assert "HDFC Bank" in notified, "HDFC Bank must be notified"
    assert "Bajaj Auto" in dropped, "Bajaj Auto must be dropped (not notified)"


def test_stage1_inactive_agent_filter(test_db):
    """Verifies that deactivated agents are filtered out in Stage 1."""
    phonepe = test_db.query(Agent).filter(Agent.company_name == "PhonePe").first()
    phonepe.is_active = False
    test_db.commit()

    swiggy = test_db.query(Agent).filter(Agent.company_name == "Swiggy").first()
    post = Post(
        author_agent_id=swiggy.id,
        title="Diwali Discount",
        content="Food delivery discount"
    )
    post.post_embedding = embedding_service.get_embedding(f"{post.title} {post.content}")
    test_db.add(post)
    test_db.commit()

    results = routing_engine.route_post(test_db, post)
    phonepe_result = next(r for r in results if r["agent"].company_name == "PhonePe")

    assert phonepe_result["stage1_passed"] is False
    assert phonepe_result["status"] == "FILTERED_OUT"

