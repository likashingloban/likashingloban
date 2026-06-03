"""CoinGecko — free (keyless public tier) crypto market data.

Useful for public-comparable / token market caps that aren't equities.
"""

from __future__ import annotations

from typing import Any

from .. import config
from .base import ok, request_json

BASE = "https://api.coingecko.com/api/v3"
PRO_BASE = "https://pro-api.coingecko.com/api/v3"


def _base_and_headers() -> tuple[str, dict[str, str]]:
    if config.COINGECKO_API_KEY:
        return PRO_BASE, {"x-cg-pro-api-key": config.COINGECKO_API_KEY}
    return BASE, {}


async def markets(ids: list[str], *, vs_currency: str = "usd") -> dict[str, Any]:
    """Market snapshot for the given coin ids (e.g. ['usd-coin','tether'])."""
    base, headers = _base_and_headers()
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(ids),
        "order": "market_cap_desc",
        "per_page": str(min(len(ids), 250)),
        "page": "1",
    }
    res = await request_json("GET", f"{base}/coins/markets", headers=headers, params=params)
    if not res["ok"]:
        return res
    rows = [
        {
            "id": c.get("id"),
            "symbol": c.get("symbol"),
            "name": c.get("name"),
            "price_usd": c.get("current_price"),
            "market_cap_usd": c.get("market_cap"),
            "volume_24h_usd": c.get("total_volume"),
            "last_updated": c.get("last_updated"),
        }
        for c in res["data"]
    ]
    return ok(source_url="https://www.coingecko.com", coins=rows)
