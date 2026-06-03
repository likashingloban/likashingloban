"""FastMCP server exposing sector market-research tooling.

Design split:
  - The *server* gathers source-traceable data (Tavily/Messari/Amberdata/SEC/
    DefiLlama/CoinGecko), supplies the standardized methodology + skeleton, and
    does the deterministic rubric math + final rendering.
  - The *calling model* does the synthesis, filling the skeleton from the data
    the tools return.

Every tool returns JSON-serializable data and never raises on missing keys.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import config
from . import rubrics as _rub
from .docx_render import render_markdown_to_docx
from .methodology import build_instructions
from .pdf import render_markdown_to_pdf
from .rubrics import ALL_RUBRICS, MarketOpportunity, ScoreCard, average
from .skeleton import build_skeleton, report_basename, report_title
from .sectors import SECTORS, get_sector, list_sector_keys
from .windows import exit_windows, funding_windows
from .sources import (
    amberdata,
    coingecko,
    defillama,
    messari,
    sec_edgar,
    tavily,
)

mcp = FastMCP(
    "sector-research",
    instructions=(
        "Generate standardized, directly comparable sector market-map memos for "
        "Stablecoins & Payment Rails, AI Infrastructure, AI Consumer, and Market "
        "Infrastructure. Start with get_research_instructions(sector) and "
        "get_report_skeleton(sector); gather data with web_search/extract_url and "
        "the SEC/Messari/Amberdata/DefiLlama/CoinGecko tools; compute rubric "
        "scores with compute_scores; finish by calling render_report to emit the "
        "Word (.docx) + Markdown deliverables. Never estimate beyond disclosed data."
    ),
)


# --------------------------------------------------------------------------
# Methodology / structure tools
# --------------------------------------------------------------------------

@mcp.tool()
def list_sectors() -> dict[str, Any]:
    """List the supported sectors with definitions and scope boundaries."""
    return {
        "sectors": [
            {
                "key": s.key,
                "short_name": s.short_name,
                "name": s.name,
                "definition": s.definition,
                "in_scope": s.in_scope,
                "out_of_scope": s.out_of_scope,
                "specialized_apis": s.specialized_apis,
            }
            for s in SECTORS.values()
        ],
        "key_status": config.key_status(),
    }


@mcp.tool()
def get_sector_profile(sector: str) -> dict[str, Any]:
    """Full profile for one sector: scope, seed companies, tickers, sources."""
    s = get_sector(sector)
    return {
        "key": s.key,
        "short_name": s.short_name,
        "name": s.name,
        "definition": s.definition,
        "in_scope": s.in_scope,
        "out_of_scope": s.out_of_scope,
        "seed_public": s.seed_public,
        "seed_private": s.seed_private,
        "tickers": s.tickers,
        "source_domains": s.source_domains,
        "specialized_apis": s.specialized_apis,
        "sample_queries": s.sample_queries,
        "note": (
            "Seed companies are starting points only — expand the universe via "
            "web_search before clustering."
        ),
    }


@mcp.tool()
def get_research_instructions(sector: str) -> dict[str, Any]:
    """Return the full standardized methodology brief for a sector."""
    s = get_sector(sector)
    return {
        "sector": s.key,
        "title": report_title(s),
        "instructions": build_instructions(s),
    }


@mcp.tool()
def get_report_skeleton(sector: str) -> dict[str, Any]:
    """Return the Markdown skeleton (fixed section order + tables + score lines)."""
    s = get_sector(sector)
    return {
        "sector": s.key,
        "title": report_title(s),
        "basename": report_basename(s),
        "skeleton_markdown": build_skeleton(s),
    }


@mcp.tool()
def get_rubrics() -> dict[str, str]:
    """Return all scoring rubrics verbatim."""
    return dict(ALL_RUBRICS)


# --------------------------------------------------------------------------
# Deterministic scoring
# --------------------------------------------------------------------------

@mcp.tool()
def compute_scores(
    funding_by_year_usd: list[float] | None = None,
    competitive_intensity_band: int | None = None,
    market_size_annual_revenue_usd: float | None = None,
    avg_gross_margin_pct: float | None = None,
    growth_cagr_pct: float | None = None,
    exit_12m_max_ma_usd: float = 0.0,
    exit_12m_max_ipo_usd: float = 0.0,
    exit_3y_max_ma_usd: float = 0.0,
    exit_3y_max_ipo_usd: float = 0.0,
) -> dict[str, Any]:
    """Compute every rubric score deterministically from source-backed inputs.

    Provide only the inputs you have; scores you don't supply inputs for are
    omitted. ``funding_by_year_usd`` is the aggregate disclosed funding for each
    of the last 3 years (the Funding Intensity Score averages their bands).
    Exit inputs are the largest in-sector M&A deal value and largest IPO
    size/market cap for each window (USD).
    """
    detail: dict[str, Any] = {}
    card = ScoreCard()

    if funding_by_year_usd:
        bands = [_rub.funding_intensity_band(v) for v in funding_by_year_usd]
        card.funding_intensity = average([float(b) for b in bands])
        detail["funding_year_bands"] = bands

    if competitive_intensity_band is not None:
        band = max(1, min(5, int(competitive_intensity_band)))
        card.competitive_intensity = band

    if (
        market_size_annual_revenue_usd is not None
        and avg_gross_margin_pct is not None
        and growth_cagr_pct is not None
    ):
        ms = _rub.market_size_band(market_size_annual_revenue_usd)
        pr = _rub.profitability_band(avg_gross_margin_pct)
        gr = _rub.growth_band(growth_cagr_pct)
        card.market_opportunity = MarketOpportunity(ms, pr, gr)
        detail["market_size_band"] = ms
        detail["profitability_band"] = pr
        detail["growth_band"] = gr

    has_exit = any(
        [
            exit_12m_max_ma_usd,
            exit_12m_max_ipo_usd,
            exit_3y_max_ma_usd,
            exit_3y_max_ipo_usd,
        ]
    )
    if has_exit:
        b12 = _rub.exit_intensity_band(exit_12m_max_ma_usd, exit_12m_max_ipo_usd)
        b3y = _rub.exit_intensity_band(exit_3y_max_ma_usd, exit_3y_max_ipo_usd)
        card.exit_intensity = average([float(b12), float(b3y)])
        detail["exit_band_12m"] = b12
        detail["exit_band_3y"] = b3y

    return {
        "score_lines": card.summary_lines(),
        "detail": detail,
    }


# --------------------------------------------------------------------------
# Discovery / scraping
# --------------------------------------------------------------------------

@mcp.tool()
async def web_search(
    query: str,
    sector: str | None = None,
    max_results: int = 8,
    recency_days: int | None = None,
    restrict_to_sources: bool = False,
    news: bool = False,
) -> dict[str, Any]:
    """Tavily web search.

    Set ``sector`` + ``restrict_to_sources=True`` to confine results to that
    sector's curated source domains. ``recency_days`` controls the recency
    filter: leave it as ``None`` to default to the configured lookback window
    (SECTOR_RESEARCH_LOOKBACK_MONTHS, default 2 months); pass ``0`` to disable
    recency filtering for time-insensitive sources (e.g. market-size reports).
    The recency filter is applied by Tavily on the news topic, so a window is
    auto-promoted to ``news`` unless you explicitly searched general.
    """
    include = None
    if restrict_to_sources and sector:
        include = get_sector(sector).source_domains

    if recency_days is None:
        effective_days: int | None = config.lookback_days()
    elif recency_days <= 0:
        effective_days = None
    else:
        effective_days = recency_days

    topic = "news" if (news or effective_days is not None) else "general"
    return await tavily.search(
        query,
        max_results=max_results,
        include_domains=include,
        days=effective_days,
        topic=topic,
    )


@mcp.tool()
async def extract_url(urls: list[str]) -> dict[str, Any]:
    """Extract cleaned full-text content from up to 20 URLs via Tavily."""
    return await tavily.extract(urls)


# --------------------------------------------------------------------------
# SEC EDGAR (free)
# --------------------------------------------------------------------------

@mcp.tool()
async def sec_recent_filings(
    ticker: str, forms: list[str] | None = None, limit: int = 15
) -> dict[str, Any]:
    """Recent SEC filings for a ticker/CIK, optionally filtered (e.g. ['10-K'])."""
    return await sec_edgar.recent_filings(ticker, forms=forms, limit=limit)


@mcp.tool()
async def sec_company_concept(
    ticker: str, concept: str = "Revenues", taxonomy: str = "us-gaap"
) -> dict[str, Any]:
    """Recent XBRL values for one concept (e.g. Revenues, GrossProfit)."""
    return await sec_edgar.company_concept(ticker, concept=concept, taxonomy=taxonomy)


@mcp.tool()
async def sec_full_text_search(query: str, forms: str | None = None) -> dict[str, Any]:
    """EDGAR full-text search across filings."""
    return await sec_edgar.full_text_search(query, forms=forms)


# --------------------------------------------------------------------------
# Crypto / digital-asset data
# --------------------------------------------------------------------------

@mcp.tool()
async def messari_asset(slug: str, kind: str = "metrics") -> dict[str, Any]:
    """Messari asset data. kind='metrics' (market data) or 'profile' (qualitative)."""
    if kind == "profile":
        return await messari.asset_profile(slug)
    return await messari.asset_metrics(slug)


@mcp.tool()
async def amberdata_request(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call any Amberdata REST endpoint (path after the host)."""
    return await amberdata.get(path, params=params)


@mcp.tool()
async def amberdata_spot_price(symbol: str) -> dict[str, Any]:
    """Latest Amberdata spot price for a pair (e.g. 'usdc_usd')."""
    return await amberdata.spot_price(symbol)


@mcp.tool()
async def defillama_stablecoins(top: int = 25) -> dict[str, Any]:
    """Keyless DefiLlama: top stablecoins by circulating supply (USD)."""
    return await defillama.stablecoins(top=top)


@mcp.tool()
async def defillama_stablecoin_detail(pegged_id: str) -> dict[str, Any]:
    """Keyless DefiLlama: per-chain breakdown/history for one stablecoin id."""
    return await defillama.stablecoin_detail(pegged_id)


@mcp.tool()
async def coingecko_markets(ids: list[str]) -> dict[str, Any]:
    """Keyless CoinGecko market snapshot for coin ids (e.g. ['usd-coin'])."""
    return await coingecko.markets(ids)


# --------------------------------------------------------------------------
# Rendering / status
# --------------------------------------------------------------------------

@mcp.tool()
def render_report(
    sector: str,
    markdown_body: str,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    """Write the completed memo and return the paths produced.

    ``formats`` selects deliverables from {"markdown", "docx", "pdf"} and
    defaults to ["markdown", "docx"] — Word is the primary document output.
    The title line is enforced to exactly
    "Standardized Sector Market Map <short_name>"; if ``markdown_body`` does not
    already begin with that H1, it is prepended.
    """
    s = get_sector(sector)
    title = report_title(s)
    body = markdown_body.strip()
    if not body.startswith(f"# {title}"):
        body = f"# {title}\n\n{body}"

    wanted = [f.lower() for f in (formats or ["markdown", "docx"])]
    unknown = [f for f in wanted if f not in {"markdown", "docx", "pdf"}]
    if unknown:
        return {"ok": False, "error": f"Unknown formats: {unknown}"}

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = report_basename(s)
    result: dict[str, Any] = {
        "sector": s.key,
        "title": title,
        "bytes_markdown": len(body.encode("utf-8")),
        "outputs": {},
    }

    if "markdown" in wanted:
        md_path = config.OUTPUT_DIR / f"{base}.md"
        md_path.write_text(body, encoding="utf-8")
        result["outputs"]["markdown"] = {"path": str(md_path)}

    if "docx" in wanted:
        docx_info = render_markdown_to_docx(body, config.OUTPUT_DIR / f"{base}.docx")
        result["outputs"]["docx"] = {
            "path": docx_info["path"],
            "engine": docx_info["engine"],
            "note": docx_info.get("note"),
        }

    if "pdf" in wanted:
        pdf_info = render_markdown_to_pdf(body, config.OUTPUT_DIR / f"{base}.pdf")
        result["outputs"]["pdf"] = {
            "path": pdf_info["path"],
            "engine": pdf_info["engine"],
            "note": pdf_info.get("note"),
        }

    return result


@mcp.tool()
def server_status() -> dict[str, Any]:
    """Report which API credentials are configured and the output directory."""
    fw = funding_windows()
    ew = exit_windows()
    return {
        "version": __import__("sector_research_mcp").__version__,
        "today": date.today().isoformat(),
        "output_dir": str(config.OUTPUT_DIR),
        "key_status": config.key_status(),
        "sectors": list_sector_keys(),
        "lookback_months": config.LOOKBACK_MONTHS,
        "windows": {
            "funding": [w["range"] for w in fw],
            "exit": [w["range"] for w in ew],
        },
    }


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------

@mcp.prompt(title="Standardized Sector Market Map")
def sector_market_map(sector: str) -> str:
    """A ready-to-run brief that drives a full standardized memo for a sector."""
    s = get_sector(sector)
    instructions = build_instructions(s)
    skeleton = build_skeleton(s)
    return (
        f"You are producing a standardized sector market-map memo titled exactly "
        f'"{report_title(s)}".\n\n'
        "Follow this methodology precisely. Use the MCP tools on this server to "
        "gather source-traceable data: get_sector_profile, web_search / "
        "extract_url (Tavily), sec_recent_filings / sec_company_concept "
        "(SEC EDGAR), messari_asset, amberdata_request, defillama_stablecoins, "
        "coingecko_markets. Compute all rubric scores with compute_scores. When "
        "the memo is complete, call render_report(sector, markdown_body) to emit "
        "the Word (.docx) + Markdown deliverables.\n\n"
        "Never estimate beyond disclosed data; if a window has no disclosed "
        "activity, say so explicitly.\n\n"
        "=== METHODOLOGY ===\n"
        f"{instructions}\n\n"
        "=== FILL THIS SKELETON ===\n"
        f"{skeleton}"
    )


def get_server() -> FastMCP:
    return mcp
