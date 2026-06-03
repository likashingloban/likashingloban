"""Render a Markdown memo to PDF with graceful fallbacks.

Order of preference:
  1. markdown -> HTML -> PDF via xhtml2pdf (pure-python, good table support)
  2. fpdf2 plain-text fallback (always available)

Returns the path written plus which engine produced it, so the caller can
report honestly which renderer was used.
"""

from __future__ import annotations

from pathlib import Path

import markdown as md

_CSS = """
@page { size: A4; margin: 1.8cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.5pt; color: #111; }
h1 { font-size: 18pt; border-bottom: 2px solid #222; padding-bottom: 4px; }
h2 { font-size: 13pt; margin-top: 16px; border-bottom: 1px solid #ccc; }
h3 { font-size: 11pt; margin-top: 12px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8pt; }
th, td { border: 1px solid #bbb; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; }
code { background: #f5f5f5; padding: 1px 3px; font-size: 8pt; }
a { color: #1a4f8b; word-break: break-all; }
"""


def _render_xhtml2pdf(markdown_text: str, out_path: Path) -> bool:
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return False
    html_body = md.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )
    html = (
        f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head>"
        f"<body>{html_body}</body></html>"
    )
    with out_path.open("wb") as fh:
        result = pisa.CreatePDF(src=html, dest=fh, encoding="utf-8")
    return not result.err


def _render_fpdf(markdown_text: str, out_path: Path) -> bool:
    try:
        from fpdf import FPDF
    except ImportError:
        return False
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=9)
    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 15)
            pdf.multi_cell(0, 7, line[2:])
            pdf.set_font("Helvetica", size=9)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 6, line[3:])
            pdf.set_font("Helvetica", size=9)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 5, line[4:])
            pdf.set_font("Helvetica", size=9)
        else:
            # latin-1 safe encoding for the core fonts
            safe = line.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 4.6, safe or " ")
    pdf.output(str(out_path))
    return True


def render_markdown_to_pdf(markdown_text: str, out_path: Path) -> dict[str, str]:
    """Write ``markdown_text`` as a PDF at ``out_path``; report the engine used."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if _render_xhtml2pdf(markdown_text, out_path):
            return {"engine": "xhtml2pdf", "path": str(out_path)}
    except Exception as exc:  # noqa: BLE001 - fall through to text renderer
        last = str(exc)
    else:
        last = "xhtml2pdf reported an error"
    if _render_fpdf(markdown_text, out_path):
        return {"engine": "fpdf2", "path": str(out_path), "note": f"fallback ({last})"}
    raise RuntimeError(f"No PDF engine available; last error: {last}")
