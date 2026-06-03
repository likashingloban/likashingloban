"""Render a Markdown memo to a Word (.docx) document.

Order of preference:
  1. markdown -> HTML -> docx via htmldocx (keeps tables, headings, links)
  2. python-docx plain-text fallback (always available if python-docx is)

Returns the path written plus which engine produced it, so the caller can
report honestly which renderer was used.
"""

from __future__ import annotations

from pathlib import Path

import markdown as md


def _render_htmldocx(markdown_text: str, out_path: Path) -> bool:
    try:
        from docx import Document
        from htmldocx import HtmlToDocx
    except ImportError:
        return False
    # htmldocx emits a spurious BeautifulSoup warning on bare-URL lines.
    try:
        import warnings

        from bs4 import MarkupResemblesLocatorWarning

        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    except Exception:  # noqa: BLE001 - warning suppression is best-effort
        pass
    html = md.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    document = Document()
    document.core_properties.title = markdown_text.lstrip("# ").splitlines()[0][:255]
    HtmlToDocx().add_html_to_document(html, document)
    document.save(str(out_path))
    return True


def _render_plain(markdown_text: str, out_path: Path) -> bool:
    try:
        from docx import Document
    except ImportError:
        return False
    document = Document()
    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            document.add_heading(line[2:], level=0)
        elif line.startswith("## "):
            document.add_heading(line[3:], level=1)
        elif line.startswith("### "):
            document.add_heading(line[4:], level=2)
        elif line:
            document.add_paragraph(line)
    document.save(str(out_path))
    return True


def render_markdown_to_docx(markdown_text: str, out_path: Path) -> dict[str, str]:
    """Write ``markdown_text`` as a .docx at ``out_path``; report the engine used."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if _render_htmldocx(markdown_text, out_path):
            return {"engine": "htmldocx", "path": str(out_path)}
    except Exception as exc:  # noqa: BLE001 - fall through to plain renderer
        last = str(exc)
    else:
        last = "htmldocx unavailable"
    if _render_plain(markdown_text, out_path):
        return {"engine": "python-docx", "path": str(out_path), "note": f"fallback ({last})"}
    raise RuntimeError(f"No .docx engine available; last error: {last}")
