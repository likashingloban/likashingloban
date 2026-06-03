"""Runtime configuration sourced from environment variables.

Nothing here raises on import. Missing API keys are reported per-tool at call
time so the MCP server always starts cleanly.
"""

from __future__ import annotations

import os
from pathlib import Path


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
