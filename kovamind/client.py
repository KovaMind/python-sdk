"""
kovamind.client -- Main client for the Kova Mind memory API.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from requests import Response

from .exceptions import AuthError, KovaMindError, NotFoundError, RateLimitError, ServerError
from .models import (
    EmotionalContext,
    ExtractResult,
    HealthStatus,
    RecallResult,
    ReinforcementResult,
    SurpriseResult,
)

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0
_DEFAULT_TIMEOUT = 30
_DEFAULT_BASE_URL = "https://api.kovamind.ai"


class KovaMind:
    """Kova Mind REST client.

    Usage::

        from kovamind import KovaMind

        kova = KovaMind(api_key="km_live_xxx")

        result = kova.extract(
            conversation=[{"role": "user", "content": "I prefer dark mode"}],
            user_id="alex",
        )

        context = kova.recall(context="what does alex like?", user_id="alex")

        kova.reinforce(pattern_id="17", reinforcement_type="confirmed")

        surprise = kova.surprise(content="Alex hates dark mode now", user_id="alex")
        print(surprise.score, surprise.route)

    Args:
        api_key: Your Kova Mind API key (``km_live_...`` or ``km_test_...``).
        base_url: Base URL for the Kova Mind API (default: https://api.kovamind.ai).
        timeout: HTTP request timeout in seconds (default 30).
        session: Optional custom :class:`requests.Session`.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: int = _DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def extract(
        self,
        conversation: list[dict[str, Any]],
        user_id: str,
        *,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> ExtractResult:
        """Extract memory patterns from a list of conversation messages.

        Args:
            conversation: List of message dicts with ``role`` and ``content`` keys.
            user_id: The user whose memory is being updated.
            session_id: Optional session identifier for buffering.
            **kwargs: Additional fields forwarded to the API payload.

        Returns:
            ExtractResult with the extracted patterns.
        """
        payload: dict[str, Any] = {
            "conversation": conversation,
            "user_id": user_id,
            **kwargs,
        }
        if session_id is not None:
            payload["session_id"] = session_id

        data = self._post("/memory/extract", payload)
        return ExtractResult.from_dict(data)

    def recall(
        self,
        context: str,
        user_id: str,
        *,
        max_patterns: int = 10,
        min_confidence: float = 0.3,
        **kwargs: Any,
    ) -> RecallResult:
        """Retrieve memory patterns relevant to a context string.

        Args:
            context: Natural-language context string.
            user_id: The user whose memory to search.
            max_patterns: Maximum number of patterns to return (default 10, max 100).
            min_confidence: Minimum confidence threshold 0.0-1.0 (default 0.3).

        Returns:
            RecallResult with matching patterns.
        """
        payload: dict[str, Any] = {
            "context": context,
            "user_id": user_id,
            "max_patterns": max_patterns,
            "min_confidence": min_confidence,
            **kwargs,
        }
        data = self._post("/memory/retrieve", payload)
        return RecallResult.from_dict(data, query=context)

    def reinforce(
        self,
        pattern_id: str,
        reinforcement_type: str,
        *,
        context: str | None = None,
        **kwargs: Any,
    ) -> ReinforcementResult:
        """Reinforce (confirm, deny, or adjust) a stored pattern.

        Args:
            pattern_id: The ID of the pattern to reinforce.
            reinforcement_type: One of "confirmed", "denied", "strengthened", "weakened".
            context: Optional context explaining the reinforcement.

        Returns:
            ReinforcementResult.
        """
        payload: dict[str, Any] = {
            "pattern_id": pattern_id,
            "reinforcement_type": reinforcement_type,
            **kwargs,
        }
        if context is not None:
            payload["context"] = context

        data = self._post("/memory/reinforce", payload)
        return ReinforcementResult.from_dict(data, pattern_id=pattern_id, reinforcement_type=reinforcement_type)

    def surprise(
        self,
        content: str,
        user_id: str,
        **kwargs: Any,
    ) -> SurpriseResult:
        """Score the surprise of new content against existing memories.

        Args:
            content: The new content to evaluate.
            user_id: The user whose memory to compare against.

        Returns:
            SurpriseResult with score and route.
        """
        payload: dict[str, Any] = {"content": content, "user_id": user_id, **kwargs}
        data = self._post("/memory/surprise", payload)
        return SurpriseResult.from_dict(data)

    def context(
        self,
        conversation_id: str,
        **kwargs: Any,
    ) -> EmotionalContext:
        """Retrieve the emotional/contextual state for a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            EmotionalContext.
        """
        params: dict[str, Any] = {"conversation_id": conversation_id, **kwargs}
        data = self._get("/memory/context", params)
        return EmotionalContext.from_dict(data, conversation_id=conversation_id)

    def health(self) -> HealthStatus:
        """Check the server health status.

        Returns:
            HealthStatus.
        """
        data = self._get("/health", {})
        return HealthStatus.from_dict(data)

    # -- Internal helpers --

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        return self._request_with_retry("POST", url, json=payload)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        return self._request_with_retry("GET", url, params=params)

    def _request_with_retry(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        delay = _RETRY_BASE_DELAY
        for attempt in range(_MAX_RETRIES):
            response = self._session.request(method, url, timeout=self._timeout, **kwargs)
            if response.status_code != 429:
                return self._handle_response(response)

            retry_after: int | None = None
            raw_header = response.headers.get("Retry-After")
            if raw_header is not None:
                try:
                    retry_after = int(raw_header)
                except ValueError:
                    pass

            if attempt < _MAX_RETRIES - 1:
                sleep_time = float(retry_after) if retry_after is not None else delay
                time.sleep(sleep_time)
                delay *= 2
            else:
                raise RateLimitError(retry_after=retry_after)

        raise RateLimitError()

    @staticmethod
    def _handle_response(response: Response) -> dict[str, Any]:
        if response.status_code == 401:
            raise AuthError()

        if response.status_code == 404:
            _try_json = _safe_json(response)
            raise NotFoundError(_try_json.get("detail", "Resource not found"))

        if response.status_code >= 500:
            raise ServerError(status_code=response.status_code)

        if not response.ok:
            _try_json = _safe_json(response)
            detail = _try_json.get("detail", response.text or "Unknown error")
            raise KovaMindError(detail, status_code=response.status_code)

        return _safe_json(response)


def _safe_json(response: Response) -> dict[str, Any]:
    try:
        return response.json()
    except Exception:
        return {}
