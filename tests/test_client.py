"""Tests for PopflyClient (client.py)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

_FAKE_TOKENS = {
    "access_token": "fake_access_token",
    "refresh_token": "fake_refresh",
    "creator_id": "99999",
}

_FAKE_CAMPAIGNS_RESPONSE = {
    "campaigns": [
        {
            "title": "Test Campaign",
            "slug": "test-campaign",
            "companyName": "TestBrand",
            "services": [{"title": "TikTok"}],
            "compensationMonetary": 150,
            "maxCompensationMonetary": 300,
            "applicationDeadline": 1_800_000_000_000,
            "contentDeadline": 1_800_100_000_000,
            "isApplied": False,
        }
    ],
    "nextCursor": 16,
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("popfly_mcp.cache._CACHE_PATH", tmp_path / "cache.db")
    monkeypatch.setattr("popfly_mcp.cache.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("popfly_mcp.auth.CONFIG_DIR", tmp_path)
    with patch("popfly_mcp.client.load_tokens", return_value=_FAKE_TOKENS):
        from popfly_mcp.client import PopflyClient
        return PopflyClient()


# ---------------------------------------------------------------------------
# list_campaigns — cache behaviour
# ---------------------------------------------------------------------------

class TestListCampaigns:
    def test_cold_cache_calls_api(self, client):
        with patch.object(client, "_post", return_value=_FAKE_CAMPAIGNS_RESPONSE) as mock_post:
            result = client.list_campaigns(cursor=0, limit=16)

        mock_post.assert_called_once()
        assert result == _FAKE_CAMPAIGNS_RESPONSE

    def test_warm_cache_skips_api(self, client):
        with patch.object(client, "_post", return_value=_FAKE_CAMPAIGNS_RESPONSE):
            client.list_campaigns(cursor=0, limit=16)

        with patch.object(client, "_post") as mock_post:
            result = client.list_campaigns(cursor=0, limit=16)

        mock_post.assert_not_called()
        assert result["campaigns"][0]["title"] == "Test Campaign"

    def test_different_cursor_uses_separate_cache_key(self, client):
        with patch.object(client, "_post", return_value=_FAKE_CAMPAIGNS_RESPONSE) as mock_post:
            client.list_campaigns(cursor=0, limit=16)
            client.list_campaigns(cursor=16, limit=16)

        assert mock_post.call_count == 2

    def test_creator_id_in_post_params(self, client):
        with patch.object(client, "_post", return_value=_FAKE_CAMPAIGNS_RESPONSE) as mock_post:
            client.list_campaigns(cursor=0, limit=16)

        call_kwargs = mock_post.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else {}
        # The creator_id from tokens must be passed to the API
        assert "99999" in str(mock_post.call_args)


# ---------------------------------------------------------------------------
# _post — 401 triggers token refresh
# ---------------------------------------------------------------------------

class TestPostRetry:
    def test_401_triggers_refresh_and_retry(self, client):
        fake_401 = MagicMock()
        fake_401.status_code = 401

        fake_200 = MagicMock()
        fake_200.status_code = 200
        fake_200.json.return_value = _FAKE_CAMPAIGNS_RESPONSE

        new_tokens = {**_FAKE_TOKENS, "access_token": "refreshed_token"}

        with patch("popfly_mcp.client.refresh_tokens", return_value=new_tokens) as mock_refresh, \
             patch("httpx.Client") as mock_http_cls:
            mock_http = MagicMock()
            mock_http_cls.return_value.__enter__.return_value = mock_http
            mock_http.post.side_effect = [fake_401, fake_200]

            result = client._post("/test-path")

        mock_refresh.assert_called_once()
        assert mock_http.post.call_count == 2
        assert result == _FAKE_CAMPAIGNS_RESPONSE
