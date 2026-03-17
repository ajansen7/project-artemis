#!/usr/bin/env python3
"""
Resume DOCX/PDF Generator — Builds a resume DOCX from the Noto Sans template,
then converts to PDF via LibreOffice (soffice).

Usage:
  uv run python .claude/tools/generate_resume_docx.py --job-id <uuid>
  uv run python .claude/tools/generate_resume_docx.py --resume-path path/to/resume.md

Requires LibreOffice for PDF conversion:
  brew install --cask libreoffice
"""

import argparse
import copy
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# .claude/tools/ is 2 levels below project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

TEMPLATE_PATH = PROJECT_ROOT / ".claude" / "skills" / "apply" / "references" / "resume_template.docx"

W  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML = "http://www.w3.org/XML/1998/namespace"

def _w(tag): return f"{{{W}}}{tag}"
def _r(tag): return f"{{{R}}}{tag}"


# ─── Markdown parser ──────────────────────────────────────────────────────────

def parse_resume_md(md_text: str) -> list[tuple[str, str]]:
    """
    Parse resume markdown into (block_type, content) tuples.

    Types:
      name       # H1
      contact    # pipe-separated contact line right after name
      section    # H2 heading
      role       # H3 entry (role/company/dates)
      bold       # **text** standalone paragraph
      italic     # *text* or _text_ standalone paragraph
      bullet     # - list item
      hr         # --- divider (skipped in output)
      paragraph  # body text
    """
    blocks: list[tuple[str, str]] = []
    prev_type: str | None = None

    for raw in md_text.split("\n"):
        line = raw.rstrip()
        if not line:
            prev_type = "blank"
            continue

        if line.startswith("# "):
            t, content = "name", line[2:].strip()
        elif line.startswith("## "):
            t, content = "section", line[3:].strip()
        elif line.startswith("### "):
            t, content = "role", line[4:].strip()
        elif line.startswith("- ") or line.startswith("* "):
            t, content = "bullet", line[2:].strip()
        elif line.strip() in ("---", "***", "___"):
            t, content = "hr", ""
        elif re.match(r"^\*\*[^*].+\*\*$", line.strip()) or re.match(r"^__[^_].+__$", line.strip()):
            t, content = "bold", line.strip().strip("*").strip("_")
        elif re.match(r"^\*[^*].+\*$", line.strip()) or re.match(r"^_[^_].+_$", line.strip()):
            t, content = "italic", line.strip().strip("*").strip("_")
        else:
            t = "contact" if prev_type == "name" else "paragraph"
            content = line.strip()

        blocks.append((t, content))
        prev_type = t

    return blocks


def parse_role_line(text: str) -> tuple[str, str, str]:
    """
    Parse '### Company — Title | dates' → (title, company, dates).
    Also handles '### Company — Title (dates)' and '### Title (dates)'.
    """
    # Try ' | dates' suffix first
    pipe_match = re.search(r"\s+\|\s+(.+)$", text)
    if pipe_match:
        dates = pipe_match.group(1).strip()
        remainder = text[: pipe_match.start()].strip()
    else:
        # Try '(dates)' suffix
        paren_match = re.search(r"\(([^()]+)\)\s*$", text)
        if paren_match:
            dates = paren_match.group(1).strip()
            remainder = text[: paren_match.start()].strip()
        else:
            dates = ""
            remainder = text

    for sep in (" \u2014 ", " \u2013 ", " — ", " – ", " - "):
        if sep in remainder:
            parts = remainder.split(sep, 1)
            company = parts[0].strip()
            title = parts[1].strip()
            return title, company, dates

    return remainder, "", dates


def parse_contact_items(contact_line: str) -> list[dict]:
    """
    Split 'email | phone | [LinkedIn](url) | ...' into structured items.
    Returns list of {'label': str, 'url': str|None}.
    """
    items = []
    for part in contact_line.split(" | "):
        part = part.strip()
        m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
        if m:
            items.append({"label": m.group(1), "url": m.group(2)})
        else:
            items.append({"label": part, "url": None})
    return items


# ─── Inline markup stripping ──────────────────────────────────────────────────

def _strip_inline(text: str) -> str:
    """Remove markdown inline formatting for plain text insertion."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def _parse_inline_runs(text: str) -> list[dict]:
    """
    Parse inline markdown into runs: [{'text': str, 'bold': bool, 'italic': bool, 'url': str|None}]
    """
    runs = []
    pattern = re.compile(
        r"\*\*(.+?)\*\*"       # **bold**
        r"|\*(.+?)\*"          # *italic*
        r"|__(.+?)__"          # __bold__
        r"|_(.+?)_"            # _italic_
        r"|\[([^\]]+)\]\(([^)]+)\)"  # [link](url)
    )
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            runs.append({"text": text[pos:m.start()], "bold": False, "italic": False, "url": None})
        if m.group(1):   # **bold**
            runs.append({"text": m.group(1), "bold": True, "italic": False, "url": None})
        elif m.group(2): # *italic*
            runs.append({"text": m.group(2), "bold": False, "italic": True, "url": None})
        elif m.group(3): # __bold__
            runs.append({"text": m.group(3), "bold": True, "italic": False, "url": None})
        elif m.group(4): # _italic_
            runs.append({"text": m.group(4), "bold": False, "italic": True, "url": None})
        elif m.group(5): # [link](url)
            runs.append({"text": m.group(5), "bold": False, "italic": False, "url": m.group(6)})
        pos = m.end()
    if pos < len(text):
        runs.append({"text": text[pos:], "bold": False, "italic": False, "url": None})
    return runs or [{"text": text, "bold": False, "italic": False, "url": None}]


# ─── DOCX XML helpers ─────────────────────────────────────────────────────────

from lxml import etree


def _new_elem(tag: str, **attrs) -> etree._Element:
    e = etree.Element(_w(tag))
    for k, v in attrs.items():
        e.set(_w(k), str(v))
    return e


def _make_run(text: str, bold=False, italic=False, color=None, sz=None,
              font_ascii=None, underline=False) -> etree._Element:
    r = _new_elem("r")
    rPr = _new_elem("rPr")
    if font_ascii:
        fonts = _new_elem("rFonts")
        for attr in ("ascii", "cs", "eastAsia", "hAnsi"):
            fonts.set(_w(attr), font_ascii)
        rPr.append(fonts)
    if bold:
        b = _new_elem("b"); b.set(_w("val"), "1"); rPr.append(b)
        bCs = _new_elem("bCs"); bCs.set(_w("val"), "1"); rPr.append(bCs)
    if italic:
        i = _new_elem("i"); rPr.append(i)
    if color:
        c = _new_elem("color"); c.set(_w("val"), color.lstrip("#")); rPr.append(c)
    if sz:
        s = _new_elem("sz"); s.set(_w("val"), str(sz)); rPr.append(s)
        sCs = _new_elem("szCs"); sCs.set(_w("val"), str(sz)); rPr.append(sCs)
    if underline:
        u = _new_elem("u"); u.set(_w("val"), "single"); rPr.append(u)
    if len(rPr):
        r.append(rPr)
    t = _new_elem("t")
    t.text = text
    if text and (text[0] == " " or text[-1] == " "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    return r


def _make_hyperlink(text: str, url: str, rel_id: str, color="1155cc",
                    sz=20, font="Noto Sans Light") -> etree._Element:
    hl = etree.Element(_w("hyperlink"))
    hl.set(_r("id"), rel_id)
    r = _make_run(text, color=color, sz=sz, font_ascii=font, underline=True)
    hl.append(r)
    return hl


def _clear_para_runs(para_elem: etree._Element) -> None:
    """Remove all runs and hyperlinks from a paragraph."""
    for child in list(para_elem):
        tag = child.tag.split("}")[-1]
        if tag in ("r", "hyperlink", "bookmarkStart", "bookmarkEnd"):
            para_elem.remove(child)


def _set_para_text(para_elem: etree._Element, text: str,
                   font=None, sz=None, bold=False, color=None) -> None:
    """Replace paragraph content with a single plain run."""
    _clear_para_runs(para_elem)
    r = _make_run(text, bold=bold, color=color, sz=sz, font_ascii=font)
    para_elem.append(r)


# ─── Template paragraph builders ──────────────────────────────────────────────

def _build_summary_para(text: str) -> etree._Element:
    """Plain body paragraph for summary text."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    sp = _new_elem("spacing"); sp.set(_w("before"), "120"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    ind = _new_elem("ind"); ind.set(_w("right"), "-90"); pPr.append(ind)
    p.append(pPr)
    for run_data in _parse_inline_runs(text):
        p.append(_make_run(run_data["text"], bold=run_data["bold"], italic=run_data["italic"]))
    return p


def _build_section_heading(text: str) -> etree._Element:
    """Heading1 section header."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    style = _new_elem("pStyle"); style.set(_w("val"), "Heading1"); pPr.append(style)
    rPr = _new_elem("rPr")
    sz = _new_elem("sz"); sz.set(_w("val"), "30"); rPr.append(sz)
    szCs = _new_elem("szCs"); szCs.set(_w("val"), "30"); rPr.append(szCs)
    pPr.append(rPr)
    p.append(pPr)
    p.append(_make_run(text))
    return p


def _build_divider() -> etree._Element:
    """Horizontal rule divider paragraph (grey line)."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    sp = _new_elem("spacing"); sp.set(_w("line"), "36"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    ind = _new_elem("ind")
    ind.set(_w("left"), "-90"); ind.set(_w("right"), "-90"); ind.set(_w("firstLine"), "0")
    pPr.append(ind)
    p.append(pPr)
    r = etree.Element(_w("r"))
    pict = etree.SubElement(r, _w("pict"))
    ns_v = "urn:schemas-microsoft-com:vml"
    ns_o = "urn:schemas-microsoft-com:office:office"
    rect = etree.SubElement(pict, f"{{{ns_v}}}rect")
    rect.set("style", "width:0.0pt;height:1.5pt")
    rect.set(f"{{{ns_o}}}hr", "t")
    rect.set(f"{{{ns_o}}}hrstd", "t")
    rect.set(f"{{{ns_o}}}hralign", "center")
    rect.set("fillcolor", "#A0A0A0")
    rect.set("stroked", "f")
    p.append(r)
    return p


def _build_role_header(title: str, company: str, dates: str) -> etree._Element:
    """Role header: 'Title | Company [right-tab] dates'"""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    tabs = _new_elem("tabs")
    tab = _new_elem("tab")
    tab.set(_w("val"), "right"); tab.set(_w("leader"), "none"); tab.set(_w("pos"), "10980")
    tabs.append(tab); pPr.append(tabs)
    sp = _new_elem("spacing"); sp.set(_w("before"), "80"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    p.append(pPr)

    # Title — bold, dark color
    p.append(_make_run(title, bold=True, color="434343", sz=22, font_ascii="Noto Sans"))
    if company:
        p.append(_make_run(" | ", bold=True, color="434343", sz=22, font_ascii="Noto Sans"))
        # Company — bold, blue
        p.append(_make_run(company, bold=True, color="6A94BF", sz=22, font_ascii="Noto Sans"))
    if dates:
        # Tab + dates — grey, lighter
        tab_r = etree.Element(_w("r"))
        tab_t = etree.SubElement(tab_r, _w("tab"))  # noqa — this is a tab character element
        p.append(tab_r)
        p.append(_make_run(dates, color="73808D", sz=18, font_ascii="Noto Sans Light"))
    return p


def _build_body_para(text: str, indent_left: int = 0) -> etree._Element:
    """Plain body paragraph (intro text under a role)."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    sp = _new_elem("spacing"); sp.set(_w("after"), "80"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    if indent_left:
        ind = _new_elem("ind"); ind.set(_w("left"), str(indent_left)); ind.set(_w("firstLine"), "0"); pPr.append(ind)
    p.append(pPr)
    for run_data in _parse_inline_runs(text):
        p.append(_make_run(run_data["text"], bold=run_data["bold"], italic=run_data["italic"],
                           font_ascii="Noto Sans"))
    return p


def _build_bold_intro(text: str) -> etree._Element:
    """Bold intro line (e.g. **AI Strategy & Platform**)."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    sp = _new_elem("spacing"); sp.set(_w("after"), "40"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    p.append(pPr)
    for run_data in _parse_inline_runs(text):
        p.append(_make_run(run_data["text"], bold=True if run_data["bold"] or not any(
            r["bold"] for r in _parse_inline_runs(text)) else False,
                           italic=run_data["italic"], font_ascii="Noto Sans", sz=22))
    return p


def _build_italic_para(text: str) -> etree._Element:
    """Italic note paragraph."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    sp = _new_elem("spacing"); sp.set(_w("after"), "40"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    p.append(pPr)
    # Strip outer italic markers, render italic
    inner = re.sub(r"^\*(.+)\*$", r"\1", text.strip())
    inner = re.sub(r"^_(.+)_$", r"\1", inner)
    p.append(_make_run(inner, italic=True, color="73808D", sz=20, font_ascii="Noto Sans Light"))
    return p


def _build_bullet(text: str) -> etree._Element:
    """Bullet list paragraph (numId=2 from template)."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    numPr = _new_elem("numPr")
    ilvl = _new_elem("ilvl"); ilvl.set(_w("val"), "0"); numPr.append(ilvl)
    numId = _new_elem("numId"); numId.set(_w("val"), "2"); numPr.append(numId)
    pPr.append(numPr)
    sp = _new_elem("spacing"); sp.set(_w("after"), "80"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    ind = _new_elem("ind"); ind.set(_w("left"), "450"); ind.set(_w("hanging"), "360"); pPr.append(ind)
    rPr_default = _new_elem("rPr")
    fonts = _new_elem("rFonts")
    for attr in ("ascii", "cs", "eastAsia", "hAnsi"):
        fonts.set(_w(attr), "Noto Sans Light")
    rPr_default.append(fonts)
    color = _new_elem("color"); color.set(_w("val"), "434343"); rPr_default.append(color)
    sz = _new_elem("sz"); sz.set(_w("val"), "18"); rPr_default.append(sz)
    szCs = _new_elem("szCs"); szCs.set(_w("val"), "18"); rPr_default.append(szCs)
    pPr.append(rPr_default)
    p.append(pPr)

    # Render inline markup in bullets
    for run_data in _parse_inline_runs(text):
        font = "Noto Sans" if run_data["bold"] else "Noto Sans"
        p.append(_make_run(run_data["text"], bold=run_data["bold"], italic=run_data["italic"],
                           color="434343", sz=18, font_ascii=font))
    return p


def _build_skills_category(category: str) -> etree._Element:
    """Skills category header (bold, smaller)."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    sp = _new_elem("spacing"); sp.set(_w("before"), "60"); sp.set(_w("after"), "20"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    p.append(pPr)
    p.append(_make_run(category, bold=True, color="434343", sz=20, font_ascii="Noto Sans"))
    return p


def _build_skills_items(text: str) -> etree._Element:
    """Skills items line."""
    p = etree.Element(_w("p"))
    pPr = _new_elem("pPr")
    wc = _new_elem("widowControl"); wc.set(_w("val"), "0"); pPr.append(wc)
    sp = _new_elem("spacing"); sp.set(_w("after"), "60"); sp.set(_w("line"), "240"); sp.set(_w("lineRule"), "auto"); pPr.append(sp)
    p.append(pPr)
    for run_data in _parse_inline_runs(text):
        p.append(_make_run(run_data["text"], bold=run_data["bold"], italic=run_data["italic"],
                           color="434343", sz=18, font_ascii="Noto Sans Light"))
    return p


# ─── Header paragraph editors ─────────────────────────────────────────────────

def _update_header(doc_body: etree._Element, name: str, contact_items: list[dict]) -> None:
    """
    Update paragraphs 0-6 in the template with the candidate's info.
    Template layout:
      [0] Name  [1] Subtitle(tagline)  [2] empty
      [3] email [4] phone [5] location [6] LinkedIn+sectPr
    """
    children = list(doc_body)

    # Para 0: Name
    _set_para_text(children[0], name, font="Noto Sans Black", sz=72)

    # Para 1: Subtitle — leave as-is (template has "AI Product Leader")
    # We could update if the MD had a subtitle, but for now keep template value

    # Paras 2-6: contact items (right-aligned, Noto Sans Light, sz=20)
    # Map contact items to contact slot paragraphs (3, 4, 5, 6)
    # Items are: email, phone, location (optional), LinkedIn, Portfolio, GitHub, ...
    # Slots [3,4,5,6] — fill first 4 items or leave blank
    contact_slots = [children[3], children[4], children[5], children[6]]

    # Separate hyperlinks from plain items
    plain_items = [c for c in contact_items if not c["url"]]
    link_items  = [c for c in contact_items if c["url"]]

    # Fill slots: plain items first, then links (last slot = LinkedIn)
    slot_data = (plain_items + link_items)[:4]
    # Pad to 4 with empty
    while len(slot_data) < 4:
        slot_data.append({"label": "", "url": None})

    for slot_para, item in zip(contact_slots, slot_data):
        _clear_para_runs(slot_para)
        if not item["label"]:
            continue
        if item["url"]:
            # Add hyperlink relationship
            from docx.opc.constants import RELATIONSHIP_TYPE as RT
            # We'll handle rel ids by reusing existing ones or adding new ones
            # For simplicity, render as plain text with blue styling
            slot_para.append(_make_run(item["label"], color="1155cc", sz=20,
                                       font_ascii="Noto Sans Light", underline=True))
        else:
            slot_para.append(_make_run(item["label"], sz=20, font_ascii="Noto Sans Light"))


# ─── Body builder ─────────────────────────────────────────────────────────────

def _build_body_elements(blocks: list[tuple[str, str]]) -> list[etree._Element]:
    """Convert parsed blocks into DOCX paragraph elements for the main body."""
    elements: list[etree._Element] = []
    i = 0

    # Skip header blocks — already handled by _update_header
    while i < len(blocks) and blocks[i][0] in ("name", "contact"):
        i += 1

    # Check for a summary paragraph (paragraph block before first section)
    summary_blocks = []
    while i < len(blocks) and blocks[i][0] in ("paragraph", "hr", "blank"):
        if blocks[i][0] == "paragraph":
            summary_blocks.append(blocks[i][1])
        i += 1

    if summary_blocks:
        for s in summary_blocks:
            elements.append(_build_summary_para(s))

    # Now process sections
    while i < len(blocks):
        btype, content = blocks[i]

        if btype == "hr":
            i += 1
            continue

        if btype == "section":
            elements.append(_build_section_heading(content))
            elements.append(_build_divider())
            i += 1
            continue

        if btype == "role":
            title, company, dates = parse_role_line(content)
            elements.append(_build_role_header(title, company, dates))
            i += 1
            continue

        if btype == "bold":
            elements.append(_build_bold_intro(content))
            i += 1
            continue

        if btype == "italic":
            elements.append(_build_italic_para(content))
            i += 1
            continue

        if btype == "bullet":
            elements.append(_build_bullet(content))
            i += 1
            continue

        if btype == "paragraph":
            elements.append(_build_body_para(content))
            i += 1
            continue

        i += 1  # skip unknowns

    return elements


# ─── Main builder ─────────────────────────────────────────────────────────────

def markdown_to_docx(md_text: str, output_path: str) -> None:
    try:
        from docx import Document
    except ImportError:
        print("❌ Missing dependency: python-docx")
        print("Install with: uv add python-docx")
        sys.exit(1)

    if not TEMPLATE_PATH.exists():
        print(f"❌ Template not found: {TEMPLATE_PATH}")
        sys.exit(1)

    doc = Document(str(TEMPLATE_PATH))
    body = doc.element.body
    children = list(body)

    blocks = parse_resume_md(md_text)

    # Update header paragraphs (name, contact)
    name_block = next((c for t, c in blocks if t == "name"), "")
    contact_block = next((c for t, c in blocks if t == "contact"), "")
    contact_items = parse_contact_items(contact_block) if contact_block else []
    _update_header(body, name_block, contact_items)

    # Determine whether the MD contains a summary paragraph
    has_md_summary = any(
        t == "paragraph"
        for t, _ in blocks
        if t not in ("name", "contact")  # first non-header paragraph before a section
    ) and next(
        (t for t, _ in blocks if t not in ("name", "contact", "hr")), None
    ) == "paragraph"

    # Remove body content paragraphs (index 8 onwards, keep final sectPr)
    # children[7]  = horizontal rule divider right after header — keep it
    # children[8]  = template summary paragraph — keep if MD has no summary
    # children[9:] = rest of existing body content — remove
    # children[-1] = final sectPr — keep
    final_sectPr = children[-1]
    body_start = 8 if has_md_summary else 9
    for child in children[body_start:-1]:
        body.remove(child)

    # Build new body content
    new_elements = _build_body_elements(blocks)

    # Insert new elements before the final sectPr
    for elem in new_elements:
        final_sectPr.addprevious(elem)

    doc.save(output_path)
    print(f"✅ DOCX written to: {output_path}")


def docx_to_pdf(docx_path: str, output_dir: str) -> str:
    """Convert DOCX to PDF using LibreOffice headless. Returns PDF path."""
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

    docx_stem = Path(docx_path).stem
    pdf_path = str(Path(output_dir) / f"{docx_stem}.pdf")
    print(f"✅ PDF written to: {pdf_path}")
    return pdf_path


def _find_soffice() -> str | None:
    """Find the LibreOffice soffice binary."""
    candidates = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    # Try PATH
    result = subprocess.run(["which", "soffice"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def markdown_to_pdf(md_text: str, output_path: str) -> None:
    """Generate DOCX then convert to PDF. output_path should end in .pdf"""
    docx_path = output_path.replace(".pdf", ".docx")
    markdown_to_docx(md_text, docx_path)
    out_dir = str(Path(output_path).parent)
    docx_to_pdf(docx_path, out_dir)


# ─── DB helpers ───────────────────────────────────────────────────────────────

def fetch_resume_md_from_db(job_id: str) -> tuple[str, str, str]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    app_res = sb.table("applications").select("resume_md").eq("job_id", job_id).execute()
    if not app_res.data or not app_res.data[0].get("resume_md"):
        print(f"❌ No resume_md found for job {job_id}. Run /apply first.")
        sys.exit(1)

    job_res = sb.table("jobs").select("title, companies(name)").eq("id", job_id).execute()
    if not job_res.data:
        print(f"❌ Job {job_id} not found.")
        sys.exit(1)

    job = job_res.data[0]
    company_name = (job.get("companies") or {}).get("name", "unknown")
    job_title = job.get("title", "unknown")

    return app_res.data[0]["resume_md"], company_name, job_title


def update_pdf_path_in_db(job_id: str, pdf_path: str) -> None:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    res = sb.table("applications").update({"resume_pdf_path": pdf_path}).eq("job_id", job_id).execute()
    if res.data:
        print(f"✅ Saved PDF path to DB for job {job_id}")
    else:
        print(f"⚠️  Could not update resume_pdf_path in DB for job {job_id}")


def _safe_dirname(s: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", s.lower())[:40].strip("-")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a styled resume DOCX/PDF from markdown.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--job-id", help="Job UUID — fetches resume_md from DB")
    src.add_argument("--resume-path", help="Path to a local resume.md file")
    parser.add_argument("--output", "-o", help="Output path (.docx or .pdf)")
    parser.add_argument("--docx-only", action="store_true", help="Generate DOCX only, skip PDF")
    parser.add_argument("--no-db-update", action="store_true",
                        help="Skip writing PDF path back to DB")
    args = parser.parse_args()

    if args.job_id:
        resume_md, company, title = fetch_resume_md_from_db(args.job_id)
        if args.output:
            output_path = args.output
        else:
            dir_name = f"{_safe_dirname(company)}-{_safe_dirname(title)}"
            out_dir = PROJECT_ROOT / "output" / "applications" / dir_name
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

    if args.docx_only or output_path.endswith(".docx"):
        markdown_to_docx(resume_md, output_path if output_path.endswith(".docx")
                          else output_path.replace(".pdf", ".docx"))
    else:
        markdown_to_pdf(resume_md, output_path)

    if args.job_id and not args.no_db_update and not args.docx_only:
        update_pdf_path_in_db(args.job_id, output_path)


if __name__ == "__main__":
    main()
