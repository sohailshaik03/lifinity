from __future__ import annotations

import os
import random
from typing import Any, Dict, Optional
from ..logger import logger

# Model configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gpt-4o-mini")
ROLLOUT_PERCENT = int(os.getenv("AI_ROLLOUT_PERCENT", "0"))

# Track which model was used for each request (for monitoring)
_last_model_used = FALLBACK_MODEL


def _should_use_new_model(user_id: int | None = None) -> bool:
    """Deterministic rollout: if user_id provided, hash it for consistent rollout.
    Otherwise use random percent."""
    if ROLLOUT_PERCENT <= 0:
        return False
    if ROLLOUT_PERCENT >= 100:
        return True
    if user_id is not None:
        # Deterministic hash-based rollout
        return (hash(user_id) % 100) < ROLLOUT_PERCENT
    # Random for anonymous calls
    return random.random() * 100 < ROLLOUT_PERCENT


def get_active_model(user_id: int | None = None) -> str:
    """Return the model that should be used for this request."""
    return MODEL_NAME if _should_use_new_model(user_id) else FALLBACK_MODEL


def call_chat_api(
    messages: list[Dict[str, Any]],
    user_id: int | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Call OpenAI chat API with feature-flag rollout.

    Returns: {content, model_used, tokens_used, error}
    """
    chosen_model = get_active_model(user_id)
    global _last_model_used
    _last_model_used = chosen_model

    try:
        import openai

        openai.api_key = os.getenv("OPENAI_API_KEY")
        resp = openai.ChatCompletion.create(
            model=chosen_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        logger.info(f"AI call succeeded: model={chosen_model} user={user_id}")

        return {
            "content": resp["choices"][0]["message"]["content"],
            "model_used": chosen_model,
            "tokens_used": resp.get("usage", {}).get("total_tokens", 0),
            "error": None,
        }
    except Exception as e:
        logger.error(f"AI call failed: model={chosen_model} error={e}")
        return {
            "content": None,
            "model_used": chosen_model,
            "tokens_used": 0,
            "error": str(e),
        }


def get_rollout_status() -> Dict[str, Any]:
    """Return current rollout configuration and stats."""
    return {
        "model_name": MODEL_NAME,
        "fallback_model": FALLBACK_MODEL,
        "rollout_percent": ROLLOUT_PERCENT,
        "last_model_used": _last_model_used,
    }
