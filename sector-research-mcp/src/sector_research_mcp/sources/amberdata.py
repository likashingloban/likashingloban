"""Amberdata API — on-chain and market data."""

from __future__ import annotations

from typing import Any

from .. import config
from .base import err, ok, request_json

BASE = "https://api.amberdata.com"


def _headers() -> dict[str, str]:
    return {
        "x-api-key": config.AMBERDATA_API_KEY or "",
        "accept": "application/json",
    }


async def spot_price(symbol: str) -> dict[str, Any]:
    """Latest spot price for a pair such as 'usdc_usd'."""
    if not config.AMBERDATA_API_KEY:
        return err("AMBERDATA_API_KEY is not set.")
    url = f"{BASE}/market/spot/prices/pairs/{symbol}/latest"
    res = await request_json("GET", url, headers=_headers())
    if not res["ok"]:
        return res
    return ok(symbol=symbol, data=res["data"].get("payload", res["data"]))


async def get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Escape hatch for any Amberdata REST endpoint (path after the host)."""
    if not config.AMBERDATA_API_KEY:
        return err("AMBERDATA_API_KEY is not set.")
    url = f"{BASE}/{path.lstrip('/')}"
    res = await request_json("GET", url, headers=_headers(), params=params)
    if not res["ok"]:
        return res
    return ok(path=path, data=res["data"])
