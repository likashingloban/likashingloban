from pathlib import Path

import pytest

from sector_research_mcp import skeleton
from sector_research_mcp.methodology import build_instructions
from sector_research_mcp.pdf import render_markdown_to_pdf
from sector_research_mcp.sectors import SECTORS, get_sector, list_sector_keys


def test_four_sectors_present():
    keys = list_sector_keys()
    assert set(keys) == {
        "stablecoin-payments",
        "ai-infrastructure",
        "ai-consumer",
        "market-infrastructure",
    }


@pytest.mark.parametrize("alias,expected", [
    ("stablecoin", "stablecoin-payments"),
    ("payments", "stablecoin-payments"),
    ("ai-infra", "ai-infrastructure"),
    ("consumer", "ai-consumer"),
    ("market-infrastructures", "market-infrastructure"),
])
def test_aliases_resolve(alias, expected):
    assert get_sector(alias).key == expected


def test_unknown_sector_raises():
    with pytest.raises(KeyError):
        get_sector("crypto-gaming")


@pytest.mark.parametrize("key", list(SECTORS))
def test_title_and_basename(key):
    s = get_sector(key)
    title = skeleton.report_title(s)
    assert title.startswith("Standardized Sector Market Map ")
    assert s.short_name in title
    base = skeleton.report_basename(s)
    assert base.startswith("standardized-sector-market-map-")
    assert " " not in base


@pytest.mark.parametrize("key", list(SECTORS))
def test_skeleton_has_required_sections(key):
    s = get_sector(key)
    md = skeleton.build_skeleton(s)
    for heading in [
        "## 1. Funding",
        "## 2. Competitive Landscape",
        "## 3. Market Opportunity",
        "## 4. Exit Opportunities",
        "## 5. Legal & Regulatory Analysis",
        "## 6. Tech Stack Analysis",
        "## 7. References",
    ]:
        assert heading in md
    for score in [
        "Funding Intensity Score",
        "Competitive Intensity Score",
        "Market Opportunity Score",
        "Exit Intensity Score",
    ]:
        assert score in md


@pytest.mark.parametrize("key", list(SECTORS))
def test_instructions_mention_windows_and_rubrics(key):
    text = build_instructions(get_sector(key))
    assert "last twelve months" in text.lower()
    assert "24 month" in text.lower() or "24-month" in text.lower()
    assert "Funding Intensity Rubric" in text


def test_render_pdf(tmp_path: Path):
    s = get_sector("stablecoin-payments")
    md = skeleton.build_skeleton(s)
    out = tmp_path / "memo.pdf"
    info = render_markdown_to_pdf(md, out)
    assert out.exists()
    assert out.stat().st_size > 1000
    assert info["engine"] in {"xhtml2pdf", "fpdf2"}
