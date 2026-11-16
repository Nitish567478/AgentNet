import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.services.feedback_service import feedback_service
from app.services.embedding_service import embedding_service


def test_positive_and_negative_feedback_adaptation():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    agent = Agent(
        company_name="TestFintech",
        industry_category="Payments & Fintech",
        webhook_url="http://test/webhook",
        interest_manifesto="Digital payments and card discounts"
    )
    initial_vec = embedding_service.get_embedding(agent.interest_manifesto)
    agent.interest_embedding = initial_vec
    session.add(agent)
    session.flush()

    post = Post(
        author_agent_id=agent.id,
        title="Food Delivery Offer",
        content="Discounts on weekend dinners"
    )
    post_vec = embedding_service.get_embedding(f"{post.title} {post.content}")
    post.post_embedding = post_vec
    session.add(post)
    session.commit()

    log = RoutingLog(
        post_id=post.id,
        target_agent_id=agent.id,
        vector_score=0.5,
        rerank_score=0.8,
        final_score=0.78,
        status="NOTIFIED"
    )
    session.add(log)
    session.commit()

    # Record engagement (positive feedback)
    initial_v_array = np.array(agent.interest_embedding)
    feedback_service.record_engagement(session, agent.id, post.id)

    updated_v_array = np.array(agent.interest_embedding)

    # Verify vector updated and normalized
    assert not np.allclose(initial_v_array, updated_v_array)
    assert np.isclose(np.linalg.norm(updated_v_array), 1.0, atol=1e-4)

    # Verify routing log status changed to ENGAGED
    updated_log = session.query(RoutingLog).filter(RoutingLog.id == log.id).first()
    assert updated_log.status == "ENGAGED"

    # Record ignored (negative feedback)
    post2 = Post(
        author_agent_id=agent.id,
        title="Automotive Parts",
        content="Heavy machinery engine repair"
    )
    post2.post_embedding = embedding_service.get_embedding(f"{post2.title} {post2.content}")
    session.add(post2)
    session.commit()

    log2 = RoutingLog(
        post_id=post2.id,
        target_agent_id=agent.id,
        status="NOTIFIED"
    )
    session.add(log2)
    session.commit()

    feedback_service.record_ignored(session, agent.id, post2.id)
    assert log2.status == "IGNORED"

    session.close()
