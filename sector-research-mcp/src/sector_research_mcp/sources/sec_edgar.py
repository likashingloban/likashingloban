"""SEC EDGAR — free filings + company facts (10-K, 10-Q, 8-K).

No API key required; SEC asks only for a descriptive User-Agent with a contact
address (set SEC_EDGAR_USER_AGENT).
"""

from __future__ import annotations

from typing import Any

from .. import config
from .base import err, ok, request_json, request_text

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
FTS_URL = "https://efts.sec.gov/LATEST/search-index?q={q}"

_ticker_cache: dict[str, int] = {}


def _headers() -> dict[str, str]:
    return {"User-Agent": config.SEC_EDGAR_USER_AGENT, "Accept-Encoding": "gzip, deflate"}


async def _load_ticker_map() -> dict[str, int]:
    global _ticker_cache
    if _ticker_cache:
        return _ticker_cache
    res = await request_json("GET", TICKERS_URL, headers=_headers())
    if not res["ok"]:
        return {}
    mapping: dict[str, int] = {}
    for row in res["data"].values():
        mapping[str(row["ticker"]).upper()] = int(row["cik_str"])
    _ticker_cache = mapping
    return mapping


async def resolve_cik(ticker_or_cik: str) -> int | None:
    t = ticker_or_cik.strip().upper()
    if t.isdigit():
        return int(t)
    mapping = await _load_ticker_map()
    return mapping.get(t)


async def recent_filings(
    ticker_or_cik: str,
    *,
    forms: list[str] | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    """Most recent filings for a company, optionally filtered by form type."""
    cik = await resolve_cik(ticker_or_cik)
    if cik is None:
        return err(f"Could not resolve '{ticker_or_cik}' to a CIK.")
    res = await request_json(
        "GET", SUBMISSIONS_URL.format(cik=cik), headers=_headers()
    )
    if not res["ok"]:
        return res
    data = res["data"]
    recent = data.get("filings", {}).get("recent", {})
    forms_set = {f.upper() for f in forms} if forms else None
    out: list[dict[str, Any]] = []
    accession = recent.get("accessionNumber", [])
    for i in range(len(accession)):
        form = recent.get("form", [])[i]
        if forms_set and form.upper() not in forms_set:
            continue
        acc_nodash = accession[i].replace("-", "")
        primary = recent.get("primaryDocument", [])[i]
        out.append(
            {
                "form": form,
                "filing_date": recent.get("filingDate", [])[i],
                "report_date": recent.get("reportDate", [])[i],
                "accession": accession[i],
                "url": (
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                    f"{acc_nodash}/{primary}"
                ),
            }
        )
        if len(out) >= limit:
            break
    return ok(
        ticker=ticker_or_cik.upper(),
        cik=cik,
        company=data.get("name"),
        filings=out,
    )


async def company_concept(
    ticker_or_cik: str, concept: str = "Revenues", taxonomy: str = "us-gaap"
) -> dict[str, Any]:
    """Pull a single XBRL concept's recent values (e.g. Revenues, GrossProfit)."""
    cik = await resolve_cik(ticker_or_cik)
    if cik is None:
        return err(f"Could not resolve '{ticker_or_cik}' to a CIK.")
    url = (
        f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/"
        f"{taxonomy}/{concept}.json"
    )
    res = await request_json("GET", url, headers=_headers())
    if not res["ok"]:
        return res
    units = res["data"].get("units", {})
    points = []
    for unit, vals in units.items():
        for v in vals[-8:]:
            points.append(
                {
                    "unit": unit,
                    "value": v.get("val"),
                    "end": v.get("end"),
                    "form": v.get("form"),
                    "fy": v.get("fy"),
                    "fp": v.get("fp"),
                }
            )
    return ok(ticker=ticker_or_cik.upper(), concept=concept, points=points)


async def full_text_search(query: str, *, forms: str | None = None) -> dict[str, Any]:
    """EDGAR full-text search across filings (last ~ rolling window)."""
    params = {"q": query}
    if forms:
        params["forms"] = forms
    res = await request_text(
        "https://efts.sec.gov/LATEST/search-index",
        headers=_headers(),
        params=params,
    )
    return res
