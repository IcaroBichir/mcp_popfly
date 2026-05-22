from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Popfly MCP server — connect Claude to your Popfly creator campaigns."""


@cli.command()
def auth() -> None:
    """Store Popfly credentials locally (~/.config/popfly-mcp/tokens.json)."""
    import json
    from .auth import TOKENS_FILE, save_tokens

    existing = {}
    if TOKENS_FILE.exists():
        try:
            existing = json.loads(TOKENS_FILE.read_text())
        except Exception:
            pass

    click.echo("Open app.popfly.com in Chrome, then open DevTools → Network → Fetch/XHR.")
    click.echo("Click any 'query?creatorId=...' request.\n")

    access_token = click.prompt(
        "Access token (Authorization header value, with or without 'Bearer ')"
    ).removeprefix("Bearer ").strip()
    refresh_token = click.prompt(
        "Refresh token (value of the 'refreshToken' cookie from a /auth/refresh request)"
    ).strip()

    existing_id = existing.get("creator_id", "")
    if existing_id:
        creator_id = existing_id
        click.echo(f"Creator ID: {creator_id} (kept from existing config)")
    else:
        creator_id = click.prompt(
            "Creator ID (numeric value from the creatorId URL parameter)"
        ).strip()

    save_tokens(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "creator_id": creator_id,
        }
    )
    click.echo(f"\nCredentials saved to: {TOKENS_FILE}")
    click.echo("The server auto-refreshes the access token on 401 — no manual updates needed.")


@cli.command()
def serve() -> None:
    """Start the MCP server (stdio transport for Claude)."""
    from .server import mcp

    mcp.run()


@cli.group()
def cache() -> None:
    """Inspect or manage the local response cache."""


@cache.command("stats")
def cache_stats() -> None:
    """Show cache entry count and file size."""
    from .cache import CacheStore

    s = CacheStore().stats()
    click.echo(f"Entries:  {s['total_entries']} total, {s['expired_entries']} expired")
    click.echo(f"Size:     {s['cache_size_bytes'] / 1024:.1f} KB")


@cache.command("clear")
def cache_clear() -> None:
    """Delete all cached responses."""
    from .cache import CacheStore

    count = CacheStore().clear()
    click.echo(f"Cleared {count} cache entries.")


if __name__ == "__main__":
    cli()
