#!/usr/bin/env python3
"""
Resume PDF Generator — Converts resume markdown to a styled PDF matching the
AI 2026 Resume template (large name, two-column header, accent color on companies).

Usage:
  uv run python .claude/skills/scout/scripts/generate_resume_pdf.py --job-id <uuid>
  uv run python .claude/skills/scout/scripts/generate_resume_pdf.py --resume-path path/to/resume.md

Install: uv add reportlab
"""

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

ACCENT_COLOR = "#4A90D9"   # Blue used for company names and links


# ─── ReportLab lazy import ────────────────────────────────────────────────────

def _require_reportlab():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT, TA_RIGHT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            HRFlowable, Table, TableStyle, KeepTogether,
        )
        return dict(
            letter=letter, inch=inch,
            PS=ParagraphStyle, C=HexColor,
            TA_LEFT=TA_LEFT, TA_RIGHT=TA_RIGHT,
            Doc=SimpleDocTemplate, P=Paragraph, S=Spacer,
            HR=HRFlowable, T=Table, TS=TableStyle, KT=KeepTogether,
        )
    except ImportError:
        print("❌ Missing dependency: reportlab")
        print("Install with:  uv add reportlab")
        sys.exit(1)


# ─── Markdown parsing ─────────────────────────────────────────────────────────

def parse_resume_md(md_text: str) -> list[tuple[str, str]]:
    """
    Parse resume markdown into (block_type, content) tuples.

    Types:
      name       # H1 — candidate name
      contact    # line immediately following name (pipe-separated contact info)
      section    # H2 — section header (Experience, Education, Skills…)
      role       # H3 — role/company/education entry
      subtitle   # H4
      bullet     # - or * list item
      paragraph  # body text
    """
    blocks: list[tuple[str, str]] = []
    prev_type: str | None = None

    for raw in md_text.split('\n'):
        line = raw.rstrip()
        if not line:
            prev_type = 'blank'
            continue

        if line.startswith('# '):
            t, content = 'name', line[2:].strip()
        elif line.startswith('## '):
            t, content = 'section', line[3:].strip()
        elif line.startswith('### '):
            t, content = 'role', line[4:].strip()
        elif line.startswith('#### '):
            t, content = 'subtitle', line[5:].strip()
        elif line.startswith('- ') or line.startswith('* '):
            t, content = 'bullet', line[2:].strip()
        else:
            t = 'contact' if prev_type == 'name' else 'paragraph'
            content = line.strip()

        blocks.append((t, content))
        prev_type = t

    return blocks


def parse_role_line(text: str) -> tuple[str, str, str]:
    """
    Parse '### Company — Title (dates)' → (title, company, dates).

    Returns (full_text, '', '') if no recognisable pattern is found
    (e.g. a skills subsection header).
    """
    # Extract trailing (dates) — the parens may contain an em-dash for date ranges
    date_match = re.search(r'\(([^()]+)\)\s*$', text)
    dates = ''
    remainder = text
    if date_match:
        dates = date_match.group(1).strip()
        remainder = text[:date_match.start()].strip()

    # Split on first em-dash, en-dash, or hyphen separator
    for sep in (' \u2014 ', ' \u2013 ', ' — ', ' – ', ' - '):
        if sep in remainder:
            parts = remainder.split(sep, 1)
            company = parts[0].strip()
            title = parts[1].strip()
            return title, company, dates

    # No separator — could be a subsection header (Skills) or bare entry
    return remainder, '', dates


def parse_contact_items(contact_line: str) -> list[dict]:
    """
    Split 'email | phone | [LinkedIn](url)' into structured items.
    Returns list of {'label': str, 'is_link': bool}.
    """
    items = []
    for part in contact_line.split(' | '):
        part = part.strip()
        m = re.match(r'\[([^\]]+)\]\([^)]+\)', part)
        if m:
            items.append({'label': m.group(1), 'is_link': True})
        else:
            items.append({'label': part, 'is_link': False})
    return items


# ─── Inline markup helpers ────────────────────────────────────────────────────

def _x(text: str) -> str:
    """XML-escape special characters."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _inline(text: str) -> str:
    """Escape XML then apply inline markdown → ReportLab markup."""
    text = _x(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'<u>\1</u>', text)
    return text


# ─── PDF construction ─────────────────────────────────────────────────────────

def build_flowables(blocks: list[tuple[str, str]], rl: dict) -> list:
    P  = rl['P']
    S  = rl['S']
    HR = rl['HR']
    PS = rl['PS']
    C  = rl['C']
    T  = rl['T']
    TS = rl['TS']
    KT = rl['KT']
    inch   = rl['inch']
    letter = rl['letter']

    # Page geometry — must match SimpleDocTemplate margins below
    LEFT_MARGIN  = 0.75 * inch
    RIGHT_MARGIN = 0.75 * inch
    text_w = letter[0] - LEFT_MARGIN - RIGHT_MARGIN

    # ── Palette ──────────────────────────────────────────────────────────────
    c_dark   = C('#111111')
    c_mid    = C('#333333')
    c_muted  = C('#888888')
    c_rule   = C('#CCCCCC')
    c_accent = C(ACCENT_COLOR)

    # ── Styles ───────────────────────────────────────────────────────────────
    name_st   = PS('Name',    fontName='Helvetica-Bold', fontSize=38, leading=42,
                              textColor=c_dark)
    sub_st    = PS('NameSub', fontName='Helvetica',      fontSize=12, leading=16,
                              textColor=C('#777777'), spaceAfter=0)
    ctact_st  = PS('Ctact',   fontName='Helvetica',      fontSize=9,  leading=13,
                              textColor=c_muted, alignment=rl['TA_RIGHT'])
    ctact_link_st = PS('CtactLink', fontName='Helvetica', fontSize=9, leading=13,
                                    textColor=c_accent, alignment=rl['TA_RIGHT'])

    sect_st   = PS('Sect',    fontName='Helvetica-Bold', fontSize=15, leading=18,
                              textColor=c_dark, spaceBefore=4, spaceAfter=3)

    role_t_st = PS('RoleT',   fontName='Helvetica-Bold', fontSize=10.5, leading=14,
                              textColor=c_dark)
    role_d_st = PS('RoleD',   fontName='Helvetica',      fontSize=9.5,  leading=14,
                              textColor=c_muted, alignment=rl['TA_RIGHT'])
    subsect_st = PS('Subsect', fontName='Helvetica-Bold', fontSize=10.5, leading=14,
                               textColor=c_dark, spaceBefore=4, spaceAfter=1)

    body_st   = PS('Body',    fontName='Helvetica', fontSize=10,  leading=13.5,
                              textColor=c_dark, spaceAfter=3)
    bull_st   = PS('Bull',    fontName='Helvetica', fontSize=10,  leading=13,
                              textColor=c_dark, leftIndent=12,   spaceAfter=2)
    subt_st   = PS('Subt',    fontName='Helvetica-Oblique', fontSize=9.5, leading=12,
                              textColor=c_muted, spaceAfter=2)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _hr(space_before=6, space_after=4):
        return HR(width='100%', thickness=0.5, color=c_rule,
                  spaceBefore=space_before, spaceAfter=space_after)

    def _role_table(left_para, right_para):
        tbl = T(
            [[left_para, right_para]],
            colWidths=[text_w * 0.68, text_w * 0.32],
        )
        tbl.setStyle(TS([
            ('VALIGN',        (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN',         (1, 0), (1,  0),  'RIGHT'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return tbl

    # ── Walk blocks ───────────────────────────────────────────────────────────
    flowables: list = []
    pending_bullets: list[str] = []
    pending_name: str | None = None

    def flush_bullets():
        for b in pending_bullets:
            flowables.append(P(f'&#x2022;&#160; {b}', bull_st))
        pending_bullets.clear()

    for block_type, content in blocks:

        if block_type == 'bullet':
            pending_bullets.append(_inline(content))
            continue

        flush_bullets()

        # ── Name — stash and wait for contact line to render header ──────────
        if block_type == 'name':
            pending_name = content
            continue

        # ── Contact — render two-column header now ───────────────────────────
        elif block_type == 'contact':
            items = parse_contact_items(content)

            left_cell = [P(_x(pending_name or ''), name_st)]

            right_cell = []
            for ci in items:
                st = ctact_link_st if ci['is_link'] else ctact_st
                right_cell.append(P(_x(ci['label']), st))

            header_tbl = T(
                [[left_cell, right_cell]],
                colWidths=[text_w * 0.62, text_w * 0.38],
            )
            header_tbl.setStyle(TS([
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                ('ALIGN',         (1, 0), (1,  0),  'RIGHT'),
                ('LEFTPADDING',   (0, 0), (-1, -1), 0),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
                ('TOPPADDING',    (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            flowables.append(header_tbl)
            flowables.append(S(10, 0))
            flowables.append(_hr(space_before=0, space_after=8))

        # ── Section header ────────────────────────────────────────────────────
        elif block_type == 'section':
            flowables.append(P(_x(content), sect_st))
            flowables.append(_hr(space_before=0, space_after=5))

        # ── Role / subsection entry ───────────────────────────────────────────
        elif block_type == 'role':
            title, company, dates = parse_role_line(content)

            if company or dates:
                # Looks like a real role entry
                if company:
                    role_html = (
                        f'<b>{_x(title)}</b>'
                        f' | <font color="{ACCENT_COLOR}">{_x(company)}</font>'
                    )
                else:
                    role_html = f'<b>{_x(title)}</b>'

                flowables.append(_role_table(
                    P(role_html, role_t_st),
                    P(_x(dates), role_d_st),
                ))
            else:
                # No company/dates — subsection header (e.g. Skills subcategory)
                flowables.append(P(_x(title), subsect_st))

        # ── Subtitle (H4) ─────────────────────────────────────────────────────
        elif block_type == 'subtitle':
            flowables.append(P(_inline(content), subt_st))

        # ── Body paragraph ────────────────────────────────────────────────────
        elif block_type == 'paragraph':
            flowables.append(P(_inline(content), body_st))

    flush_bullets()
    return flowables


def markdown_to_pdf(md_text: str, output_path: str) -> None:
    rl = _require_reportlab()

    blocks    = parse_resume_md(md_text)
    flowables = build_flowables(blocks, rl)

    doc = rl['Doc'](
        output_path,
        pagesize=rl['letter'],
        leftMargin=0.75 * rl['inch'],
        rightMargin=0.75 * rl['inch'],
        topMargin=0.70 * rl['inch'],
        bottomMargin=0.70 * rl['inch'],
    )
    doc.build(flowables)
    print(f"✅ PDF written to: {output_path}")


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

    job          = job_res.data[0]
    company_name = (job.get("companies") or {}).get("name", "unknown")
    job_title    = job.get("title", "unknown")

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
    return re.sub(r'[^a-z0-9-]', '-', s.lower())[:40].strip('-')


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a styled PDF resume from markdown.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--job-id",      help="Job UUID — fetches resume_md from DB")
    src.add_argument("--resume-path", help="Path to a local resume.md file")
    parser.add_argument("--output", "-o", help="Output PDF path")
    parser.add_argument("--no-db-update", action="store_true",
                        help="Skip writing PDF path back to DB")
    args = parser.parse_args()

    if args.job_id:
        resume_md, company, title = fetch_resume_md_from_db(args.job_id)
        if args.output:
            output_path = args.output
        else:
            dir_name = f"{_safe_dirname(company)}-{_safe_dirname(title)}"
            out_dir  = Path(__file__).parent.parent / "applications" / dir_name
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(out_dir / "resume.pdf")
    else:
        p = Path(args.resume_path)
        if not p.exists():
            print(f"❌ File not found: {args.resume_path}")
            sys.exit(1)
        resume_md   = p.read_text(encoding="utf-8")
        output_path = args.output or str(p.with_suffix(".pdf"))

    markdown_to_pdf(resume_md, output_path)

    if args.job_id and not args.no_db_update:
        update_pdf_path_in_db(args.job_id, output_path)


if __name__ == "__main__":
    main()
