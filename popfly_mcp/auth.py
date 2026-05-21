from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

CONFIG_DIR = Path.home() / ".config" / "popfly-mcp"
TOKENS_FILE = CONFIG_DIR / "tokens.json"

POPFLY_API = "https://api.popfly.com/api/v1"


def load_tokens() -> dict:
    if not TOKENS_FILE.exists():
        raise RuntimeError(
            f"No credentials found at {TOKENS_FILE}. Run `popfly-mcp auth` first."
        )
    return json.loads(TOKENS_FILE.read_text())


def save_tokens(tokens: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(TOKENS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(tokens, f, indent=2)


def refresh_tokens(tokens: dict) -> dict:
    """Exchange the refresh token for a new access token. Returns updated tokens dict."""
    refresh_token = tokens.get("refresh_token", "")
    if not refresh_token:
        raise RuntimeError("No refresh token stored. Run `popfly-mcp auth` again.")

    resp = httpx.post(
        f"{POPFLY_API}/auth/refresh",
        headers={
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://app.popfly.com",
            "Referer": "https://app.popfly.com/",
            "Cookie": f"refreshToken={refresh_token}",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    new_access = data.get("accessToken", "")
    if not new_access:
        raise RuntimeError("Refresh response missing accessToken.")

    # Popfly rotates the refresh token on each use — capture it from Set-Cookie.
    new_refresh = refresh_token
    for part in resp.headers.get("set-cookie", "").split(";"):
        part = part.strip()
        if part.startswith("refreshToken="):
            new_refresh = part[len("refreshToken="):]
            break

    updated = {**tokens, "access_token": new_access, "refresh_token": new_refresh}
    save_tokens(updated)
    return updated
