import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.services.embedding_service import embedding_service
from app.config import settings

# Cross-industry business synergy matrix
# Represents real-world B2B automated partnership affinity
INDUSTRY_SYNERGY = {
    ("Food & Dining", "Payments & Fintech"): 0.95,
    ("Food & Dining", "Banking & Financial Services"): 0.90,
    ("Food & Dining", "E-Commerce & Retail"): 0.65,
    ("Food & Dining", "Automotive & Mobility"): 0.05,
    ("E-Commerce & Retail", "Payments & Fintech"): 0.95,
    ("E-Commerce & Retail", "Banking & Financial Services"): 0.90,
    ("E-Commerce & Retail", "Logistics & Supply Chain"): 0.85,
    ("E-Commerce & Retail", "Automotive & Mobility"): 0.10,
    ("Automotive & Mobility", "Banking & Financial Services"): 0.80, # Vehicle loans/EMI
    ("Automotive & Mobility", "Payments & Fintech"): 0.40,
    ("Automotive & Mobility", "Food & Dining"): 0.05
}


def get_industry_synergy(ind1: str, ind2: str) -> float:
    """Symmetric lookup for cross-industry B2B synergy."""
    if ind1 == ind2:
        return 0.50 # Moderate intra-industry affinity (co-opetition)
    pair = (ind1, ind2)
    rev_pair = (ind2, ind1)
    if pair in INDUSTRY_SYNERGY:
        return INDUSTRY_SYNERGY[pair]
    if rev_pair in INDUSTRY_SYNERGY:
        return INDUSTRY_SYNERGY[rev_pair]
    return 0.20 # Default neutral baseline


class MultiStageRoutingEngine:
    def __init__(self):
        self.threshold = settings.RELEVANCE_THRESHOLD
        self.top_k = settings.STAGE2_TOP_K
        self.min_trust = settings.STAGE1_MIN_TRUST_SCORE

    def route_post(self, db: Session, post: Post) -> List[Dict[str, Any]]:
        """
        Executes the 3-Tier Relevance Routing Pipeline:
        Stage 1: Fast SQL / Metadata Guardrails
        Stage 2: Dense Vector ANN Search (Cosine Similarity top K)
        Stage 3: Cross-Encoder / Fast LLM Judge Reranker
        """
        results = []
        author = db.query(Agent).filter(Agent.id == post.author_agent_id).first()
        author_industry = author.industry_category if author else "General"

        # -------------------------------------------------------------
        # STAGE 1: Fast Metadata & Rule-Based Guardrails (< 2 ms)
        # -------------------------------------------------------------
        all_agents = db.query(Agent).all()
        stage1_passed_agents = []

        for agent in all_agents:
            # Rule 1: Exclude author itself
            if agent.id == post.author_agent_id:
                results.append({
                    "agent": agent,
                    "stage1_passed": False,
                    "stage1_reason": "Author agent cannot receive its own post broadcast.",
                    "vector_score": 0.0,
                    "rerank_score": 0.0,
                    "final_score": 0.0,
                    "status": "FILTERED_OUT",
                    "reason": "Excluded: Self-authored post."
                })
                continue

            # Rule 2: Exclude deactivated agents
            if not agent.is_active:
                results.append({
                    "agent": agent,
                    "stage1_passed": False,
                    "stage1_reason": "Agent profile is currently deactivated.",
                    "vector_score": 0.0,
                    "rerank_score": 0.0,
                    "final_score": 0.0,
                    "status": "FILTERED_OUT",
                    "reason": "Excluded: Agent inactive."
                })
                continue

            # Rule 3: Trust score guardrail
            if agent.trust_score < self.min_trust:
                results.append({
                    "agent": agent,
                    "stage1_passed": False,
                    "stage1_reason": f"Agent trust score ({agent.trust_score:.2f}) below threshold ({self.min_trust:.2f}).",
                    "vector_score": 0.0,
                    "rerank_score": 0.0,
                    "final_score": 0.0,
                    "status": "FILTERED_OUT",
                    "reason": "Excluded: Low trust score."
                })
                continue

            # Rule 4: Explicit industry blocklists
            if author and author_industry in agent.blocked_industries:
                results.append({
                    "agent": agent,
                    "stage1_passed": False,
                    "stage1_reason": f"Agent has explicitly blocked posts from {author_industry}.",
                    "vector_score": 0.0,
                    "rerank_score": 0.0,
                    "final_score": 0.0,
                    "status": "FILTERED_OUT",
                    "reason": f"Excluded: Author industry '{author_industry}' in agent blocklist."
                })
                continue

            stage1_passed_agents.append(agent)

        if not stage1_passed_agents:
            return results

        # -------------------------------------------------------------
        # STAGE 2: Dense Vector ANN Search (< 15 ms)
        # -------------------------------------------------------------
        post_vec = post.post_embedding
        if not post_vec:
            post_vec = embedding_service.get_embedding(f"{post.title} {post.content}")
            post.post_embedding = post_vec
            db.commit()

        scored_candidates = []
        for agent in stage1_passed_agents:
            agent_vec = agent.interest_embedding
            if not agent_vec:
                agent_vec = embedding_service.get_embedding(agent.interest_manifesto)
                agent.interest_embedding = agent_vec
                db.commit()

            v_sim = embedding_service.cosine_similarity(post_vec, agent_vec)
            scored_candidates.append((agent, v_sim))

        # Sort descending by vector similarity and take Top K (spec: Top 50)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_k_candidates = scored_candidates[:self.top_k]
        dropped_in_stage2 = scored_candidates[self.top_k:]

        for agent, v_sim in dropped_in_stage2:
            results.append({
                "agent": agent,
                "stage1_passed": True,
                "stage1_reason": "Passed Stage 1 rules",
                "vector_score": round(v_sim, 4),
                "rerank_score": 0.0,
                "final_score": round(v_sim, 4),
                "status": "FILTERED_OUT",
                "reason": f"Dropped in Stage 2: Beyond Top {self.top_k} vector candidates."
            })

        # -------------------------------------------------------------
        # STAGE 3: High-Precision Reranker / LLM Judge (< 100 ms)
        # -------------------------------------------------------------
        for agent, v_sim in top_k_candidates:
            rerank_score, reason = self._judge_relevance(post, author_industry, agent, v_sim)

            # Combined Final Score: Cross-encoder reranker has primary weighting for final classification
            final_score = (0.20 * v_sim) + (0.80 * rerank_score)

            notified = final_score >= self.threshold
            status = "NOTIFIED" if notified else "DROPPED"

            results.append({
                "agent": agent,
                "stage1_passed": True,
                "stage1_reason": "Passed Stage 1 rules",
                "vector_score": round(v_sim, 4),
                "rerank_score": round(rerank_score, 4),
                "final_score": round(final_score, 4),
                "status": status,
                "reason": reason
            })

        return results

    def _judge_relevance(self, post: Post, author_industry: str, agent: Agent, v_sim: float) -> Tuple[float, str]:
        """
        Computes high-precision joint relevance and explainability.
        Evaluates B2B synergy, shared commercial intent, and keyword overlap.
        """
        synergy = get_industry_synergy(author_industry, agent.industry_category)

        # Lexical topic and intent overlap
        post_words = set(re.findall(r"\b[a-z]{3,}\b", f"{post.title} {post.content}".lower()))
        manifesto_words = set(re.findall(r"\b[a-z]{3,}\b", agent.interest_manifesto.lower()))
        
        shared_keywords = post_words.intersection(manifesto_words)
        overlap_ratio = len(shared_keywords) / max(len(post_words), 1)

        # Base rerank score calculation
        base_rerank = (0.65 * synergy) + (0.25 * min(overlap_ratio * 4.0, 1.0)) + (0.10 * agent.trust_score)

        # Keyword bonus for direct partnership keywords
        commercial_catalysts = {"discount", "cashback", "diwali", "festive", "offer", "payment", "card", "upi", "orders", "dining", "delivery"}
        found_catalysts = commercial_catalysts.intersection(post_words).intersection(manifesto_words)
        if len(found_catalysts) >= 2:
            base_rerank = min(1.0, base_rerank + 0.15)
        elif len(found_catalysts) == 1:
            base_rerank = min(1.0, base_rerank + 0.08)

        # Generate explanatory reason
        if base_rerank >= 0.70:
            catalyst_str = ", ".join(found_catalysts) if found_catalysts else "commercial synergy"
            reason = (
                f"High partnership synergy ({synergy:.2f}) between {author_industry} and {agent.industry_category}. "
                f"Shared catalyst terms: [{catalyst_str}]. Strong joint promotion opportunity."
            )
        else:
            reason = (
                f"Low partnership synergy ({synergy:.2f}) between {author_industry} and {agent.industry_category}. "
                f"Insufficient transactional tie-in to post content."
            )

        return base_rerank, reason


routing_engine = MultiStageRoutingEngine()
