"""
Exhaustive tests for the KovaMind client — every public method, every error path.
"""

from unittest.mock import patch

import pytest
import responses as rsps_lib
from responses import matchers

from kovamind import (
    KovaMind,
    AuthError,
    RateLimitError,
    NotFoundError,
    ServerError,
    KovaMindError,
)
from kovamind.models import (
    ExtractResult,
    RecallResult,
    ReinforcementResult,
    EmotionalContext,
    HealthStatus,
    SurpriseResult,
)

BASE_URL = "https://api.kovamind.io"
API_KEY = "km_live_testhexhexhexhexhexhexhexhex01"


@pytest.fixture
def kova():
    return KovaMind(api_key=API_KEY, base_url=BASE_URL)


# ── extract ──────────────────────────────────────────────────────────


@rsps_lib.activate
def test_extract_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/extract",
        json={
            "patterns": [
                {"id": "1", "pattern": "Prefers dark mode", "category": "preference",
                 "confidence": 0.95, "user_id": "alex", "tenant_id": "t1"},
            ]
        },
        status=200,
    )
    result = kova.extract(
        conversation=[{"role": "user", "content": "I love dark mode"}],
        user_id="alex",
    )
    assert isinstance(result, ExtractResult)
    assert len(result.patterns) == 1
    assert result.patterns[0].pattern == "Prefers dark mode"
    assert result.patterns[0].confidence == 0.95
    assert result.patterns[0].category == "preference"


@rsps_lib.activate
def test_extract_with_session_id(kova):
    def req_callback(request):
        import json
        body = json.loads(request.body)
        assert body["session_id"] == "sess-42"
        return (200, {}, json.dumps({"patterns": []}))

    rsps_lib.add_callback(rsps_lib.POST, f"{BASE_URL}/memory/extract", callback=req_callback)
    kova.extract(conversation=[], user_id="alex", session_id="sess-42")


@rsps_lib.activate
def test_extract_empty_patterns(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", json={"patterns": []}, status=200)
    result = kova.extract(conversation=[], user_id="alex")
    assert isinstance(result, ExtractResult)
    assert len(result.patterns) == 0


@rsps_lib.activate
def test_extract_auth_error_401(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=401)
    with pytest.raises(AuthError) as exc_info:
        kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 401


@rsps_lib.activate
def test_extract_rate_limit_429(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=429, headers={"Retry-After": "30"})
    with patch("kovamind.client.time.sleep"):
        with pytest.raises(RateLimitError) as exc_info:
            kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 30


@rsps_lib.activate
def test_extract_429_retries_then_succeeds(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=429)
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", json={"patterns": []}, status=200)
    with patch("kovamind.client.time.sleep"):
        result = kova.extract(conversation=[], user_id="alex")
    assert isinstance(result, ExtractResult)


@rsps_lib.activate
def test_extract_server_error_500(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=500)
    with pytest.raises(ServerError) as exc_info:
        kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 500


# ── recall ───────────────────────────────────────────────────────────


@rsps_lib.activate
def test_recall_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/retrieve",
        json={
            "patterns": [
                {"id": "1", "pattern": "Prefers dark mode", "category": "preference",
                 "confidence": 0.9, "user_id": "alex", "tenant_id": "t1"},
            ]
        },
        status=200,
    )
    result = kova.recall(context="what does alex like?", user_id="alex")
    assert isinstance(result, RecallResult)
    assert result.query == "what does alex like?"
    assert len(result.patterns) == 1


@rsps_lib.activate
def test_recall_empty_results(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/retrieve", json={"patterns": []}, status=200)
    result = kova.recall(context="anything", user_id="alex")
    assert len(result.patterns) == 0


@rsps_lib.activate
def test_recall_custom_params(kova):
    def req_callback(request):
        import json
        body = json.loads(request.body)
        assert body["max_patterns"] == 5
        assert body["min_confidence"] == 0.8
        return (200, {}, json.dumps({"patterns": []}))

    rsps_lib.add_callback(rsps_lib.POST, f"{BASE_URL}/memory/retrieve", callback=req_callback)
    kova.recall(context="test", user_id="alex", max_patterns=5, min_confidence=0.8)


# ── reinforce ────────────────────────────────────────────────────────


@rsps_lib.activate
def test_reinforce_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/reinforce",
        json={"pattern_id": "17", "type": "confirmed", "success": True},
        status=200,
    )
    result = kova.reinforce(pattern_id="17", reinforcement_type="confirmed")
    assert isinstance(result, ReinforcementResult)
    assert result.pattern_id == "17"
    assert result.success is True


@rsps_lib.activate
def test_reinforce_with_context(kova):
    def req_callback(request):
        import json
        body = json.loads(request.body)
        assert body["context"] == "User confirmed this"
        return (200, {}, json.dumps({"success": True}))

    rsps_lib.add_callback(rsps_lib.POST, f"{BASE_URL}/memory/reinforce", callback=req_callback)
    kova.reinforce(pattern_id="17", reinforcement_type="confirmed", context="User confirmed this")


@rsps_lib.activate
def test_reinforce_not_found_404(kova):
    rsps_lib.add(
        rsps_lib.POST, f"{BASE_URL}/memory/reinforce",
        json={"detail": "Pattern not found"}, status=404,
    )
    with pytest.raises(NotFoundError):
        kova.reinforce(pattern_id="999", reinforcement_type="confirmed")


# ── surprise ─────────────────────────────────────────────────────────


@rsps_lib.activate
def test_surprise_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/surprise",
        json={"surprise_score": 0.82, "route": "contradict"},
        status=200,
    )
    result = kova.surprise(content="Alex prefers light mode", user_id="alex")
    assert isinstance(result, SurpriseResult)
    assert result.score == 0.82
    assert result.route == "contradict"


@rsps_lib.activate
def test_surprise_low_score_reinforce(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/surprise",
        json={"surprise_score": 0.1, "route": "reinforce"},
        status=200,
    )
    result = kova.surprise(content="Alex likes dark mode", user_id="alex")
    assert result.score == 0.1
    assert result.route == "reinforce"


# ── context ──────────────────────────────────────────────────────────


@rsps_lib.activate
def test_context_success(kova):
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE_URL}/memory/context",
        json={
            "conversation_id": "conv-123",
            "emotions": {"joy": 0.8, "curiosity": 0.6},
            "dominant_emotion": "joy",
            "sentiment": "positive",
        },
        status=200,
    )
    result = kova.context(conversation_id="conv-123")
    assert isinstance(result, EmotionalContext)
    assert result.conversation_id == "conv-123"
    assert result.dominant_emotion == "joy"
    assert result.sentiment == "positive"
    assert result.emotions["joy"] == 0.8


@rsps_lib.activate
def test_context_not_found_404(kova):
    rsps_lib.add(
        rsps_lib.GET, f"{BASE_URL}/memory/context",
        json={"detail": "Conversation not found"}, status=404,
    )
    with pytest.raises(NotFoundError):
        kova.context(conversation_id="nonexistent")


# ── health ───────────────────────────────────────────────────────────


@rsps_lib.activate
def test_health_success(kova):
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/health", json={"status": "ok", "version": "1.0.0"}, status=200)
    result = kova.health()
    assert isinstance(result, HealthStatus)
    assert result.status == "ok"
    assert result.version == "1.0.0"


@rsps_lib.activate
def test_health_server_error(kova):
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/health", status=503)
    with pytest.raises(ServerError) as exc_info:
        kova.health()
    assert exc_info.value.status_code == 503


# ── auth & config ────────────────────────────────────────────────────


@rsps_lib.activate
def test_bearer_token_sent(kova):
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE_URL}/health",
        json={"status": "ok"},
        match=[matchers.header_matcher({"Authorization": f"Bearer {API_KEY}"})],
        status=200,
    )
    kova.health()


@rsps_lib.activate
def test_custom_base_url():
    custom_url = "https://custom.example.com"
    kova = KovaMind(api_key=API_KEY, base_url=custom_url)
    rsps_lib.add(rsps_lib.GET, f"{custom_url}/health", json={"status": "ok"}, status=200)
    result = kova.health()
    assert result.status == "ok"


def test_default_base_url():
    kova = KovaMind(api_key=API_KEY)
    assert kova._base_url == "https://api.kovamind.io"


def test_trailing_slash_stripped():
    kova = KovaMind(api_key=API_KEY, base_url="https://example.com/")
    assert kova._base_url == "https://example.com"


# ── error edge cases ────────────────────────────────────────────────


@rsps_lib.activate
def test_generic_error_422(kova):
    rsps_lib.add(
        rsps_lib.POST, f"{BASE_URL}/memory/extract",
        json={"detail": "Validation error"}, status=422,
    )
    with pytest.raises(KovaMindError) as exc_info:
        kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 422


@rsps_lib.activate
def test_retry_respects_retry_after_header(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=429, headers={"Retry-After": "5"})
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", json={"patterns": []}, status=200)
    with patch("kovamind.client.time.sleep") as mock_sleep:
        kova.extract(conversation=[], user_id="alex")
    mock_sleep.assert_called_once_with(5.0)
