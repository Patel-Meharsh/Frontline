"""Adapter that reuses the existing, tested challenge triage engine."""
import os
import triage
from backend.app.core.config import settings

def classify_message(message_text: str) -> tuple[dict, dict]:
    # Keep the existing CLI engine and API workflow on the same guardrails.
    local, route = triage.local_safety_decision(message_text)
    if local is not None:
        return local, {"tokens": 0, "latency_sec": 0.0, "route": route, "error": None}
    if not settings.groq_api_key:
        return triage.fallback_decision("GROQ_API_KEY is not configured."), {
            "tokens": 0, "latency_sec": 0.0, "route": "configuration_fallback",
            "error": "GROQ_API_KEY is not configured.",
        }
    os.environ["GROQ_API_KEY"] = settings.groq_api_key
    client = triage.get_client()
    return triage.triage_message(client, message_text)
