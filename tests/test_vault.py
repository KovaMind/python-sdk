"""Tests for Vault v2 SDK methods."""
import pytest
from unittest.mock import patch, MagicMock
from kovamind import KovaMind


@pytest.fixture
def client():
    return KovaMind(api_key="km_test_xxx")


def _mock_response(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.ok = 200 <= status < 400
    resp.json.return_value = data
    resp.text = str(data)
    resp.headers = {}
    return resp


class TestVaultSetup:
    def test_vault_setup_returns_words(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"status": "created", "recovery_words": ["w"] * 12})):
            result = client.vault_setup("strongpass")
            assert result["status"] == "created"
            assert len(result["recovery_words"]) == 12


class TestVaultUnlock:
    def test_vault_unlock_success(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"status": "unlocked"})):
            result = client.vault_unlock("strongpass")
            assert result["status"] == "unlocked"


class TestVaultLock:
    def test_vault_lock_success(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"status": "locked"})):
            result = client.vault_lock()
            assert result["status"] == "locked"


class TestVaultStore:
    def test_vault_store_returns_handle(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"handle": "h" * 32, "label": "Key"})):
            result = client.vault_store("Key", "api_key", {"key": "sk-test"})
            assert "handle" in result
            assert "sk-test" not in str(result)


class TestVaultList:
    def test_vault_list_returns_metadata_no_values(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"credentials": [{"id": "c1", "label": "Key", "schema_type": "api_key", "tags": None, "created_at": "2026-01-01"}]})):
            result = client.vault_list()
            assert len(result) == 1
            assert "key" not in result[0] or result[0].get("key") is None


class TestVaultDelete:
    def test_vault_delete_success(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"status": "deleted", "id": "c1"})):
            result = client.vault_delete("c1")
            assert result["status"] == "deleted"


class TestVaultHandles:
    def test_vault_handles_returns_labels_only(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"handles": [{"handle": "h" * 32, "label": "Key", "schema_type": "api_key"}]})):
            result = client.vault_handles()
            assert len(result) == 1
            assert set(result[0].keys()) == {"handle", "label", "schema_type"}

    def test_vault_handles_response_keys(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"handles": [{"handle": "h" * 32, "label": "Key", "schema_type": "api_key"}]})):
            result = client.vault_handles()
            for h in result:
                assert "password" not in h
                assert "secret" not in h
                assert "value" not in h


class TestVaultExecute:
    def test_vault_execute_returns_result_not_credential(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"success": True, "output": "OK", "error": None, "status_code": 200})):
            result = client.vault_execute("h" * 32, "http_request", "https://api.example.com")
            assert result["success"] is True
            assert "output" in result

    def test_vault_execute_error_no_credential_leak(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"success": False, "output": "", "error": "ConnectionError", "status_code": None})):
            result = client.vault_execute("h" * 32, "http_request", "https://bad.com")
            assert result["success"] is False
            assert "password" not in str(result).lower()
            assert "secret" not in str(result).lower()


class TestVaultRecover:
    def test_vault_recover_success(self, client):
        with patch.object(client._session, "request", return_value=_mock_response({"status": "recovered", "recovery_words": ["new"] * 12})):
            result = client.vault_recover(["word"] * 12, "newstrongpass")
            assert result["status"] == "recovered"


class TestNoPlantext:
    def test_grep_no_plaintext_in_codebase(self):
        import os, re
        sdk_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, dirs, files in os.walk(os.path.join(sdk_dir, "kovamind")):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                # Check vault methods don't return raw credential fields
                assert "decrypt" not in content, f"Found 'decrypt' in {path}"
                assert "plaintext" not in content.lower() or "no plaintext" in content.lower() or "never" in content.lower(), f"Suspicious 'plaintext' in {path}"
