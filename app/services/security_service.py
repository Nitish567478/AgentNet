import hmac
import hashlib
import json
import re
from typing import Tuple, Optional

# Known prompt injection & jailbreak patterns (spec.md Section 6.B)
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+(guidelines|instructions|rules)",
    r"you\s+are\s+now\s+(a|an)?\s*(unrestricted|jailbroken|developer\s+mode|dan)",
    r"(reveal|output|print|leak|exfiltrate)\s+(your\s+)?(secret|token|api_key|password|system\s+prompt)",
    r"system\s*:\s*override",
    r"assistant\s*:\s*sure,\s*i\s*will",
    r"<\s*script[^>]*>",
    r"eval\s*\(",
    r"exec\s*\("
]


class SecurityService:
    @staticmethod
    def inspect_content_safety(title: str, content: str) -> Tuple[bool, Optional[str]]:
        """
        Inspect incoming text for indirect prompt injection and security risks.
        Returns (is_safe: bool, violation_reason: Optional[str]).
        """
        combined = f"{title}\n{content}".lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return False, f"Prompt injection or unauthorized directive pattern matched: '{pattern}'"

        return True, None

    @staticmethod
    def generate_hmac_signature(payload_bytes: bytes, secret: str) -> str:
        """
        Generates HMAC-SHA256 signature for outgoing webhook payload.
        Header format: sha256=<hex_digest>
        """
        mac = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256)
        return f"sha256={mac.hexdigest()}"

    @staticmethod
    def verify_hmac_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
        """
        Verifies HMAC-SHA256 signature from incoming webhook headers.
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header.split("sha256=")[1].strip()
        actual_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_sig, actual_sig)


security_service = SecurityService()

