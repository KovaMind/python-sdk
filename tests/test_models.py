"""
Exhaustive tests for all model from_dict methods.
"""

from kovamind.models import (
    Pattern,
    ExtractResult,
    RecallResult,
    ReinforcementResult,
    EmotionalContext,
    HealthStatus,
    SurpriseResult,
)


# ── Pattern ──────────────────────────────────────────────────────────


def test_pattern_from_dict():
    data = {
        "id": "42",
        "pattern": "Likes dark mode",
        "category": "preference",
        "confidence": 0.95,
        "user_id": "alex",
        "tenant_id": "t1",
    }
    p = Pattern.from_dict(data)
    assert p.id == "42"
    assert p.pattern == "Likes dark mode"
    assert p.category == "preference"
    assert p.confidence == 0.95
    assert p.user_id == "alex"
    assert p.tenant_id == "t1"


def test_pattern_from_dict_minimal():
    p = Pattern.from_dict({})
    assert p.id == ""
    assert p.pattern == ""
    assert p.category == ""
    assert p.confidence == 1.0
    assert p.user_id == ""
    assert p.tenant_id == ""


def test_pattern_metadata_captures_extra_fields():
    data = {
        "id": "1",
        "pattern": "test",
        "custom_field": "hello",
        "extra": 42,
    }
    p = Pattern.from_dict(data)
    assert p.metadata["custom_field"] == "hello"
    assert p.metadata["extra"] == 42
    assert "id" not in p.metadata
    assert "pattern" not in p.metadata


# ── ExtractResult ────────────────────────────────────────────────────


def test_extract_result_from_dict_patterns_key():
    data = {
        "patterns": [
            {"id": "1", "pattern": "test", "category": "pref", "confidence": 0.9},
        ]
    }
    r = ExtractResult.from_dict(data)
    assert len(r.patterns) == 1
    assert r.patterns[0].pattern == "test"
    assert r.raw == data


def test_extract_result_from_dict_results_key():
    data = {
        "results": [
            {"id": "2", "pattern": "fallback", "confidence": 0.8},
        ]
    }
    r = ExtractResult.from_dict(data)
    assert len(r.patterns) == 1
    assert r.patterns[0].pattern == "fallback"


def test_extract_result_from_dict_empty():
    r = ExtractResult.from_dict({})
    assert len(r.patterns) == 0


# ── RecallResult ─────────────────────────────────────────────────────


def test_recall_result_from_dict_patterns_key():
    data = {"patterns": [{"id": "1", "pattern": "test"}]}
    r = RecallResult.from_dict(data, query="hello")
    assert len(r.patterns) == 1
    assert r.query == "hello"


def test_recall_result_from_dict_memories_key():
    data = {"memories": [{"id": "1", "pattern": "via memories"}]}
    r = RecallResult.from_dict(data)
    assert len(r.patterns) == 1
    assert r.patterns[0].pattern == "via memories"


def test_recall_result_from_dict_empty():
    r = RecallResult.from_dict({})
    assert len(r.patterns) == 0
    assert r.query == ""


# ── ReinforcementResult ──────────────────────────────────────────────


def test_reinforcement_result_from_dict():
    data = {"pattern_id": "17", "type": "confirmed", "success": True}
    r = ReinforcementResult.from_dict(data)
    assert r.pattern_id == "17"
    assert r.reinforcement_type == "confirmed"
    assert r.success is True


def test_reinforcement_result_uses_passed_args():
    r = ReinforcementResult.from_dict({}, pattern_id="99", reinforcement_type="denied")
    assert r.pattern_id == "99"
    assert r.reinforcement_type == "denied"
    assert r.success is True  # default


# ── EmotionalContext ─────────────────────────────────────────────────


def test_emotional_context_from_dict():
    data = {
        "conversation_id": "conv-1",
        "emotions": {"joy": 0.9},
        "dominant_emotion": "joy",
        "sentiment": "positive",
    }
    r = EmotionalContext.from_dict(data)
    assert r.conversation_id == "conv-1"
    assert r.emotions["joy"] == 0.9
    assert r.dominant_emotion == "joy"
    assert r.sentiment == "positive"


def test_emotional_context_defaults():
    r = EmotionalContext.from_dict({}, conversation_id="fallback")
    assert r.conversation_id == "fallback"
    assert r.emotions == {}
    assert r.dominant_emotion == ""
    assert r.sentiment == "neutral"


# ── HealthStatus ─────────────────────────────────────────────────────


def test_health_status_from_dict():
    r = HealthStatus.from_dict({"status": "ok", "version": "2.0"})
    assert r.status == "ok"
    assert r.version == "2.0"


def test_health_status_defaults():
    r = HealthStatus.from_dict({})
    assert r.status == "unknown"
    assert r.version == ""


# ── SurpriseResult ───────────────────────────────────────────────────


def test_surprise_result_surprise_score_key():
    data = {"surprise_score": 0.82, "route": "contradict"}
    r = SurpriseResult.from_dict(data)
    assert r.score == 0.82
    assert r.route == "contradict"


def test_surprise_result_score_key_fallback():
    data = {"score": 0.5, "route": "update"}
    r = SurpriseResult.from_dict(data)
    assert r.score == 0.5
    assert r.route == "update"


def test_surprise_result_defaults():
    r = SurpriseResult.from_dict({})
    assert r.score == 0.0
    assert r.route == "update"
    assert r.content == ""
    assert r.metadata == {}


def test_surprise_result_metadata_captures_extras():
    data = {"surprise_score": 0.3, "route": "reinforce", "extra_field": "hello"}
    r = SurpriseResult.from_dict(data)
    assert r.metadata["extra_field"] == "hello"
    assert "surprise_score" not in r.metadata
