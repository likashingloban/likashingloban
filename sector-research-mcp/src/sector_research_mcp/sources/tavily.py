"""Tavily search + extract — the primary discovery / scraping layer."""

from __future__ import annotations

from typing import Any

from .. import config
from .base import err, ok, request_json

SEARCH_URL = "https://api.tavily.com/search"
EXTRACT_URL = "https://api.tavily.com/extract"


async def search(
    query: str,
    *,
    max_results: int = 8,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    search_depth: str = "advanced",
    topic: str = "general",
    days: int | None = None,
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """Run a Tavily web search, optionally constrained to the source whitelist.

    ``days`` constrains recency (useful for the 12-month funding/exit windows
    when combined with ``topic='news'``).
    """
    if not config.TAVILY_API_KEY:
        return err("TAVILY_API_KEY is not set; cannot run web_search.")

    payload: dict[str, Any] = {
        "api_key": config.TAVILY_API_KEY,
        "query": query,
        "max_results": max(1, min(max_results, 20)),
        "search_depth": search_depth,
        "topic": topic,
        "include_answer": False,
        "include_raw_content": include_raw_content,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    if days is not None:
        payload["days"] = days

    res = await request_json("POST", SEARCH_URL, json=payload)
    if not res["ok"]:
        return res

    data = res["data"]
    results = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content"),
            "score": r.get("score"),
            "published_date": r.get("published_date"),
            "raw_content": r.get("raw_content") if include_raw_content else None,
        }
        for r in data.get("results", [])
    ]
    return ok(query=query, result_count=len(results), results=results)


async def extract(urls: list[str], *, extract_depth: str = "advanced") -> dict[str, Any]:
    """Extract cleaned content from up to 20 URLs."""
    if not config.TAVILY_API_KEY:
        return err("TAVILY_API_KEY is not set; cannot run extract_url.")
    if not urls:
        return err("Provide at least one URL to extract.")

    payload = {
        "api_key": config.TAVILY_API_KEY,
        "urls": urls[:20],
        "extract_depth": extract_depth,
    }
    res = await request_json("POST", EXTRACT_URL, json=payload)
    if not res["ok"]:
        return res
    data = res["data"]
    return ok(
        results=[
            {"url": r.get("url"), "raw_content": r.get("raw_content")}
            for r in data.get("results", [])
        ],
        failed=data.get("failed_results", []),
    )
