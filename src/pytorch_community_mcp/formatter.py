"""Unified output formatting for all MCP tools."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def safe_parse_date(value: str) -> str:
    """Try to parse a date string and return ISO date, or return as-is."""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return value[:10] if value else ""


def format_results(
    tool_name: str,
    params: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    total_count: int | None = None,
    rate_limit_remaining: int | None = None,
    rate_limit_total: int | None = None,
    truncated: bool = False,
) -> str:
    """Format tool results into unified Markdown output.

    Each item dict should have keys like: title, date, author, url, description.
    """
    lines: list[str] = []

    # Summary section
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Tool:** `{tool_name}`")
    param_parts = [f"{k}={v!r}" for k, v in params.items() if v is not None]
    if param_parts:
        lines.append(f"**Parameters:** {', '.join(param_parts)}")

    # Show result count with total if available
    if total_count is not None and total_count > len(items):
        lines.append(f"**Results:** {len(items)} / {total_count} total")
    else:
        lines.append(f"**Results:** {len(items)}")

    lines.append(f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    if truncated or (total_count is not None and total_count > len(items)):
        lines.append("")
        lines.append(
            f"> **Note:** Results truncated. Total matching items: {total_count}. "
            f"Use `max_results` parameter to retrieve more."
        )

    # Rate limit warning
    if rate_limit_remaining is not None and rate_limit_total is not None:
        if rate_limit_remaining < rate_limit_total * 0.3:
            lines.append("")
            lines.append(
                f"> **Note:** GitHub API quota low "
                f"({rate_limit_remaining}/{rate_limit_total} remaining). "
                f"Queries may be delayed."
            )

    lines.append("")

    # Results section
    if not items:
        lines.append("## Results")
        lines.append("")
        lines.append("No items matched the query criteria.")
        return "\n".join(lines)

    lines.append("## Results")
    lines.append("")

    for i, item in enumerate(items, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        date = item.get("date", "")
        author = item.get("author", "")
        description = item.get("description", "")

        header = f"### {i}. {title}"
        if url:
            header = f"### {i}. [{title}]({url})"
        lines.append(header)
        lines.append("")

        meta_parts: list[str] = []
        if date:
            meta_parts.append(f"**Date:** {date}")
        if author:
            meta_parts.append(f"**Author:** {author}")
        # Include any extra fields
        for key, value in item.items():
            if key not in ("title", "url", "date", "author", "description") and value:
                label = key.replace("_", " ").title()
                meta_parts.append(f"**{label}:** {value}")
        if meta_parts:
            lines.append(" | ".join(meta_parts))
            lines.append("")

        if description:
            lines.append(description)
            lines.append("")

    return "\n".join(lines)


def format_error(error_type: str, message: str, resolution: str | None = None) -> str:
    """Format a standardized error response."""
    lines: list[str] = []
    lines.append("## Error")
    lines.append("")
    lines.append(f"**Type:** {error_type}")
    lines.append(f"**Message:** {message}")
    if resolution:
        lines.append(f"**Resolution:** {resolution}")
    return "\n".join(lines)
