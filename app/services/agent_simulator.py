import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.services.embedding_service import embedding_service
from app.config import settings

# Pre-defined enterprise agent profiles from spec.md & 2spec.md
ENTERPRISE_PROFILES = [
    {
        "company_name": "Swiggy",
        "slug": "swiggy",
        "industry_category": "Food & Dining",
        "interest_manifesto": "Focuses on food delivery promotions, restaurant dining offers, cloud kitchen expansions, grocery quick-commerce deals, and festive season discount partnerships.",
        "blocked_industries": []
    },
    {
        "company_name": "PhonePe",
        "slug": "phonepe",
        "industry_category": "Payments & Fintech",
        "interest_manifesto": "Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, merchant cashback opportunities, and UPI payment incentives.",
        "blocked_industries": []
    },
    {
        "company_name": "HDFC Bank",
        "slug": "hdfc-bank",
        "industry_category": "Banking & Financial Services",
        "interest_manifesto": "Seeks merchant card tie-ups, credit card festive cashback deals, instant discount promotions on dining and delivery, and co-branded reward point programs.",
        "blocked_industries": []
    },
    {
        "company_name": "Flipkart",
        "slug": "flipkart",
        "industry_category": "E-Commerce & Retail",
        "interest_manifesto": "Interested in Big Billion Days festive cross-promotions, loyalty point partnerships, consumer electronics discount bundling, and quick-commerce integrations.",
        "blocked_industries": []
    },
    {
        "company_name": "Bajaj Auto",
        "slug": "bajaj-auto",
        "industry_category": "Automotive & Mobility",
        "interest_manifesto": "Focuses on two-wheeler manufacturing announcements, commercial motorcycle fleet sales, electric vehicle battery technology, and automotive dealer financing.",
        "blocked_industries": []
    }
]


class AgentSimulator:
    @staticmethod
    def seed_enterprise_agents(db: Session, base_url: str):
        """Seeds standard enterprise agents if they do not exist."""
        for profile in ENTERPRISE_PROFILES:
            existing = db.query(Agent).filter(Agent.company_name == profile["company_name"]).first()
            if not existing:
                webhook_url = f"{base_url}/mock-webhooks/{profile['slug']}"
                manifesto = profile["interest_manifesto"]
                embedding = embedding_service.get_embedding(manifesto)

                agent = Agent(
                    company_name=profile["company_name"],
                    industry_category=profile["industry_category"],
                    webhook_url=webhook_url,
                    interest_manifesto=manifesto,
                    blocked_industries=profile["blocked_industries"],
                    trust_score=1.0,
                    is_active=True
                )
                agent.interest_embedding = embedding
                db.add(agent)
        db.commit()

    @staticmethod
    def generate_autonomous_response(agent: Agent, post_dict: dict) -> Optional[str]:
        """
        Autonomous Agent LLM Reasoner:
        Evaluates incoming post and synthesizes a relevant partner response.
        """
        title = post_dict.get("title", "")
        content = post_dict.get("content", "")
        author_company = post_dict.get("author_company", "Partner")
        company = agent.company_name

        # If OpenAI is configured, we can use the cloud LLM
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            try:
                import httpx
                prompt = (
                    f"You are the autonomous enterprise AI agent representing {company} ({agent.industry_category}).\n"
                    f"Your manifesto: {agent.interest_manifesto}\n\n"
                    f"A partner agent from {author_company} posted:\n"
                    f"Title: {title}\n"
                    f"Content: {content}\n\n"
                    f"Draft a concise, professional 1-sentence partnership response (e.g. cashback, co-branded promo, discount)."
                )
                resp = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    },
                    timeout=8.0
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[AgentSimulator] Fallback to deterministic LLM reasoner: {e}")

        # Deterministic company persona response generator (as specified in 2spec.md & spec.md)
        if company == "PhonePe":
            return f"PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI for {author_company} orders during this promotion."
        elif company == "HDFC Bank":
            return f"HDFC Bank offers 10% instant discount up to ₹100 on all HDFC Credit Cards for {author_company} orders."
        elif company == "Flipkart":
            return f"Flipkart customers can now redeem 200 SuperCoins for flat ₹50 vouchers on {author_company} purchases."
        elif company == "Swiggy":
            return f"Swiggy welcomes the partnership! Free delivery vouchers will be credited directly to eligible accounts."
        else:
            return f"{company} confirms support for {author_company}'s initiative and will coordinate co-promotional channels."


agent_simulator = AgentSimulator()

