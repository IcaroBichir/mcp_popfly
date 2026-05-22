from __future__ import annotations

import httpx

from .auth import POPFLY_API, load_tokens, refresh_tokens
from .cache import CacheStore

_TTL_CAMPAIGNS = 15 * 60  # 15 minutes


class PopflyClient:
    def __init__(self) -> None:
        self._tokens = load_tokens()
        self._cache = CacheStore()

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._tokens['access_token']}",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://app.popfly.com",
            "Referer": "https://app.popfly.com/",
        }

    def _post(self, path: str, **kwargs) -> dict:
        with httpx.Client(timeout=15) as http:
            resp = http.post(
                f"{POPFLY_API}{path}", headers=self._auth_headers(), **kwargs
            )
            if resp.status_code == 401:
                self._tokens = refresh_tokens(self._tokens)
                resp = http.post(
                    f"{POPFLY_API}{path}", headers=self._auth_headers(), **kwargs
                )
            resp.raise_for_status()
            return resp.json()

    def list_campaigns(self, cursor: int = 0, limit: int = 16) -> dict:
        creator_id = self._tokens["creator_id"]
        cache_key = f"campaigns:{creator_id}:{cursor}:{limit}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        data = self._post(
            "/creator-campaign/campaigns/query",
            params={"creatorId": creator_id, "limit": limit, "nextCursor": cursor},
        )
        self._cache.set(cache_key, data, ttl=_TTL_CAMPAIGNS)
        return data
