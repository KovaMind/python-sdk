"""
kovamind -- Python SDK for the Kova Mind memory API.

Quick start::

    from kovamind import KovaMind

    kova = KovaMind(api_key="km_live_xxx")

    # Extract patterns from conversation messages
    result = kova.extract(
        conversation=[{"role": "user", "content": "I love dark mode"}],
        user_id="alex",
    )

    # Recall relevant patterns
    context = kova.recall(context="what does alex like?", user_id="alex")

    # Reinforce a pattern
    kova.reinforce(pattern_id="17", reinforcement_type="confirmed")

    # Score surprise
    surprise = kova.surprise(content="Alex hates dark mode now", user_id="alex")
"""

from .client import KovaMind
from .exceptions import AuthError, KovaMindError, NotFoundError, RateLimitError, ServerError
from .models import (
    EmotionalContext,
    ExtractResult,
    HealthStatus,
    Pattern,
    RecallResult,
    ReinforcementResult,
    SurpriseResult,
)

__version__ = "0.4.0"
__all__ = [
    "KovaMind",
    "KovaMindError",
    "AuthError",
    "RateLimitError",
    "NotFoundError",
    "ServerError",
    "Pattern",
    "ExtractResult",
    "RecallResult",
    "ReinforcementResult",
    "EmotionalContext",
    "HealthStatus",
    "SurpriseResult",
]
