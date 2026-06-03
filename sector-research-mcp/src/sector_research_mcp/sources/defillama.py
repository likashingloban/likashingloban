"""DefiLlama — free, keyless stablecoin + protocol data.

Especially relevant to the Stablecoins & Payment Rails sector: circulating
supply by asset, by chain, and historical series — all source-traceable.
"""

from __future__ import annotations

from typing import Any

from .base import ok, request_json

STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins"
STABLECOIN_DETAIL_URL = "https://stablecoins.llama.fi/stablecoin/{id}"


async def stablecoins(*, include_prices: bool = True, top: int = 25) -> dict[str, Any]:
    """Ranked stablecoins by circulating supply (USD)."""
    res = await request_json(
        "GET", STABLECOINS_URL, params={"includePrices": str(include_prices).lower()}
    )
    if not res["ok"]:
        return res
    peg = res["data"].get("peggedAssets", [])

    def circ(item: dict[str, Any]) -> float:
        c = item.get("circulating", {}) or {}
        # value is keyed by peg type, e.g. {"peggedUSD": 1234.0}
        return float(next(iter(c.values()), 0) or 0)

    peg.sort(key=circ, reverse=True)
    rows = [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "symbol": a.get("symbol"),
            "peg_type": a.get("pegType"),
            "peg_mechanism": a.get("pegMechanism"),
            "circulating_usd": circ(a),
            "chains": a.get("chains", [])[:12],
        }
        for a in peg[:top]
    ]
    total = sum(r["circulating_usd"] for r in rows)
    return ok(
        source_url="https://defillama.com/stablecoins",
        count=len(rows),
        top_circulating_total_usd=total,
        stablecoins=rows,
    )


async def stablecoin_detail(pegged_id: str) -> dict[str, Any]:
    """Per-chain breakdown and history for one stablecoin id."""
    res = await request_json("GET", STABLECOIN_DETAIL_URL.format(id=pegged_id))
    if not res["ok"]:
        return res
    return ok(id=pegged_id, data=res["data"])
