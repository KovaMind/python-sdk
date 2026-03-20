"""
kovamind.models -- Response models for the Kova Mind SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Pattern:
    """A memory pattern extracted from conversation messages."""

    id: str
    pattern: str
    category: str = ""
    confidence: float = 1.0
    user_id: str = ""
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pattern":
        return cls(
            id=str(data.get("id", "")),
            pattern=data.get("pattern", ""),
            category=data.get("category", ""),
            confidence=float(data.get("confidence", 1.0)),
            user_id=data.get("user_id", ""),
            tenant_id=data.get("tenant_id", ""),
            metadata={k: v for k, v in data.items()
                      if k not in {"id", "pattern", "category", "confidence", "user_id", "tenant_id"}},
        )


@dataclass
class ExtractResult:
    """Result from a memory extraction call."""

    patterns: list[Pattern]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractResult":
        patterns_data = data.get("patterns", data.get("results", []))
        if isinstance(patterns_data, list):
            patterns = [Pattern.from_dict(p) if isinstance(p, dict) else p for p in patterns_data]
        else:
            patterns = []
        return cls(patterns=patterns, raw=data)


@dataclass
class RecallResult:
    """Result from a memory recall/retrieve call."""

    patterns: list[Pattern]
    query: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], query: str = "") -> "RecallResult":
        patterns_data = data.get("patterns", data.get("results", data.get("memories", [])))
        if isinstance(patterns_data, list):
            patterns = [Pattern.from_dict(p) if isinstance(p, dict) else p for p in patterns_data]
        else:
            patterns = []
        return cls(patterns=patterns, query=query, raw=data)


@dataclass
class ReinforcementResult:
    """Result from a pattern reinforcement call."""

    pattern_id: str
    reinforcement_type: str
    success: bool = True
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], pattern_id: str = "", reinforcement_type: str = "") -> "ReinforcementResult":
        return cls(
            pattern_id=data.get("pattern_id", pattern_id),
            reinforcement_type=data.get("type", reinforcement_type),
            success=data.get("success", True),
            raw=data,
        )


@dataclass
class EmotionalContext:
    """Emotional/contextual state for a conversation."""

    conversation_id: str
    emotions: dict[str, float] = field(default_factory=dict)
    dominant_emotion: str = ""
    sentiment: str = "neutral"
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], conversation_id: str = "") -> "EmotionalContext":
        return cls(
            conversation_id=data.get("conversation_id", conversation_id),
            emotions=data.get("emotions", {}),
            dominant_emotion=data.get("dominant_emotion", ""),
            sentiment=data.get("sentiment", "neutral"),
            raw=data,
        )


@dataclass
class HealthStatus:
    """Server health information."""

    status: str
    version: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthStatus":
        return cls(
            status=data.get("status", "unknown"),
            version=data.get("version", ""),
            raw=data,
        )


@dataclass
class SurpriseResult:
    """Result from a /memory/surprise request."""

    score: float
    route: str
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SurpriseResult":
        return cls(
            score=float(data.get("surprise_score", data.get("score", 0.0))),
            route=data.get("route", "update"),
            content=data.get("content", ""),
            metadata={k: v for k, v in data.items()
                      if k not in ("surprise_score", "score", "route", "content")},
        )


@dataclass
class VaultSetupResult:
    """Result from vault setup."""

    status: str
    recovery_words: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultSetupResult":
        return cls(status=data.get("status", ""), recovery_words=data.get("recovery_words", []), raw=data)


@dataclass
class VaultHandle:
    """An opaque handle for a vault credential."""

    handle: str
    label: str
    schema_type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultHandle":
        return cls(handle=data.get("handle", ""), label=data.get("label", ""), schema_type=data.get("schema_type", ""))


@dataclass
class VaultCredentialMeta:
    """Metadata for a vault credential (no secret values)."""

    id: str
    label: str
    schema_type: str
    tags: str | None = None
    created_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultCredentialMeta":
        return cls(id=data.get("id", ""), label=data.get("label", ""), schema_type=data.get("schema_type", ""),
                   tags=data.get("tags"), created_at=data.get("created_at", ""))


@dataclass
class VaultExecuteResult:
    """Result from vault execute (never contains credential values)."""

    success: bool
    output: str
    error: str | None = None
    status_code: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultExecuteResult":
        return cls(success=data.get("success", False), output=data.get("output", ""),
                   error=data.get("error"), status_code=data.get("status_code"), raw=data)
