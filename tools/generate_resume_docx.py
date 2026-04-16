#!/usr/bin/env python3
"""
Resume DOCX/PDF Generator — Builds a styled resume from markdown.
Matches resume_pretty.docx: dark navy/blue header table, light-blue summary
box with blue left border, ALL-CAPS blue section headings, 2-col skills table.

Usage:
  uv run python tools/generate_resume_docx.py --job-id <uuid>
  uv run python tools/generate_resume_docx.py --resume-path path/to/resume.md

Requires LibreOffice for PDF conversion:
  brew install --cask libreoffice
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ─── Colour palette ───────────────────────────────────────────────────────────

NAVY   = "1B3A5C"   # header left bg
BLUE   = "2E7EBF"   # header right bg + section headings + summary border
LBLUE  = "A8CCE8"   # subtitle in header
SUMMBG = "EAF3FA"   # summary box background
DARK   = "222222"   # body text
GREY   = "646464"   # dates / secondary


# ─── Markdown parser ──────────────────────────────────────────────────────────

def parse_resume_md(md_text: str) -> list[tuple[str, str]]:
    """
    Parse resume markdown into (block_type, content) tuples.

    Types: name, contact, section, role, bullet, hr, blank, paragraph
    """
    blocks: list[tuple[str, str]] = []
    seen_name = False
    seen_contact = False

    for raw in md_text.split("\n"):
        line = raw.rstrip()
        if not line:
            blocks.append(("blank", ""))
            continue

        if line.startswith("# "):
            t, content = "name", line[2:].strip()
            seen_name = True
        elif line.startswith("## "):
            t, content = "section", line[3:].strip()
        elif line.startswith("### "):
            t, content = "role", line[4:].strip()
        elif line.startswith("- ") or line.startswith("* "):
            t, content = "bullet", line[2:].strip()
        elif line.strip() in ("---", "***", "___"):
            t, content = "hr", ""
        elif seen_name and not seen_contact and not line.startswith("#"):
            t = "contact"
            content = re.sub(r"^\*\*Contact\*\*:\s*", "", line.strip())
            seen_contact = True
        elif re.match(r"^\*\*[^*].+\*\*$", line.strip()):
            t, content = "bold", line.strip()[2:-2]
        elif re.match(r"^\*[^*].+\*$", line.strip()):
            t, content = "italic", line.strip()[1:-1]
        else:
            t, content = "paragraph", line.strip()

        blocks.append((t, content))

    return blocks


def parse_role_line(text: str) -> tuple[str, str, str]:
    """Parse '### Company — Title | dates' → (title, company, dates)."""
    pipe_match = re.search(r"\s+\|\s+(.+)$", text)
    if pipe_match:
        dates = pipe_match.group(1).strip()
        remainder = text[: pipe_match.start()].strip()
    else:
        paren_match = re.search(r"\(([^()]+)\)\s*$", text)
        if paren_match:
            dates = paren_match.group(1).strip()
            remainder = text[: paren_match.start()].strip()
        else:
            dates, remainder = "", text

    for sep in (" \u2014 ", " \u2013 ", " — ", " – ", " - "):
        if sep in remainder:
            parts = remainder.split(sep, 1)
            return parts[1].strip(), parts[0].strip(), dates

    return remainder, "", dates


def parse_contact_items(contact_line: str) -> list[dict]:
    """Split 'email | phone | url' into [{'label': str, 'url': str|None}]."""
    items = []
    for part in contact_line.split(" | "):
        part = part.strip()
        m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
        if m:
            items.append({"label": m.group(1), "url": m.group(2)})
        else:
            items.append({"label": part, "url": None})
    return items


def _parse_inline_runs(text: str) -> list[dict]:
    """Parse **bold**, *italic*, [link](url) into run dicts."""
    runs = []
    pattern = re.compile(
        r"\*\*(.+?)\*\*|\*(.+?)\*|__(.+?)__|_(.+?)_|\[([^\]]+)\]\(([^)]+)\)"
    )
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            runs.append({"text": text[pos : m.start()], "bold": False, "italic": False, "url": None})
        if m.group(1):
            runs.append({"text": m.group(1), "bold": True,  "italic": False, "url": None})
        elif m.group(2):
            runs.append({"text": m.group(2), "bold": False, "italic": True,  "url": None})
        elif m.group(3):
            runs.append({"text": m.group(3), "bold": True,  "italic": False, "url": None})
        elif m.group(4):
            runs.append({"text": m.group(4), "bold": False, "italic": True,  "url": None})
        elif m.group(5):
            runs.append({"text": m.group(5), "bold": False, "italic": False, "url": m.group(6)})
        pos = m.end()
    if pos < len(text):
        runs.append({"text": text[pos:], "bold": False, "italic": False, "url": None})
    return runs or [{"text": text, "bold": False, "italic": False, "url": None}]


# ─── Low-level helpers ────────────────────────────────────────────────────────

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def _rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _font(run, size=None, bold=None, italic=None, color: str | None = None):
    run.font.name = "Calibri"
    if size   is not None: run.font.size  = Pt(size)
    if bold   is not None: run.font.bold  = bold
    if italic is not None: run.font.italic = italic
    if color  is not None: run.font.color.rgb = _rgb(color)


def _spacing(p, before=0, after=0, line=None):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if line is not None:
        pf.line_spacing = Pt(line)


def _shd(cell, fill: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"),  "clear")
    tcPr.append(shd)


def _cell_margins(cell, top=0, left=0, bottom=0, right=0):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("left", left), ("bottom", bottom), ("right", right)]:
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:type"), "dxa")
        e.set(qn("w:w"), str(val))
        tcMar.append(e)
    tcPr.append(tcMar)


def _no_cell_borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBdr = OxmlElement("w:tcBorders")
    for side in ["top", "left", "bottom", "right"]:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "none")
        tcBdr.append(b)
    tcPr.append(tcBdr)


def _get_or_add_tblPr(tbl_elem):
    tblPr = tbl_elem.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl_elem.insert(0, tblPr)
    return tblPr


def _no_tbl_borders(table):
    tblPr = _get_or_add_tblPr(table._tbl)
    tblBdr = OxmlElement("w:tblBorders")
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "none")
        tblBdr.append(b)
    tblPr.append(tblBdr)


def _valign(cell, val="center"):
    tcPr = cell._tc.get_or_add_tcPr()
    v = OxmlElement("w:vAlign")
    v.set(qn("w:val"), val)
    tcPr.append(v)


def _set_col_widths(table, widths: list[int]):
    """Set column widths in twips."""
    tbl = table._tbl
    tblGrid = tbl.find(qn("w:tblGrid"))
    if tblGrid is None:
        tblGrid = OxmlElement("w:tblGrid")
        tbl.append(tblGrid)
    for gc in tblGrid.findall(qn("w:gridCol")):
        tblGrid.remove(gc)
    for w in widths:
        gc = OxmlElement("w:gridCol")
        gc.set(qn("w:w"), str(w))
        tblGrid.append(gc)
    for cell, w in zip(table.rows[0].cells, widths):
        tcPr = cell._tc.get_or_add_tcPr()
        existing = tcPr.find(qn("w:tcW"))
        if existing is not None:
            tcPr.remove(existing)
        tcW = OxmlElement("w:tcW")
        tcW.set(qn("w:type"), "dxa")
        tcW.set(qn("w:w"), str(w))
        tcPr.append(tcW)


def _set_tbl_width(table, width: int):
    tblPr = _get_or_add_tblPr(table._tbl)
    existing = tblPr.find(qn("w:tblW"))
    if existing is not None:
        tblPr.remove(existing)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(width))
    tblPr.append(tblW)


def _inline_runs(para, text: str, size=9.5, color: str | None = None):
    """Add inline-markup-aware runs to a paragraph."""
    for rd in _parse_inline_runs(text):
        run = para.add_run(rd["text"])
        _font(run, size=size, bold=rd["bold"], italic=rd["italic"],
              color=color or DARK)


def _hrule(doc, color="BBBBBB"):
    p = doc.add_paragraph()
    _spacing(p, before=0, after=1)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


# ─── Section builders ─────────────────────────────────────────────────────────

def _header_table(doc, name: str, subtitle: str, contact_items: list[dict]):
    """Two-column dark header: navy left (name+title), blue right (contact)."""
    table = doc.add_table(rows=1, cols=2)
    _no_tbl_borders(table)
    _set_tbl_width(table, 10080)
    _set_col_widths(table, [7200, 2880])

    left = table.cell(0, 0)
    _shd(left, NAVY)
    _cell_margins(left, top=280, left=320, bottom=280, right=200)
    _valign(left, "center")
    _no_cell_borders(left)

    p = left.paragraphs[0]
    _spacing(p, before=0, after=3)
    _font(p.add_run(name), size=26, bold=True, color="FFFFFF")

    if subtitle:
        p2 = left.add_paragraph()
        _spacing(p2, before=0, after=0)
        _font(p2.add_run(subtitle), size=13, bold=False, color=LBLUE)

    right = table.cell(0, 1)
    _shd(right, BLUE)
    _cell_margins(right, top=280, left=200, bottom=280, right=200)
    _valign(right, "center")
    _no_cell_borders(right)

    first = True
    for item in contact_items:
        if not item["label"]:
            continue
        p = right.paragraphs[0] if first else right.add_paragraph()
        first = False
        _spacing(p, before=0, after=2)
        _font(p.add_run(item["label"]), size=9, color="FFFFFF")


def _summary_box(doc, text: str):
    """Full-width light-blue box with thick blue left border."""
    table = doc.add_table(rows=1, cols=1)
    _set_tbl_width(table, 10080)
    _set_col_widths(table, [10080])

    # Blue left border only
    tblPr = _get_or_add_tblPr(table._tbl)
    tblBdr = OxmlElement("w:tblBorders")
    for side in ["top", "bottom", "right", "insideH", "insideV"]:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "none")
        tblBdr.append(b)
    left_bdr = OxmlElement("w:left")
    left_bdr.set(qn("w:val"), "single")
    left_bdr.set(qn("w:color"), BLUE)
    left_bdr.set(qn("w:sz"), "24")
    tblBdr.append(left_bdr)
    tblPr.append(tblBdr)

    cell = table.cell(0, 0)
    _shd(cell, SUMMBG)
    _cell_margins(cell, top=120, left=240, bottom=120, right=240)
    _no_cell_borders(cell)

    p = cell.paragraphs[0]
    _spacing(p, before=0, after=0)
    _inline_runs(p, text, size=10, color=DARK)


def _section_heading(doc, text: str):
    p = doc.add_paragraph()
    _spacing(p, before=8, after=2)
    _font(p.add_run(text.upper()), size=11, bold=True, color=BLUE)
    _hrule(doc)


def _role_header(doc, title: str, company: str, dates: str):
    p = doc.add_paragraph()
    _spacing(p, before=6, after=1)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_ALIGN_PARAGRAPH.RIGHT)
    if company:
        _font(p.add_run(company), size=11, bold=True)
        _font(p.add_run("  |  "), size=11, bold=False)
    _font(p.add_run(title), size=11, italic=bool(company), bold=not bool(company))
    if dates:
        _font(p.add_run(f"\t{dates}"), size=9, color=GREY)


def _bullet(doc, text: str):
    p = doc.add_paragraph(style="List Bullet")
    _spacing(p, before=1, after=1, line=12)
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.first_line_indent = Inches(-0.15)
    _inline_runs(p, text, size=9.5)


def _skills_table(doc, pairs: list[tuple[str, str]]):
    """Two-column table: bold label | value."""
    table = doc.add_table(rows=len(pairs), cols=2)
    _no_tbl_borders(table)
    _set_tbl_width(table, 10080)

    col_widths = [2600, 7480]
    tbl = table._tbl
    tblGrid = tbl.find(qn("w:tblGrid"))
    if tblGrid is None:
        tblGrid = OxmlElement("w:tblGrid")
        tbl.append(tblGrid)
    for gc in tblGrid.findall(qn("w:gridCol")):
        tblGrid.remove(gc)
    for w in col_widths:
        gc = OxmlElement("w:gridCol")
        gc.set(qn("w:w"), str(w))
        tblGrid.append(gc)

    for i, (label, value) in enumerate(pairs):
        row = table.rows[i]
        for j, (cell, w) in enumerate(zip(row.cells, col_widths)):
            _no_cell_borders(cell)
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:type"), "dxa")
            tcW.set(qn("w:w"), str(w))
            tcPr.append(tcW)

        lp = row.cells[0].paragraphs[0]
        _spacing(lp, before=1, after=1)
        _font(lp.add_run(f"{label}:"), size=9.5, bold=True)

        vp = row.cells[1].paragraphs[0]
        _spacing(vp, before=1, after=1)
        _font(vp.add_run(value), size=9.5)


# ─── Main builder ─────────────────────────────────────────────────────────────

def markdown_to_docx(md_text: str, output_path: str) -> None:
    doc = Document()

    for section in doc.sections:
        section.top_margin    = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin   = Inches(0.75)
        section.right_margin  = Inches(0.75)

    doc.styles["Normal"].paragraph_format.space_after = Pt(0)

    blocks = parse_resume_md(md_text)

    # Extract header fields
    name         = next((c for t, c in blocks if t == "name"),    "")
    contact_raw  = next((c for t, c in blocks if t == "contact"), "")
    contact_items = parse_contact_items(contact_raw) if contact_raw else []
    first_role   = next((c for t, c in blocks if t == "role"),    None)
    subtitle     = parse_role_line(first_role)[0] if first_role else ""

    _header_table(doc, name, subtitle, contact_items)

    # Find where body starts (skip name/contact/blank/hr preamble)
    i = 0
    while i < len(blocks) and blocks[i][0] in ("name", "contact", "blank", "hr"):
        i += 1

    # Collect summary paragraph(s) before first section or role
    summary_parts: list[str] = []
    j = i
    while j < len(blocks) and blocks[j][0] in ("paragraph", "blank", "hr"):
        if blocks[j][0] == "paragraph":
            summary_parts.append(blocks[j][1])
        j += 1
    if summary_parts:
        _summary_box(doc, " ".join(summary_parts))
        i = j

    # Render body
    current_section = ""
    skill_pairs: list[tuple[str, str]] = []

    def flush_skills():
        if skill_pairs:
            _skills_table(doc, list(skill_pairs))
            skill_pairs.clear()

    while i < len(blocks):
        btype, content = blocks[i]
        i += 1

        if btype in ("blank", "hr"):
            continue

        if btype == "section":
            flush_skills()
            _section_heading(doc, content)
            current_section = content.lower()
            continue

        if btype == "role":
            flush_skills()
            title, company, dates = parse_role_line(content)
            _role_header(doc, title, company, dates)
            continue

        if btype == "bullet":
            if current_section == "skills":
                m = re.match(r"\*\*(.+?)\*\*:\s*(.*)", content)
                if m:
                    skill_pairs.append((m.group(1), m.group(2)))
                    continue
            flush_skills()
            _bullet(doc, content)
            continue

        if btype in ("paragraph", "bold", "italic"):
            flush_skills()
            p = doc.add_paragraph()
            _spacing(p, before=2, after=2)
            italic_override = btype == "italic"
            for rd in _parse_inline_runs(content):
                run = p.add_run(rd["text"])
                _font(run, size=9.5, bold=rd["bold"],
                      italic=rd["italic"] or italic_override)
            continue

    flush_skills()

    docx_out = output_path if output_path.endswith(".docx") else output_path.replace(".pdf", ".docx")
    doc.save(docx_out)
    print(f"✅ DOCX written to: {docx_out}")


# ─── PDF conversion ───────────────────────────────────────────────────────────

def docx_to_pdf(docx_path: str, output_dir: str) -> str:
    soffice = _find_soffice()
    if not soffice:
        print("❌ LibreOffice not found. Install with:")
        print("   brew install --cask libreoffice")
        sys.exit(1)
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"❌ LibreOffice conversion failed:\n{result.stderr}")
        sys.exit(1)
    pdf_path = str(Path(output_dir) / f"{Path(docx_path).stem}.pdf")
    print(f"✅ PDF written to: {pdf_path}")
    return pdf_path


def markdown_to_pdf(md_text: str, output_path: str) -> None:
    docx_path = output_path.replace(".pdf", ".docx")
    markdown_to_docx(md_text, docx_path)
    docx_to_pdf(docx_path, str(Path(output_path).parent))


def _find_soffice() -> str | None:
    for c in [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]:
        if Path(c).exists():
            return c
    result = subprocess.run(["which", "soffice"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


# ─── DB helpers ───────────────────────────────────────────────────────────────

def fetch_resume_md_from_db(job_id: str) -> tuple[str, str, str]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    app_res = sb.table("applications").select("resume_md").eq("job_id", job_id).execute()
    if not app_res.data or not app_res.data[0].get("resume_md"):
        print(f"❌ No resume_md found for job {job_id}. Run /generate first.")
        sys.exit(1)

    job_res = sb.table("jobs").select("title, companies(name)").eq("id", job_id).execute()
    if not job_res.data:
        print(f"❌ Job {job_id} not found.")
        sys.exit(1)

    job = job_res.data[0]
    company = (job.get("companies") or {}).get("name", "unknown")
    title   = job.get("title", "unknown")
    return app_res.data[0]["resume_md"], company, title


def _upload_artifact_to_storage(job_id: str, file_path: str, company: str, title: str) -> str | None:
    """Upload a generated artifact to Supabase Storage. Returns storage URL or None."""
    try:
        import re
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Build storage path: artifacts/applications/{job-slug}/{filename}
        slug = f"{company}-{title}".lower()
        slug = re.sub(r"[^a-z0-9-]", "-", slug)[:50].strip("-")
        filename = Path(file_path).name
        storage_path = f"applications/{slug}/{filename}"

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        sb.storage.from_("artifacts").upload(storage_path, file_bytes)
        # Return the storage bucket path (not the full URL, just the path in the bucket)
        return storage_path
    except Exception as e:
        print(f"⚠️  Could not upload {file_path} to storage: {e}", file=sys.stderr)
        return None


def update_pdf_path_in_db(job_id: str, pdf_path: str, docx_path: str = None, company: str = "", title: str = "") -> None:
    """Update DB with local paths and storage paths for generated artifacts."""
    try:
        relative_pdf = str(Path(pdf_path).relative_to(PROJECT_ROOT))
    except ValueError:
        relative_pdf = pdf_path

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    update_data = {"resume_pdf_path": relative_pdf}

    # Upload PDF to storage
    pdf_storage_path = _upload_artifact_to_storage(job_id, pdf_path, company, title)
    if pdf_storage_path:
        update_data["resume_pdf_path_storage"] = pdf_storage_path

    # Upload DOCX to storage if provided
    if docx_path and Path(docx_path).exists():
        try:
            relative_docx = str(Path(docx_path).relative_to(PROJECT_ROOT))
        except ValueError:
            relative_docx = docx_path

        docx_storage_path = _upload_artifact_to_storage(job_id, docx_path, company, title)
        if docx_storage_path:
            update_data["resume_docx_path"] = docx_storage_path

    res = sb.table("applications").update(update_data).eq("job_id", job_id).execute()
    if res.data:
        print(f"✅ Saved artifact paths to DB for job {job_id}")
    else:
        print(f"⚠️  Could not update artifact paths in DB for job {job_id}")


def _safe_dirname(s: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", s.lower())[:40].strip("-")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a styled resume DOCX/PDF from markdown.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--job-id",      help="Job UUID — fetches resume_md from DB")
    src.add_argument("--resume-path", help="Path to a local resume.md file")
    parser.add_argument("--output", "-o", help="Output path (.docx or .pdf)")
    parser.add_argument("--docx-only",  action="store_true", help="Generate DOCX only, skip PDF")
    parser.add_argument("--no-db-update", action="store_true", help="Skip writing PDF path to DB")
    args = parser.parse_args()

    company = ""
    title = ""
    if args.job_id:
        resume_md, company, title = fetch_resume_md_from_db(args.job_id)
        if args.output:
            output_path = args.output
        else:
            dir_name = f"{_safe_dirname(company)}-{_safe_dirname(title)}"
            out_dir  = PROJECT_ROOT / "output" / "applications" / dir_name
            out_dir.mkdir(parents=True, exist_ok=True)
            ext = ".docx" if args.docx_only else ".pdf"
            output_path = str(out_dir / f"resume{ext}")
    else:
        p = Path(args.resume_path)
        if not p.exists():
            print(f"❌ File not found: {args.resume_path}")
            sys.exit(1)
        resume_md = p.read_text(encoding="utf-8")
        ext = ".docx" if args.docx_only else ".pdf"
        output_path = args.output or str(p.with_suffix(ext))

    docx_path = None
    if args.docx_only or output_path.endswith(".docx"):
        docx_output = output_path if output_path.endswith(".docx") else output_path.replace(".pdf", ".docx")
        markdown_to_docx(resume_md, docx_output)
        docx_path = docx_output
    else:
        markdown_to_pdf(resume_md, output_path)
        # For PDF, also generate DOCX alongside it
        docx_path = output_path.replace(".pdf", ".docx")

    if args.job_id and not args.no_db_update and not args.docx_only:
        update_pdf_path_in_db(args.job_id, output_path, docx_path, company, title)


if __name__ == "__main__":
    main()
