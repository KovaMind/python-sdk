"""
Unit tests for the Kova Mind SDK client.

Uses the `responses` library to mock HTTP calls.
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
)

BASE_URL = "https://api.kovamind.ai"
API_KEY = "km_live_testhexhexhexhexhexhexhexhex01"


@pytest.fixture
def kova():
    return KovaMind(api_key=API_KEY, base_url=BASE_URL)


@rsps_lib.activate
def test_extract_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/extract",
        json={
            "patterns": [
                {"id": "1", "pattern": "Prefers dark mode", "category": "preference", "confidence": 0.95,
                 "user_id": "alex", "tenant_id": "nova-001"},
            ]
        },
        status=200,
    )
    result = kova.extract(conversation=[{"role": "user", "content": "I love dark mode"}], user_id="alex")
    assert isinstance(result, ExtractResult)
    assert len(result.patterns) == 1
    assert result.patterns[0].pattern == "Prefers dark mode"
    assert result.patterns[0].confidence == 0.95


@rsps_lib.activate
def test_extract_401_raises_auth_error(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=401)
    with pytest.raises(AuthError) as exc_info:
        kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 401


@rsps_lib.activate
def test_extract_429_raises_rate_limit_error(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/extract",
        status=429,
        headers={"Retry-After": "30"},
    )
    with patch("kovamind.client.time.sleep"):
        with pytest.raises(RateLimitError) as exc_info:
            kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 30


@rsps_lib.activate
def test_extract_429_retries_then_succeeds(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=429)
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/extract",
        json={"patterns": []},
        status=200,
    )
    with patch("kovamind.client.time.sleep"):
        result = kova.extract(conversation=[], user_id="alex")
    assert isinstance(result, ExtractResult)


@rsps_lib.activate
def test_recall_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/retrieve",
        json={
            "patterns": [
                {"id": "1", "pattern": "Prefers dark mode", "category": "preference", "confidence": 0.9,
                 "user_id": "alex", "tenant_id": "nova-001"},
            ]
        },
        status=200,
    )
    result = kova.recall(context="what does alex like?", user_id="alex")
    assert isinstance(result, RecallResult)
    assert result.query == "what does alex like?"
    assert len(result.patterns) == 1


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
def test_reinforce_404(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/memory/reinforce",
        json={"detail": "Pattern not found"},
        status=404,
    )
    with pytest.raises(NotFoundError):
        kova.reinforce(pattern_id="999", reinforcement_type="confirmed")


@rsps_lib.activate
def test_health_success(kova):
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE_URL}/health",
        json={"status": "ok", "version": "1.0.0"},
        status=200,
    )
    result = kova.health()
    assert isinstance(result, HealthStatus)
    assert result.status == "ok"
    assert result.version == "1.0.0"


@rsps_lib.activate
def test_server_error(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/memory/extract", status=500)
    with pytest.raises(ServerError) as exc_info:
        kova.extract(conversation=[], user_id="alex")
    assert exc_info.value.status_code == 500


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
