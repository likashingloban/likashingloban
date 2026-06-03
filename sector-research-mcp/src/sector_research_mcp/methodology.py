"""The standardized analytical methodology, surfaced as text to the model.

This is the single source of truth for *how* a memo must be produced. It is
exposed both as an MCP prompt and via the ``get_research_instructions`` tool so
the calling model always works from the same rubric-anchored brief.
"""

from __future__ import annotations

from . import config
from .rubrics import ALL_RUBRICS
from .sectors import Sector

OBJECTIVE = """OBJECTIVE
Provide a structured, directly comparable sector-level view across verticals
using consistent definitions, time horizons, scoring rubrics, and a
data-source hierarchy."""


def timeframe_text() -> str:
    n = config.LOOKBACK_MONTHS
    return f"""CORE TIMEFRAME REQUIREMENTS
- All analysis reflects the last {n} months, including the funding window and
  exit window, unless a section specifies otherwise (Funding also runs a
  {2 * n}-month comparison view; Exit Opportunities also runs a {3 * n}-month view).
- Use ONLY data and transactions dated within the stated window. Do not use
  anything older than the last {n} months for the primary analysis.
- If no material funding or exits were publicly disclosed within a window,
  state that explicitly. Do NOT estimate or extrapolate.
- Today's date anchors every window; state the exact window dates you used."""

GENERAL_REQUIREMENTS = """GENERAL ANALYTICAL REQUIREMENTS
- Market size = current annual revenue (NOT TAM unless explicitly labeled TAM).
- Avoid double-counting adjacent verticals (respect the sector scope boundaries).
- Every material number must be traceable to a source that clearly displays it.
- Do not assume spreads, take rates, or margins unless source-backed.
- Neutral, analytical, VC-style tone. No hype. No narrative framing.
- Direct plain-text URLs only. For any uploaded source document, give its title.
- Output must read cleanly as a standalone memo."""

DATA_SOURCE_HIERARCHY = """DATA SOURCES (in rough priority order)
Tier 1 — primary/regulatory: SEC 10-K/10-Q/8-K, central-bank reports.
Tier 2 — premium research: The Business Research Company, Grand View Research,
  Allied Market Research, BCG, McKinsey, Oliver Wyman, Gartner, Forrester,
  Accenture, Bain; equity-analyst / macro / wealth-management reports.
Tier 3 — aggregate public disclosure: PR Newswire / Business Wire, corporate
  sites and verified social accounts, major tech/finance media (The Information,
  TechCrunch, WSJ, NYT, The Guardian, The Economist, Messari, Politico,
  Bloomberg, Thomson Reuters, pymnts.com, CB Insights, PitchBook, Crunchbase,
  runtime.news, citriniresearch), accelerator sites (YC / Techstars / Skydeck),
  and verified (checkmarked) X profiles.
APIs available in this server: Tavily (search/extract), Messari, Amberdata,
  SEC EDGAR (free), DefiLlama (free), CoinGecko (free).
Additional free APIs worth adding: FRED (macro), Frankfurter/ECB (FX),
  Financial Modeling Prep + Alpha Vantage (free tiers, equity fundamentals),
  rwa.xyz (tokenized assets), GLEIF LEI (entity resolution)."""

def _funding_section() -> str:
    n = config.LOOKBACK_MONTHS
    return f"""1. FUNDING
   Run TWO analyses with recaps: last {n} months AND last {2 * n} months. State
   each window explicitly.
   - Headline funding: aggregate figure, or state "No material funding rounds
     were publicly disclosed within this period." if you cannot find disclosed
     rounds summing above $100M combined. Give the change vs the prior equal-
     length period. Split headline into primary vs secondary if possible. Split
     by geography (US, EMEA, SEA, Rest of the World) if possible.
   - If funding exists, recap in a table: Company | Round size | Stage |
     Valuation (if disclosed) | Equity/Debt mix flag | Date | Brief purpose,
     with the Source URL on its own line beneath each row.
   - Do not estimate funding ranges without disclosed rounds.
   - Apply the Funding Intensity Rubric and end with:
     "Funding Intensity Score: X / 5" where X = the average rubric band across
     the windows analyzed (primary {n}-month and {2 * n}-month comparison)."""


def _exit_section() -> str:
    n = config.LOOKBACK_MONTHS
    return f"""4. EXIT OPPORTUNITIES
   State windows: last {n} months AND last {3 * n} months; run the analysis for both.
   - If no material M&A/IPO, state it explicitly.
   - M&A table: Target | Acquirer | Deal value | Deal date | Latest known
     target valuation prior to M&A | Date of that valuation | Source URL.
   - IPO table: Target | IPO indicated price range | first-day close price |
     most recent share price | IPO date | # of public comparables with market
     cap > $10B as of latest date | tickers of those comparables | Source URL.
   - Only strictly in-sector exits (not partially related).
   - Separately, public comparables on NYSE/NASDAQ/LSEG/ADX/HKEX/SSE:
     Company | Ticker | Market Cap | P/E | Gross Margin | Net Margin |
     Growth Rate | Data date.
   - Apply Exit Intensity Rubric to each window; the printed score is the
     average of the two windows' bands:
     "Exit Intensity Score = X / 5"."""


_STRUCTURE_INTRO = "REQUIRED OUTPUT STRUCTURE (in this exact order)"

_STRUCTURE_MIDDLE = """2. COMPETITIVE LANDSCAPE
   - 2-6 sentence structural summary derived from the tables below.
   - Group every discovered company into clusters by product similarity.
   - For each cluster, ONE table: columns = one per company; rows =
     Company Overview, Product & Services, Moat, Target Clients,
     Client Key Metrics, Key Risks, References. (Row content per the brief:
     founding year + funding/market cap; incumbent vs new entrant, public vs
     private; geo-focus; offering + monetization model + key partners; moat
     dimensions incl. specific regulators/licenses, patents, partnerships,
     capital raised, Gartner MQ inclusion; ICP and enterprise/mid-market/SMB/
     retail mix; revenue/growth/margins/ACV/client count/geo split/marquee
     clients; capital intensity, regulatory friction, tech risk, partner/client
     dependencies; >=1 reference link.)
   - In each cluster also add a sub-segmentation across product-offering and
     geography dimensions, with an aggregate funding amount per sub-segment.
   - Apply the Competitive Intensity Rubric and end with:
     "Competitive Intensity Score: X / 5".

3. MARKET OPPORTUNITY (three components)
   a) Market size: headline current annual revenue first, then source +
      methodology tier, then URL. Don't triangulate unless Tier 3 required.
      Apply Market Size Rubric -> "Market Size Score: X / 5".
   b) Profitability: average gross-profit-margin figure first, then source +
      tier, then URL. Apply Profitability Rubric -> "Profitability Metrics
      Score: X / 5".
   c) Market expansion: headline CAGR first, broken down by geography (US/EMEA/
      SEA) and/or segment (enterprise/mid-market/SMB/retail) if possible; state
      timeframe; cite source (same Tier-1 source if possible). Apply Growth
      Rubric -> "Growth Score: X / 5".
   End with: "Market Opportunity Score = (Market Size + Profitability + Growth)
   / 3"."""


_STRUCTURE_TAIL = """5. LEGAL & REGULATORY ANALYSIS
   One table: columns = US, EMEA, SEA; rows = (1) relevant regulations/
   frameworks/licenses/charters; (2) latest developments (updates, pilots,
   entities that filed/were granted a license/charter); (3) recent lawsuits;
   (4) recent patents. Then discuss which use-cases are favored/advantaged in
   each jurisdiction given the above.

6. TECH STACK ANALYSIS
   Open- vs closed-source; dominant stablecoins; dominant blockchain protocols;
   dominant open-source projects; recent innovations (smart-contract standards,
   hardware, algorithms, data sharing, security).

7. REFERENCES
   Every URL and every source-document filename used, listed in full.

FINAL DELIVERABLES
Produce the memo as a Word document (.docx) and Markdown, both titled exactly
"Standardized Sector Market Map <short_name>" (call render_report, whose
default formats are ["markdown", "docx"]; add "pdf" if a PDF is also wanted)."""


def output_structure_text() -> str:
    """Assemble the full output-structure brief with window-derived sections."""
    return "\n\n".join(
        [
            _STRUCTURE_INTRO,
            _funding_section(),
            _STRUCTURE_MIDDLE,
            _exit_section(),
            _STRUCTURE_TAIL,
        ]
    )


def _rubrics_block() -> str:
    return "SCORING RUBRICS (verbatim)\n\n" + "\n\n".join(ALL_RUBRICS.values())


def build_instructions(sector: Sector) -> str:
    """Assemble the full instruction brief for one sector."""
    scope_in = "\n".join(f"  - {x}" for x in sector.in_scope)
    scope_out = "\n".join(f"  - {x}" for x in sector.out_of_scope)
    seed_pub = ", ".join(sector.seed_public) or "(discover live)"
    seed_priv = ", ".join(sector.seed_private) or "(discover live)"
    apis = ", ".join(sector.specialized_apis) or "Tavily + SEC EDGAR"
    sector_block = f"""SECTOR UNDER ANALYSIS: {sector.name}
Title short-name (fills "*"): {sector.short_name}
Definition: {sector.definition}

IN SCOPE:
{scope_in}

OUT OF SCOPE (do not double-count):
{scope_out}

Seed companies (STARTING POINTS ONLY — expand via the Data Sources step):
  Public: {seed_pub}
  Private: {seed_priv}
Relevant tickers: {", ".join(sector.tickers) or "(discover live)"}
Specialized data sources to prioritize for this sector: {apis}"""

    return "\n\n".join(
        [
            OBJECTIVE,
            sector_block,
            timeframe_text(),
            GENERAL_REQUIREMENTS,
            DATA_SOURCE_HIERARCHY,
            _rubrics_block(),
            output_structure_text(),
        ]
    )
