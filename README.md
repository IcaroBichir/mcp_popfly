# popfly-mcp

MCP server for [Popfly](https://app.popfly.com) — browse and filter creator campaigns directly in Claude.

## Features

- **`list_campaigns`** — paginated campaign list with paid/gift filter and 15-minute cache
- **`get_campaign`** — direct link to any campaign by slug
- Auto-refreshes your access token on 401 (no manual `.env` edits after setup)
- Credentials stored locally at `~/.config/popfly-mcp/tokens.json` (mode 0600)

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Setup

### 1. Get your tokens (one-time, ~2 minutes)

**Access token:**
1. Open `app.popfly.com` in Chrome
2. DevTools → Network → Fetch/XHR → click any `query?creatorId=...` request
3. Headers → copy the `Authorization` value (the part after `Bearer `)

**Refresh token:**
1. In the same DevTools session, find a `refresh` POST request
2. Cookies → Request Cookies → copy the `refreshToken` value

**Creator ID:**  
Copy the numeric `creatorId` value from any campaign query URL.

### 2. Store credentials

```bash
.venv/bin/popfly-mcp auth
```

Prompts for the three values above and saves them to `~/.config/popfly-mcp/tokens.json`.

### 3. Register with Claude Code

Add to `~/.claude/.mcp.json` under `mcpServers`:

```json
"popfly": {
  "command": "/path/to/mcp_popfly/.venv/bin/popfly-mcp",
  "args": ["serve"]
}
```

## CLI

```bash
popfly-mcp auth          # store credentials
popfly-mcp serve         # start MCP server (stdio)
popfly-mcp cache stats   # show cache size and entry count
popfly-mcp cache clear   # clear all cached responses
```

## Tools

### `list_campaigns`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 16 | Campaigns per page (max 50) |
| `cursor` | integer | 0 | Pagination cursor from previous response |
| `filter` | string | `"all"` | `"paid"` (cash), `"gift"` (product only), or `"all"` |

### `get_campaign`

| Parameter | Type | Description |
|---|---|---|
| `slug` | string | Campaign slug from `list_campaigns` output |

## Development

```bash
# Run all tests (no live auth needed — all HTTP mocked)
.venv/bin/pytest

# Run a single file
.venv/bin/pytest tests/test_cache.py
```

## Token refresh

The server calls `POST /auth/refresh` with the stored `refreshToken` cookie whenever the API returns 401. Both the new access token and the rotated refresh token are written back to `~/.config/popfly-mcp/tokens.json` automatically.

## API reference

- **Campaigns endpoint:** `POST https://api.popfly.com/api/v1/creator-campaign/campaigns/query`
- **Refresh endpoint:** `POST https://api.popfly.com/api/v1/auth/refresh`
- **Auth:** Bearer JWT from browser session, refreshed automatically
