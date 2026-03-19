"""
Exhaustive tests for Vault methods on the KovaMind client.
"""

from unittest.mock import patch

import pytest
import responses as rsps_lib

from kovamind import KovaMind

BASE_URL = "https://api.kovamind.ai"
API_KEY = "km_live_testvault"


@pytest.fixture
def kova():
    return KovaMind(api_key=API_KEY, base_url=BASE_URL)


# ── vault_status ─────────────────────────────────────────────────


@rsps_lib.activate
def test_vault_status_unlocked(kova):
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/vault/status", json={"status": "unlocked"}, status=200)
    result = kova.vault_status()
    assert result["status"] == "unlocked"


@rsps_lib.activate
def test_vault_status_locked(kova):
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/vault/status", json={"status": "locked"}, status=200)
    result = kova.vault_status()
    assert result["status"] == "locked"


# ── vault_store ──────────────────────────────────────────────────


@rsps_lib.activate
def test_vault_store_success(kova):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/vault/secrets",
        json={"id": "sec-42", "label": "aws-key", "hash": "abc123def456"},
        status=200,
    )
    result = kova.vault_store(agent_id="axiom", label="aws-key", value="AKIA12345")
    assert result["id"] == "sec-42"
    assert result["label"] == "aws-key"
    assert result["hash"] == "abc123def456"


@rsps_lib.activate
def test_vault_store_with_tags(kova):
    def callback(request):
        import json
        body = json.loads(request.body)
        assert body["tags"] == "cloud,aws"
        assert body["agent_id"] == "axiom"
        assert body["label"] == "aws-key"
        return (200, {}, json.dumps({"id": "1", "label": "aws-key", "hash": "h"}))

    rsps_lib.add_callback(rsps_lib.POST, f"{BASE_URL}/vault/secrets", callback=callback)
    kova.vault_store(agent_id="axiom", label="aws-key", value="secret", tags="cloud,aws")


@rsps_lib.activate
def test_vault_store_no_tags(kova):
    def callback(request):
        import json
        body = json.loads(request.body)
        assert "tags" not in body
        return (200, {}, json.dumps({"id": "1", "label": "x", "hash": "h"}))

    rsps_lib.add_callback(rsps_lib.POST, f"{BASE_URL}/vault/secrets", callback=callback)
    kova.vault_store(agent_id="axiom", label="x", value="v")


@rsps_lib.activate
def test_vault_store_403_locked(kova):
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/vault/secrets", json={"detail": "Vault is locked"}, status=403)
    from kovamind import KovaMindError
    with pytest.raises(KovaMindError) as exc_info:
        kova.vault_store(agent_id="axiom", label="x", value="v")
    assert exc_info.value.status_code == 403


# ── vault_get ────────────────────────────────────────────────────


@rsps_lib.activate
def test_vault_get_success(kova):
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE_URL}/vault/secrets/sec-42",
        json={"id": "sec-42", "value": "AKIA12345"},
        status=200,
    )
    result = kova.vault_get(agent_id="axiom", secret_id="sec-42")
    assert result["id"] == "sec-42"
    assert result["value"] == "AKIA12345"


@rsps_lib.activate
def test_vault_get_404(kova):
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/vault/secrets/nonexistent", json={"detail": "Secret not found"}, status=404)
    from kovamind import NotFoundError
    with pytest.raises(NotFoundError):
        kova.vault_get(agent_id="axiom", secret_id="nonexistent")


# ── vault_list ───────────────────────────────────────────────────


@rsps_lib.activate
def test_vault_list_success(kova):
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE_URL}/vault/secrets",
        json={
            "secrets": [
                {"id": "sec-1", "label": "aws-key", "tags": "cloud", "created_at": "2026-03-19T00:00:00Z"},
                {"id": "sec-2", "label": "db-pass", "tags": None, "created_at": "2026-03-19T00:00:00Z"},
            ]
        },
        status=200,
    )
    result = kova.vault_list(agent_id="axiom")
    assert len(result) == 2
    assert result[0]["label"] == "aws-key"
    assert result[1]["label"] == "db-pass"


@rsps_lib.activate
def test_vault_list_empty(kova):
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/vault/secrets", json={"secrets": []}, status=200)
    result = kova.vault_list(agent_id="axiom")
    assert len(result) == 0


# ── vault_delete ─────────────────────────────────────────────────


@rsps_lib.activate
def test_vault_delete_success(kova):
    rsps_lib.add(
        rsps_lib.DELETE,
        f"{BASE_URL}/vault/secrets/sec-42",
        json={"status": "destroyed", "destroyed": True},
        status=200,
    )
    result = kova.vault_delete(agent_id="axiom", secret_id="sec-42")
    assert result["destroyed"] is True


@rsps_lib.activate
def test_vault_delete_not_found(kova):
    rsps_lib.add(
        rsps_lib.DELETE,
        f"{BASE_URL}/vault/secrets/nonexistent",
        json={"status": "not_found", "destroyed": False},
        status=200,
    )
    result = kova.vault_delete(agent_id="axiom", secret_id="nonexistent")
    assert result["destroyed"] is False
