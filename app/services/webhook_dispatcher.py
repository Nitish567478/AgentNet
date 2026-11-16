import json
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.services.security_service import security_service
from app.services.feedback_service import feedback_service
from app.database import SessionLocal


class WebhookDispatcher:
    @staticmethod
    def dispatch_webhook(
        post_id: str,
        target_agent_id: str,
        webhook_url: str,
        webhook_secret: str,
        payload_dict: dict,
        routing_log_id: str
    ):
        """
        Sends an HMAC-SHA256 signed HTTP POST to the agent's webhook endpoint.
        Executed in background threadpool.
        Logs delivery attempt, status code, and latency in the database.
        """
        payload_bytes = json.dumps(payload_dict, default=str).encode("utf-8")
        signature = security_service.generate_hmac_signature(payload_bytes, webhook_secret)

        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
            "X-Event-Type": "post.published",
            "User-Agent": "AgentSocialNetwork-RoutingDispatcher/1.0"
        }

        db = SessionLocal()
        try:
            timeout_cfg = httpx.Timeout(4.0, connect=1.5)
            with httpx.Client(timeout=timeout_cfg) as client:
                response = client.post(webhook_url, content=payload_bytes, headers=headers)
                status_code = response.status_code
                response_text = response.text[:1000]

            log_entry = db.query(RoutingLog).filter(RoutingLog.id == routing_log_id).first()
            if log_entry:
                log_entry.webhook_status_code = status_code
                log_entry.webhook_response_body = response_text
                if 200 <= status_code < 300:
                    log_entry.status = "NOTIFIED"
                else:
                    log_entry.status = "FAILED"

            feedback_service.record_notification_sent(db, target_agent_id)
            db.commit()

        except Exception as e:
            log_entry = db.query(RoutingLog).filter(RoutingLog.id == routing_log_id).first()
            if log_entry:
                log_entry.status = "FAILED"
                log_entry.webhook_response_body = f"Delivery connection error: {str(e)}"
            db.commit()
        finally:
            db.close()


webhook_dispatcher = WebhookDispatcher()
