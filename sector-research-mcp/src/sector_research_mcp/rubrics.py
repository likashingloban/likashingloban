"""Scoring rubrics for the standardized sector memo.

Every rubric maps a source-backed numeric input to an integer band (1-5) using
the exact thresholds from the methodology. Keeping the math here makes scoring
deterministic and testable, instead of leaving it to free-form LLM arithmetic.

All monetary inputs are USD. All percentage inputs are whole-number percents
(e.g. 42.0 means 42%).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- Rubric reference text (verbatim, surfaced to the model) ----------------

FUNDING_INTENSITY_RUBRIC = """Funding Intensity Rubric (5 = highest funding):
1 - Minimal (<$100M)
2 - Light ($100M-500M)
3 - Moderate ($500M-1B)
4 - Strong ($1B-2B)
5 - Very Strong ($2B+)
Funding Intensity Score = average of the rubric band over the last 3 years."""

COMPETITIVE_INTENSITY_RUBRIC = """Competitive Intensity Rubric (1 = most competitive):
1 - Extremely competitive: many firms, no product moat, competing on price/niche.
2 - Highly competitive: many firms, low product moat, competing on distribution/self-service.
3 - Moderately competitive: several-to-many firms with product or commercialization moat; subsegments large enough to support very big businesses.
4 - Concentrated: high technology/product moat, a small number of firms own a majority of the market.
5 - Structurally protected: regulatory barriers including licenses and patents."""

MARKET_SIZE_RUBRIC = """Market Size Rubric (5 = largest), on current annual revenue:
1 - < $1B
2 - $1B-3B
3 - $3B-10B
4 - $10B-50B
5 - $50B+"""

PROFITABILITY_RUBRIC = """Profitability Metrics Rubric (5 = highest margin), on average gross margin:
1 - < 20%
2 - 20%-40%
3 - 40%-60%
4 - 60%-75%
5 - 75%+"""

GROWTH_RUBRIC = """Growth Rubric (5 = fastest growth), on CAGR:
1 - <5%
2 - 5-10%
3 - 10-20%
4 - 20-35%
5 - 35%+"""

EXIT_INTENSITY_RUBRIC = """Exit Intensity Rubric (1 = none):
1 - None
2 - Limited (<$200M M&A, no IPOs)
3 - Emerging ($200M-$500M M&A and/or $1B-$3B IPOs)
4 - Active ($500M-$1B M&A and $3B+ IPOs)
5 - Strong ($1B+ M&A and $10B+ IPOs)
Exit Intensity Score = average of the last-12-months and last-3-years bands."""

ALL_RUBRICS = {
    "funding_intensity": FUNDING_INTENSITY_RUBRIC,
    "competitive_intensity": COMPETITIVE_INTENSITY_RUBRIC,
    "market_size": MARKET_SIZE_RUBRIC,
    "profitability": PROFITABILITY_RUBRIC,
    "growth": GROWTH_RUBRIC,
    "exit_intensity": EXIT_INTENSITY_RUBRIC,
}

_MM = 1_000_000
_BB = 1_000_000_000


# --- Band functions ---------------------------------------------------------

def funding_intensity_band(amount_usd: float) -> int:
    """Aggregate disclosed funding (USD over one year) -> band 1-5."""
    if amount_usd < 100 * _MM:
        return 1
    if amount_usd < 500 * _MM:
        return 2
    if amount_usd < 1 * _BB:
        return 3
    if amount_usd < 2 * _BB:
        return 4
    return 5


def market_size_band(annual_revenue_usd: float) -> int:
    if annual_revenue_usd < 1 * _BB:
        return 1
    if annual_revenue_usd < 3 * _BB:
        return 2
    if annual_revenue_usd < 10 * _BB:
        return 3
    if annual_revenue_usd < 50 * _BB:
        return 4
    return 5


def profitability_band(gross_margin_pct: float) -> int:
    if gross_margin_pct < 20:
        return 1
    if gross_margin_pct < 40:
        return 2
    if gross_margin_pct < 60:
        return 3
    if gross_margin_pct < 75:
        return 4
    return 5


def growth_band(cagr_pct: float) -> int:
    if cagr_pct < 5:
        return 1
    if cagr_pct < 10:
        return 2
    if cagr_pct < 20:
        return 3
    if cagr_pct < 35:
        return 4
    return 5


def _ma_band(max_ma_usd: float) -> int:
    if max_ma_usd <= 0:
        return 1
    if max_ma_usd < 200 * _MM:
        return 2
    if max_ma_usd < 500 * _MM:
        return 3
    if max_ma_usd < 1 * _BB:
        return 4
    return 5


def _ipo_band(max_ipo_usd: float) -> int:
    if max_ipo_usd <= 0:
        return 1
    if max_ipo_usd < 3 * _BB:
        return 3  # $1B-3B IPO maps to the "Emerging" band
    if max_ipo_usd < 10 * _BB:
        return 4
    return 5


def exit_intensity_band(max_ma_usd: float, max_ipo_usd: float) -> int:
    """Combine the largest in-sector M&A and IPO into a single 1-5 band.

    The rubric mixes "and"/"and/or" language, so we score each channel against
    its own thresholds and take the stronger of the two. A pure-M&A market and
    a pure-IPO market are therefore both representable.
    """
    if max_ma_usd <= 0 and max_ipo_usd <= 0:
        return 1
    return max(_ma_band(max_ma_usd), _ipo_band(max_ipo_usd))


# --- Composite helpers ------------------------------------------------------

def average(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)


@dataclass
class MarketOpportunity:
    market_size_score: int
    profitability_score: int
    growth_score: int

    @property
    def composite(self) -> float:
        return round(
            (self.market_size_score + self.profitability_score + self.growth_score) / 3,
            2,
        )


@dataclass
class ScoreCard:
    """Container the server fills and renders into the memo's score lines."""

    funding_intensity: float | None = None
    competitive_intensity: int | None = None
    market_opportunity: MarketOpportunity | None = None
    exit_intensity: float | None = None
    notes: list[str] = field(default_factory=list)

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        if self.funding_intensity is not None:
            lines.append(f"Funding Intensity Score: {self.funding_intensity} / 5")
        if self.competitive_intensity is not None:
            lines.append(
                f"Competitive Intensity Score: {self.competitive_intensity} / 5"
            )
        if self.market_opportunity is not None:
            mo = self.market_opportunity
            lines.append(f"Market Size Score: {mo.market_size_score} / 5")
            lines.append(f"Profitability Metrics Score: {mo.profitability_score} / 5")
            lines.append(f"Growth Score: {mo.growth_score} / 5")
            lines.append(f"Market Opportunity Score = {mo.composite} / 5")
        if self.exit_intensity is not None:
            lines.append(f"Exit Intensity Score = {self.exit_intensity} / 5")
        return lines
