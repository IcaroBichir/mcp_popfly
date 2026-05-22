from __future__ import annotations

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .client import PopflyClient

mcp = FastMCP(
    "Popfly",
    instructions=(
        "Use these tools to retrieve creator campaigns from Popfly. "
        "Always present compensation clearly, distinguishing cash from product/gift."
    ),
)


def _fmt_date(ms: int | None) -> str:
    if not ms:
        return "N/A"
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")


def _fmt_pay(c: dict) -> str:
    low = c.get("compensationMonetary") or 0
    high = c.get("maxCompensationMonetary")
    other = (c.get("compensationOther") or "").strip()
    parts = []
    if high and high > 0:
        parts.append(f"${low:.0f}–${high:.0f} cash" if low != high else f"${low:.0f} cash")
    elif low > 0:
        parts.append(f"${low:.0f} cash")
    if other:
        parts.append(other)
    return " + ".join(parts) if parts else "Gift/product only"


@mcp.tool()
def list_campaigns(
    limit: int = 16,
    cursor: int = 0,
    filter: str = "all",
) -> str:
    """
    List available Popfly campaigns the creator can apply to.

    Results are served from a 15-minute local cache so repeated calls are cheap.

    Args:
        limit: Campaigns per page (1–50). Default 16.
        cursor: Pagination cursor from a previous response. Default 0.
        filter: "paid" (cash compensation only), "gift" (product only), or "all".
    """
    limit = min(max(1, limit), 50)
    data = PopflyClient().list_campaigns(cursor=cursor, limit=limit)
    campaigns = data.get("campaigns", [])
    next_cursor = data.get("nextCursor")

    if filter == "paid":
        campaigns = [
            c for c in campaigns
            if (c.get("compensationMonetary") or 0) > 0
            or (c.get("maxCompensationMonetary") or 0) > 0
        ]
    elif filter == "gift":
        campaigns = [
            c for c in campaigns
            if not (c.get("compensationMonetary") or 0)
            and not (c.get("maxCompensationMonetary") or 0)
        ]

    if not campaigns:
        return "No campaigns found matching that filter."

    lines = [f"**{len(campaigns)} campaigns** (cursor {cursor}→{next_cursor})\n"]
    for c in campaigns:
        service = c["services"][0]["title"] if c.get("services") else "—"
        applied = " ✓" if c.get("isApplied") else ""
        lines.append(
            f"### {c['title']}{applied}\n"
            f"- **Brand:** {c['companyName']}  |  **Type:** {service}\n"
            f"- **Pay:** {_fmt_pay(c)}\n"
            f"- **Apply by:** {_fmt_date(c.get('applicationDeadline'))}"
            f"  |  **Content due:** {_fmt_date(c.get('contentDeadline'))}\n"
            f"- **Link:** https://app.popfly.com/creators/campaign/{c['slug']}\n"
        )

    if next_cursor and next_cursor > cursor:
        lines.append(
            f"\n_More campaigns available — use `cursor: {next_cursor}` to load next page._"
        )

    return "\n".join(lines)


@mcp.tool()
def get_campaign(slug: str) -> str:
    """
    Get the direct Popfly URL for a campaign by slug.

    Args:
        slug: Campaign slug (e.g. "coalatree-trailhead-pant-...").
              Found in the link field from list_campaigns.
    """
    return f"https://app.popfly.com/creators/campaign/{slug}"
