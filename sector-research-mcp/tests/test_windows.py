"""Lookback-window derivation (default 2 months) and overrides."""

import importlib
from datetime import date

from sector_research_mcp import config, windows


def test_months_ago_basic():
    assert windows.months_ago(date(2026, 6, 3), 2) == date(2026, 4, 3)
    assert windows.months_ago(date(2026, 1, 15), 2) == date(2025, 11, 15)


def test_months_ago_day_clamp():
    # 31 Mar minus 1 month -> Feb has no 31st, clamp to 28 (2026 not a leap year).
    assert windows.months_ago(date(2026, 3, 31), 1) == date(2026, 2, 28)


def test_default_windows_are_two_months():
    fw = windows.funding_windows(date(2026, 6, 3))
    assert fw[0]["months"] == 2 and fw[0]["start"] == "2026-04-03"
    assert fw[1]["months"] == 4 and fw[1]["start"] == "2026-02-03"
    ew = windows.exit_windows(date(2026, 6, 3))
    assert ew[0]["months"] == 2
    assert ew[1]["months"] == 6 and ew[1]["start"] == "2025-12-03"


def test_lookback_days_default():
    assert config.lookback_days() == config.LOOKBACK_MONTHS * 31


def test_lookback_is_env_configurable(monkeypatch):
    monkeypatch.setenv("SECTOR_RESEARCH_LOOKBACK_MONTHS", "6")
    importlib.reload(config)
    try:
        fw = windows.funding_windows(date(2026, 6, 3))
        assert fw[0]["months"] == 6 and fw[1]["months"] == 12
    finally:
        monkeypatch.delenv("SECTOR_RESEARCH_LOOKBACK_MONTHS", raising=False)
        importlib.reload(config)
