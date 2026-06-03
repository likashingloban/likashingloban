from pathlib import Path

import pytest

from sector_research_mcp import skeleton
from sector_research_mcp.docx_render import render_markdown_to_docx
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
def test_instructions_reflect_lookback_window(key):
    # Default lookback is 2 months -> primary 2m, funding compare 4m, exit 6m.
    text = build_instructions(get_sector(key))
    assert "last 2 months" in text
    assert "4-month" in text  # funding comparison window (2N)
    assert "6 months" in text  # exit comparison window (3N)
    assert "Funding Intensity Rubric" in text
    assert "last twelve months" not in text.lower()


def test_render_pdf(tmp_path: Path):
    s = get_sector("stablecoin-payments")
    md = skeleton.build_skeleton(s)
    out = tmp_path / "memo.pdf"
    info = render_markdown_to_pdf(md, out)
    assert out.exists()
    assert out.stat().st_size > 1000
    assert info["engine"] in {"xhtml2pdf", "fpdf2"}


def test_render_docx(tmp_path: Path):
    s = get_sector("ai-infrastructure")
    md = skeleton.build_skeleton(s)
    out = tmp_path / "memo.docx"
    info = render_markdown_to_docx(md, out)
    assert out.exists()
    assert out.stat().st_size > 1000
    assert info["engine"] in {"htmldocx", "python-docx"}
    # the .docx must contain the section tables
    from docx import Document

    doc = Document(str(out))
    assert len(doc.tables) >= 1


def test_render_report_defaults_to_docx_only(tmp_path: Path, monkeypatch):
    import sector_research_mcp.config as cfg
    from sector_research_mcp.server import render_report

    monkeypatch.setattr(cfg, "OUTPUT_DIR", tmp_path)
    res = render_report("stablecoin", "## 1. Funding\n\nNo material rounds.\n")
    # Word only by default — no PDF, no Markdown.
    assert set(res["outputs"]) == {"docx"}
    assert Path(res["outputs"]["docx"]["path"]).exists()
    assert res["title"] == "Standardized Sector Market Map Stablecoins & Payment Rails"


def test_render_reports_batch_all_sectors(tmp_path: Path, monkeypatch):
    import sector_research_mcp.config as cfg
    from sector_research_mcp.sectors import list_sector_keys
    from sector_research_mcp.server import render_reports

    monkeypatch.setattr(cfg, "OUTPUT_DIR", tmp_path)
    reports = [
        {"sector": k, "markdown_body": "## 1. Funding\n\nNo material rounds.\n"}
        for k in list_sector_keys()
    ]
    res = render_reports(reports)
    assert res["rendered"] == 4 and res["failed"] == 0
    for r in res["results"]:
        assert set(r["outputs"]) == {"docx"}
        assert Path(r["outputs"]["docx"]["path"]).exists()
    # all four distinct .docx files written
    assert len(list(tmp_path.glob("*.docx"))) == 4


def test_render_reports_reports_per_item_errors(tmp_path: Path, monkeypatch):
    import sector_research_mcp.config as cfg
    from sector_research_mcp.server import render_reports

    monkeypatch.setattr(cfg, "OUTPUT_DIR", tmp_path)
    res = render_reports(
        [
            {"sector": "stablecoin", "markdown_body": "## x\n"},
            {"sector": "not-a-sector", "markdown_body": "## x\n"},
            {"sector": "ai-consumer"},  # missing body
        ]
    )
    assert res["rendered"] == 1
    assert res["failed"] == 2
