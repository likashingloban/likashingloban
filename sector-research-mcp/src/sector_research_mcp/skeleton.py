"""Generate the Markdown skeleton for a sector memo.

The skeleton encodes the required section order, the mandatory tables, and the
exact score lines. The model fills the bracketed placeholders with
source-backed content; the structure is fixed so every sector memo is directly
comparable.
"""

from __future__ import annotations

from datetime import date

from .sectors import Sector

TITLE_PREFIX = "Standardized Sector Market Map"


def report_title(sector: Sector) -> str:
    return f"{TITLE_PREFIX} {sector.short_name}"


def report_basename(sector: Sector) -> str:
    """Filesystem-safe base name shared by the .md and .pdf outputs."""
    safe = (
        sector.short_name.lower()
        .replace("&", "and")
        .replace(" ", "-")
        .replace("/", "-")
    )
    safe = "".join(ch for ch in safe if ch.isalnum() or ch == "-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return f"standardized-sector-market-map-{safe.strip('-')}"


def build_skeleton(sector: Sector, *, as_of: date | None = None) -> str:
    as_of = as_of or date.today()
    title = report_title(sector)
    lines = [
        f"# {title}",
        "",
        f"*Memo date: {as_of.isoformat()}. Tone: neutral, analytical, VC-style. "
        "All figures source-traceable; no estimates beyond disclosed data.*",
        "",
        f"**Sector definition.** {sector.definition}",
        "",
        "**Scope guardrails.** In scope: "
        + "; ".join(sector.in_scope)
        + ". Out of scope (no double-counting): "
        + "; ".join(sector.out_of_scope)
        + ".",
        "",
        "---",
        "",
        "## 1. Funding",
        "",
        "### 1a. Last 12 months "
        f"(window: {as_of.replace(year=as_of.year - 1).isoformat()} -> {as_of.isoformat()})",
        "",
        "_Headline:_ [aggregate disclosed funding, or \"No material funding rounds "
        "were publicly disclosed within this period.\"]. _YoY change:_ [...]. "
        "_Primary vs secondary:_ [...]. _Geography (US / EMEA / SEA / RoW):_ [...].",
        "",
        "| Company | Round size | Stage | Valuation | Equity/Debt mix | Date | Purpose |",
        "|---|---|---|---|---|---|---|",
        "| [company] | [$] | [stage] | [val or n/d] | [flag] | [date] | [purpose] |",
        "",
        "Source: [plain-text URL per row, on its own line]",
        "",
        "### 1b. Last 24 months "
        f"(window: {as_of.replace(year=as_of.year - 2).isoformat()} -> {as_of.isoformat()})",
        "",
        "_Headline / YoY / primary-secondary / geography:_ [...]. Recap table as above.",
        "",
        "**Funding Intensity Score: [X] / 5**  _(average rubric band over the last 3 years)_",
        "",
        "---",
        "",
        "## 2. Competitive Landscape",
        "",
        "[2-6 sentence structural summary derived from the cluster tables below.]",
        "",
        "### Cluster [N]: [name]",
        "",
        "| Row \\ Company | [Company A] | [Company B] | [Company C] |",
        "|---|---|---|---|",
        "| Company Overview | | | |",
        "| Product & Services | | | |",
        "| Moat | | | |",
        "| Target Clients | | | |",
        "| Client Key Metrics | | | |",
        "| Key Risks | | | |",
        "| References | | | |",
        "",
        "_Sub-segmentation (product offering x geography), with aggregate funding per sub-segment:_",
        "",
        "| Sub-segment | Geography | Companies | Aggregate funding |",
        "|---|---|---|---|",
        "| [offering] | [geo] | [list] | [$] |",
        "",
        "**Competitive Intensity Score: [X] / 5**",
        "",
        "---",
        "",
        "## 3. Market Opportunity",
        "",
        "**3a. Market size.** _Headline current annual revenue:_ [$]. _Source & tier:_ "
        "[...]. _URL:_ [...].",
        "",
        "**Market Size Score: [X] / 5**",
        "",
        "**3b. Profitability.** _Average gross margin:_ [%]. _Source & tier:_ [...]. "
        "_URL:_ [...].",
        "",
        "**Profitability Metrics Score: [X] / 5**",
        "",
        "**3c. Market expansion.** _Headline CAGR:_ [%] over [timeframe], broken down by "
        "geography (US/EMEA/SEA) and/or segment where possible. _Source:_ [...].",
        "",
        "**Growth Score: [X] / 5**",
        "",
        "**Market Opportunity Score = (Market Size + Profitability + Growth) / 3 = [X] / 5**",
        "",
        "---",
        "",
        "## 4. Exit Opportunities",
        "",
        "### 4a. Last 12 months",
        "",
        "[If none: \"No material M&A or IPO activity occurred in this window.\"]",
        "",
        "_M&A:_",
        "",
        "| Target | Acquirer | Deal value | Deal date | Latest pre-deal valuation | "
        "Valuation date | Source URL |",
        "|---|---|---|---|---|---|---|",
        "",
        "_IPO:_",
        "",
        "| Target | Indicated price range | First-day close | Most recent price | IPO date | "
        "# comps > $10B | Comp tickers | Source URL |",
        "|---|---|---|---|---|---|---|---|",
        "",
        "### 4b. Last 3 years",
        "",
        "[Repeat M&A and IPO tables for the 3-year window.]",
        "",
        "### Public comparables (NYSE / NASDAQ / LSEG / ADX / HKEX / SSE)",
        "",
        "| Company | Ticker | Market Cap | P/E | Gross Margin | Net Margin | Growth Rate | Data date |",
        "|---|---|---|---|---|---|---|---|",
        "",
        "**Exit Intensity Score = [X] / 5**  _(average of 12-month and 3-year bands)_",
        "",
        "---",
        "",
        "## 5. Legal & Regulatory Analysis",
        "",
        "| | US | EMEA | SEA |",
        "|---|---|---|---|",
        "| Regulations / frameworks / licenses / charters | | | |",
        "| Latest developments (updates, pilots, filings/grants) | | | |",
        "| Recent lawsuits | | | |",
        "| Recent patents | | | |",
        "",
        "_Favored use-cases by jurisdiction:_ [discussion].",
        "",
        "---",
        "",
        "## 6. Tech Stack Analysis",
        "",
        "[Open- vs closed-source; dominant stablecoins; dominant blockchain protocols; "
        "dominant open-source projects; recent innovations in smart-contract standards, "
        "hardware, algorithms, data sharing, and security.]",
        "",
        "---",
        "",
        "## 7. References",
        "",
        "[Every URL and every source-document filename used, in full.]",
        "",
    ]
    return "\n".join(lines)
