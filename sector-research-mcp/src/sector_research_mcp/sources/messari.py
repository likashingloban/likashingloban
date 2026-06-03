"""Messari API — crypto/digital-asset fundamentals and market data."""

from __future__ import annotations

from typing import Any

from .. import config
from .base import err, ok, request_json

BASE = "https://data.messari.io/api"


def _headers() -> dict[str, str]:
    return {"x-messari-api-key": config.MESSARI_API_KEY or ""}


async def asset_metrics(slug: str) -> dict[str, Any]:
    """Latest market data + key fundamentals for an asset (e.g. 'tether')."""
    if not config.MESSARI_API_KEY:
        return err("MESSARI_API_KEY is not set.")
    url = f"{BASE}/v1/assets/{slug}/metrics"
    res = await request_json("GET", url, headers=_headers())
    if not res["ok"]:
        return res
    metrics = res["data"].get("data", {})
    market = metrics.get("market_data", {}) or {}
    supply = metrics.get("supply", {}) or {}
    return ok(
        slug=slug,
        price_usd=market.get("price_usd"),
        market_cap_usd=(metrics.get("marketcap") or {}).get("current_marketcap_usd"),
        circulating_supply=supply.get("circulating"),
        volume_24h_usd=market.get("volume_last_24_hours"),
        raw=metrics,
    )


async def asset_profile(slug: str) -> dict[str, Any]:
    """Qualitative profile (sector, category, overview) for an asset."""
    if not config.MESSARI_API_KEY:
        return err("MESSARI_API_KEY is not set.")
    url = f"{BASE}/v2/assets/{slug}/profile"
    res = await request_json("GET", url, headers=_headers())
    if not res["ok"]:
        return res
    return ok(slug=slug, data=res["data"].get("data", {}))
