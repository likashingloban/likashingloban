"""Analysis-window helpers.

All reporting windows derive from ``config.LOOKBACK_MONTHS`` (default 2). The
methodology keeps a two-horizon structure: a primary window of N months and a
wider comparison window (2N for funding, 3N for exits), preserving the original
design's ratios while letting the whole memo be retargeted from one setting.
"""

from __future__ import annotations

import calendar
from datetime import date

from . import config


def months_ago(anchor: date, months: int) -> date:
    """Return the date ``months`` calendar months before ``anchor`` (day-clamped)."""
    total = (anchor.year * 12 + (anchor.month - 1)) - months
    year, month = divmod(total, 12)
    month += 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _window(anchor: date, months: int) -> dict[str, str]:
    start = months_ago(anchor, months)
    label = f"last {months} months" if months != 12 else "last 12 months"
    return {
        "label": label,
        "months": months,
        "start": start.isoformat(),
        "end": anchor.isoformat(),
        "range": f"{start.isoformat()} -> {anchor.isoformat()}",
    }


def funding_windows(as_of: date | None = None) -> list[dict[str, str]]:
    """Primary (N months) and comparison (2N months) funding windows."""
    anchor = as_of or date.today()
    n = config.LOOKBACK_MONTHS
    return [_window(anchor, n), _window(anchor, 2 * n)]


def exit_windows(as_of: date | None = None) -> list[dict[str, str]]:
    """Primary (N months) and comparison (3N months) exit windows."""
    anchor = as_of or date.today()
    n = config.LOOKBACK_MONTHS
    return [_window(anchor, n), _window(anchor, 3 * n)]
