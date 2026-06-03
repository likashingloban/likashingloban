"""Runtime configuration sourced from environment variables.

Nothing here raises on import. Missing API keys are reported per-tool at call
time so the MCP server always starts cleanly.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load a local .env (if present) before reading any variables, so a project
# .env file "just works" without exporting vars or passing -e flags. Real
# environment variables always take precedence (override=False). Missing
# python-dotenv or missing .env is a no-op.
try:
    from dotenv import find_dotenv, load_dotenv

    _dotenv = find_dotenv(usecwd=True)
    if not _dotenv:
        # Fall back to a .env sitting at the package/project root.
        _candidate = Path(__file__).resolve().parents[2] / ".env"
        _dotenv = str(_candidate) if _candidate.exists() else ""
    if _dotenv:
        load_dotenv(_dotenv, override=False)
except ImportError:  # python-dotenv not installed — rely on the real environment
    pass


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


TAVILY_API_KEY = _clean(os.getenv("TAVILY_API_KEY"))
MESSARI_API_KEY = _clean(os.getenv("MESSARI_API_KEY"))
AMBERDATA_API_KEY = _clean(os.getenv("AMBERDATA_API_KEY"))
COINGECKO_API_KEY = _clean(os.getenv("COINGECKO_API_KEY"))

SEC_EDGAR_USER_AGENT = (
    _clean(os.getenv("SEC_EDGAR_USER_AGENT"))
    or "sector-research-mcp (contact: set SEC_EDGAR_USER_AGENT)"
)

DEFAULT_OUTPUT_DIR = Path.cwd() / "reports"
OUTPUT_DIR = Path(
    _clean(os.getenv("SECTOR_RESEARCH_OUTPUT_DIR")) or DEFAULT_OUTPUT_DIR
).expanduser()

# Network defaults.
HTTP_TIMEOUT_SECONDS = float(os.getenv("SECTOR_RESEARCH_HTTP_TIMEOUT", "30"))

# Core analysis window. Every window in the methodology (funding, exits) is
# derived from this, so the whole memo can be retargeted by changing one value.
# Defaults to 2 months.
LOOKBACK_MONTHS = max(1, int(os.getenv("SECTOR_RESEARCH_LOOKBACK_MONTHS", "2")))


def lookback_days() -> int:
    """Approximate the lookback window in days (for search recency filters)."""
    return LOOKBACK_MONTHS * 31


def key_status() -> dict[str, bool]:
    """Boolean availability map for each configured credential (no secrets)."""
    return {
        "tavily": TAVILY_API_KEY is not None,
        "messari": MESSARI_API_KEY is not None,
        "amberdata": AMBERDATA_API_KEY is not None,
        "coingecko": COINGECKO_API_KEY is not None,
        "sec_edgar": "set SEC_EDGAR_USER_AGENT" not in SEC_EDGAR_USER_AGENT,
        "defillama": True,  # keyless
    }
