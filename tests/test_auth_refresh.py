"""refresh_tokens must capture the rotated refresh token from Set-Cookie."""
from __future__ import annotations

from unittest.mock import patch

import httpx

from popfly_mcp import auth


def _response(set_cookies: list[str]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"accessToken": "new-access"},
        headers=[("set-cookie", c) for c in set_cookies],
        request=httpx.Request("POST", f"{auth.POPFLY_API}/auth/refresh"),
    )


def _refresh(tmp_path, monkeypatch, set_cookies):
    monkeypatch.setattr(auth, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(auth, "TOKENS_FILE", tmp_path / "tokens.json")
    with patch("popfly_mcp.auth.httpx.post", return_value=_response(set_cookies)):
        return auth.refresh_tokens({"access_token": "old", "refresh_token": "old-rt", "creator_id": "1"})


def test_rotated_token_captured_when_not_first_cookie(tmp_path, monkeypatch):
    out = _refresh(tmp_path, monkeypatch, [
        "session=abc; Path=/; HttpOnly",
        "refreshToken=new-rt; Path=/; HttpOnly; Secure",
    ])
    assert out["refresh_token"] == "new-rt"
    assert out["access_token"] == "new-access"


def test_keeps_old_token_when_not_rotated(tmp_path, monkeypatch):
    assert _refresh(tmp_path, monkeypatch, [])["refresh_token"] == "old-rt"
