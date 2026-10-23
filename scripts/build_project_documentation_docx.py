"""
Generate comprehensive, executive-ready documentation for Turio in .docx format.
Adheres strictly to professional typographic hierarchy, consistent corporate palettes,
and clear tables/callout styling.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

# Palette: Tech / Modern Minimal
# Primary: Deep Slate Teal (#164E63)
# Secondary: Cool Steel Slate (#334155)
# Accent: Electric Amber (#D97706)
# Dark Neutral (Text): Carbon (#0F172A)
# Light Neutral (Shading): Soft Fog (#F8FAFC)
# Highlight / Alert: Crimson Rose (#991B1B / #FEF2F2)
# Success: Emerald (#065F46 / #ECFDF5)
# Border Grey: #CBD5E1

COLOR_PRIMARY = RGBColor(22, 78, 99)       # #164E63
COLOR_SECONDARY = RGBColor(51, 65, 85)     # #334155
COLOR_ACCENT = RGBColor(217, 119, 6)       # #D97706
COLOR_TEXT_DARK = RGBColor(15, 23, 42)     # #0F172A
COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # #64748B
COLOR_WHITE = RGBColor(255, 255, 255)

HEX_PRIMARY = "164E63"
HEX_SECONDARY = "334155"
HEX_ACCENT = "D97706"
HEX_LIGHT_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_CALLOUT_BG = "F1F5F9"
HEX_WARN_BG = "FEF2F2"
HEX_WARN_BORDER = "EF4444"
HEX_SUCCESS_BG = "ECFDF5"
HEX_SUCCESS_BORDER = "10B981"


def set_cell_margins(cell, top=140, bottom=140, left=200, right=200):
    """Set inner padding for table cell in twips (20 twips = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, hex_color):
    """Set shading/background color for cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    """Set custom borders for cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')

    borders = {'top': top, 'bottom': bottom, 'left': left, 'right': right}
    for edge, border in borders.items():
        if border:
            b = OxmlElement(f'w:{edge}')
            b.set(qn('w:val'), border.get('val', 'single'))
            b.set(qn('w:sz'), str(border.get('sz', 4)))
            b.set(qn('w:space'), '0')
            b.set(qn('w:color'), border.get('color', HEX_BORDER))
            tcBorders.append(b)
        else:
            b = OxmlElement(f'w:{edge}')
            b.set(qn('w:val'), 'none')
            tcBorders.append(b)
    tcPr.append(tcBorders)


def style_table(table, col_widths, headers, data, alt_shading=True):
    """
    Format table with corporate styling:
    - Bold white text on Primary header
    - Alternating row background
    - Thin clean borders
    - Proper cell padding
    - CantSplit on rows and tblHeader on header
    """
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hdr_row = table.rows[0]
    hdr_tr = hdr_row._tr.get_or_add_trPr()
    hdr_tr.append(OxmlElement('w:tblHeader'))
    hdr_tr.append(OxmlElement('w:cantSplit'))

    for i, cell in enumerate(hdr_row.cells):
        cell.width = col_widths[i]
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=160, bottom=160, left=180, right=180)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_borders(cell,
                         top={'val': 'single', 'sz': 6, 'color': HEX_PRIMARY},
                         bottom={'val': 'single', 'sz': 12, 'color': HEX_ACCENT})

        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(headers[i])
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        run.font.color.rgb = COLOR_WHITE

    # Data rows
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        row_tr = row._tr.get_or_add_trPr()
        row_tr.append(OxmlElement('w:cantSplit'))

        bg_color = HEX_LIGHT_BG if (alt_shading and r_idx % 2 == 1) else "FFFFFF"

        for c_idx, cell_value in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.width = col_widths[c_idx]
            if bg_color != "FFFFFF":
                set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_borders(cell,
                             top={'val': 'single', 'sz': 4, 'color': HEX_BORDER},
                             bottom={'val': 'single', 'sz': 4, 'color': HEX_BORDER})

            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(str(cell_value))
            run.font.name = 'Calibri'
            run.font.size = Pt(9.5)
            run.font.color.rgb = COLOR_TEXT_DARK


def add_callout(doc, text, title=None, style_type="info"):
    """
    Add a styled callout box (single-cell table) with a thick left accent bar.
    style_type: "info" | "warning" | "success"
    """
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.5)

    if style_type == "warning":
        bg_hex = HEX_WARN_BG
        border_hex = HEX_WARN_BORDER
        text_color = RGBColor(153, 27, 27)
    elif style_type == "success":
        bg_hex = HEX_SUCCESS_BG
        border_hex = HEX_SUCCESS_BORDER
        text_color = RGBColor(6, 95, 70)
    else: # info
        bg_hex = HEX_CALLOUT_BG
        border_hex = HEX_PRIMARY
        text_color = COLOR_PRIMARY

    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=160, bottom=160, left=240, right=200)
    set_cell_borders(cell, left={'val': 'single', 'sz': 24, 'color': border_hex})

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    if title:
        r_title = p.add_run(title + "\n")
        r_title.bold = True
        r_title.font.name = 'Calibri'
        r_title.font.size = Pt(10.5)
        r_title.font.color.rgb = text_color

    r_body = p.add_run(text)
    r_body.font.name = 'Calibri'
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = COLOR_TEXT_DARK

    # Add spacing after callout
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(6)


def add_page_number_to_run(run):
    """Insert PAGE field into run."""
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    r = run._r
    r.append(fldChar1)
    r.append(instrText)
    r.append(fldChar2)
    r.append(fldChar3)


def add_heading_1(doc, text):
    h = doc.add_heading(level=1)
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(17)
    run.bold = True
    run.font.color.rgb = COLOR_PRIMARY
    return h


def add_heading_2(doc, text):
    h = doc.add_heading(level=2)
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(13.5)
    run.bold = True
    run.font.color.rgb = COLOR_SECONDARY
    return h


def add_heading_3(doc, text):
    h = doc.add_heading(level=3)
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.bold = True
    run.font.color.rgb = COLOR_ACCENT
    return h


def add_body_paragraph(doc, text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = COLOR_TEXT_DARK
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(10.5)
    r.font.color.rgb = COLOR_TEXT_DARK
    return p


def add_bullet_point(doc, text, bold_prefix=None, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(10)
        r_pre.font.color.rgb = COLOR_TEXT_DARK
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(10)
    r.font.color.rgb = COLOR_TEXT_DARK
    return p


def build_documentation():
    print("Initializing Document...")
    doc = docx.Document()

    # Page setup - Margins 1 inch
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)
        s.different_first_page_header_footer = True

        # Header (from page 2)
        header_p = s.header.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_hdr = header_p.add_run("TURIO — Comprehensive System Engineering Documentation")
        r_hdr.font.name = 'Calibri'
        r_hdr.font.size = Pt(8.5)
        r_hdr.font.color.rgb = COLOR_TEXT_MUTED

        # Footer
        footer_p = s.footer.paragraphs[0]
        footer_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_ftr_l = footer_p.add_run("CONFIDENTIAL & PROPRIETARY — ACADEMIC & RESEARCH USE\t\tPage ")
        r_ftr_l.font.name = 'Calibri'
        r_ftr_l.font.size = Pt(8.5)
        r_ftr_l.font.color.rgb = COLOR_TEXT_MUTED
        add_page_number_to_run(footer_p.add_run())

    # ==========================================
    # COVER PAGE
    # ==========================================
    cover_p = doc.add_paragraph()
    cover_p.paragraph_format.space_before = Pt(40)
    cover_p.paragraph_format.space_after = Pt(10)

    r_tag = cover_p.add_run("ENGINEERING & RESEARCH COMPREHENSIVE REPORT")
    r_tag.bold = True
    r_tag.font.name = 'Calibri'
    r_tag.font.size = Pt(11)
    r_tag.font.color.rgb = COLOR_ACCENT

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("TURIO: Intelligent Career Navigation, Resume Analysis & Application Automation Engine")
    r_title.bold = True
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(26)
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(40)
    r_sub = p_sub.add_run(
        "A Unified Architectural, Algorithmic, and Operational Guide to Multi-Modal Resume Parsing, "
        "SBERT-Powered Recommendation, and Verified Application Workflows."
    )
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = COLOR_SECONDARY

    # Metadata Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Author / Owner", "RUTHVIK (Final-Year Computer Science & Engineering)"),
        ("Project Status", "Phase 3/4 Verified Native Implementation (Windows Native Stack)"),
        ("Repository Location", "D:/College/4-2 project"),
        ("Active Technologies", "FastAPI, Next.js (App Router), PostgreSQL 16, S3rver, Playwright Chromium, SBERT"),
        ("Documentation Date", "October 15, 2026")
    ]
    for i, (k, v) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 80, 80, 120, 120)
        set_cell_margins(c1, 80, 80, 120, 120)
        set_cell_borders(c0, bottom={'val': 'single', 'sz': 4, 'color': HEX_BORDER})
        set_cell_borders(c1, bottom={'val': 'single', 'sz': 4, 'color': HEX_BORDER})

        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(k)
        r0.bold = True
        r0.font.name = 'Calibri'
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = COLOR_PRIMARY

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(v)
        r1.font.name = 'Calibri'
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_TEXT_DARK

    doc.add_page_break()

    # ==========================================
    # SECTION 1: EXECUTIVE SUMMARY
    # ==========================================
    add_heading_1(doc, "1. Executive Summary & Problem Formulation")

    add_body_paragraph(
        doc,
        "In modern labor markets, technical job seekers face severe friction: discovering relevant positions, "
        "interpreting multi-page job specifications, assessing domain fit, and manually completing highly repetitive "
        "application portals. Turio addresses this documented research gap by establishing a continuous, intelligent, "
        "and user-verifiable pipeline from the applicant's raw resume to human-approved application submission."
    )

    add_callout(
        doc,
        "Research Gap Solved: Prior literature and commercial tooling treat semantic matching, ATS form parsing, and "
        "application tracking as disconnected silos. Turio fuses layout-aware resume parsing, hybrid lexical-semantic "
        "job recommendation (SBERT + TF-IDF), and idempotent, guarded browser automation into a cohesive, user-in-the-loop system.",
        title="CORE RESEARCH CONTRIBUTION",
        style_type="info"
    )

    add_heading_2(doc, "1.1 The Seven-Stage Lifecycle")
    stages = [
        ("Stage 1 — Layout-Aware Ingestion: ", "Locally extracts structured facts from complex PDF resumes (tables, letter-spaced headings, multi-page timelines) without sending sensitive document bytes to external OCR vendors."),
        ("Stage 2 — Semantic Profile Generation: ", "Normalizes skills, experiences, projects, education, and contact metadata into a versioned, privacy-controlled PostgreSQL candidate profile."),
        ("Stage 3 — Job Catalog & Ingestion: ", "Deduplicates and imports tens of thousands of job opportunities (56,339 verified active jobs across 3,448 companies) with source-backed deadlines and platform metadata."),
        ("Stage 4 — Multi-Stage Hybrid Matching: ", "Combines lexical keyword matching, TF-IDF scoring, and 384-dimensional Sentence-BERT embeddings (all-MiniLM-L6-v2) to generate transparent, explainable match scores."),
        ("Stage 5 — Adaptive Form Mapping & Assistance: ", "Inspects external application forms, maps canonical candidate attributes, and selectively queries free AI models (via OpenRouter/Jev) for complex generative questions."),
        ("Stage 6 — Guarded Application Automation: ", "Fills validated ATS forms (Ashby-hosted v2) via Playwright Chromium, strictly governed by single-use cryptographic permits, checksum-verified PDF uploads, and explicit user approvals."),
        ("Stage 7 — Application Tracking & Answer Reuse: ", "Maintains full state machine lifecycles (created → ready_for_review → submitted) with cross-application answer reuse, bulk fill controls, and manual audit trails.")
    ]
    for b_title, b_desc in stages:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    # Insert System Workflow Architecture Flowchart
    flowchart_path = r"D:\College\4-2 project\docs\images\workflow_architecture.png"
    if os.path.exists(flowchart_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(12)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(flowchart_path, width=Inches(6.2))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(0)
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run("Figure 1: Turio End-to-End System Workflow & Pipeline Architecture")
        r_cap.font.name = 'Calibri'
        r_cap.font.size = Pt(8.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================
    # SECTION 2: SYSTEM ARCHITECTURE
    # ==========================================
    add_heading_1(doc, "2. High-Level System Architecture & Service Boundaries")

    add_body_paragraph(
        doc,
        "Turio is constructed as a modern, decoupled client-server architecture designed for high maintainability, "
        "local reproducibility, and strict boundary isolation. In accordance with Architectural Decision Record ADR-042, "
        "the system operates as a native Windows stack without Docker or WSL dependencies, utilizing native binaries "
        "for PostgreSQL 16, portable S3rver object storage, FastAPI, and Next.js."
    )

    arch_headers = ["Layer / Subsystem", "Primary Technology", "Port / Protocol", "Architectural Responsibility"]
    arch_widths = [Inches(1.5), Inches(1.4), Inches(1.1), Inches(2.5)]
    arch_data = [
        ["Frontend UI", "Next.js 14 (App Router), React, Tailwind CSS", "13000 (HTTP)", "Responsive user dashboard, profile editor, job match explorer, inline review & bulk application controls."],
        ["Backend API", "FastAPI (Python 3.11), Pydantic v2, Uvicorn", "18080 (HTTP)", "RESTful endpoints, authentication proxy, orchestrator state machine, ML inference dispatcher."],
        ["Relational DB", "PostgreSQL 16 (Native Portable Runtime)", "18543 (TCP)", "ACID persistence for users, profiles, jobs, applications, matching cache, and event ledger."],
        ["Object Storage", "S3rver (Local S3-Compatible Storage)", "19000 (HTTP/S3)", "Encrypted, isolated private storage for uploaded PDF resumes and original file byte buffers."],
        ["Background Worker", "Python Async Worker (app.workers.main)", "Internal Queue", "Durable database-backed execution of catalog ingestion, batch embeddings, and long-running jobs."],
        ["Automation Engine", "Playwright (Chromium), Browser Use", "Headless Subprocess", "DOM inspection, form field schema extraction, reverse-engineered GraphQL RPC, guarded submission."]
    ]
    tbl_arch = doc.add_table(rows=len(arch_data) + 1, cols=4)
    style_table(tbl_arch, arch_widths, arch_headers, arch_data)

    add_body_paragraph(doc, "", space_after=10)
    add_heading_2(doc, "2.1 Security & Network Isolation Principles")
    sec_points = [
        ("HTTP-Only Cookie Proxying: ", "The Next.js frontend acts as an authentication proxy. JWT access and refresh tokens are stored in strict HTTP-only, SameSite=Lax cookies, completely inaccessible to browser JavaScript (XSS mitigation)."),
        ("Zero Pre-Approval Outbound Mutations: ", "The headless browser network boundary blocks all HTTP POST/PUT/DELETE requests to employer domains until the candidate reviews the exact cryptographic answer snapshot."),
        ("Cryptographic Operation Nonces: ", "Every preparation, review, and submission operation is assigned an immutable UUID operation token. Expired or duplicate operations are fenced off via database idempotency tables."),
        ("Original File Verification: ", "Resumes uploaded to employer portals are verified against the SHA-256 checksum of the candidate's original document in object storage, preventing unauthorized synthetic document generation.")
    ]
    for b_title, b_desc in sec_points:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    # ==========================================
    # SECTION 3: DATABASE DESIGN & SCHEMA
    # ==========================================
    doc.add_page_break()
    add_heading_1(doc, "3. Database Architecture & Relational Entities")

    add_body_paragraph(
        doc,
        "Turio leverages PostgreSQL 16 with native JSONB columns for flexible schemas alongside strictly typed relational tables. "
        "The relational schema cleanly separates authentication, candidate profiles, normalized job catalogs, algorithmic matches, "
        "and application lifecycles."
    )

    db_headers = ["Table Name", "Primary Key", "Foreign Keys", "Key Attributes & Purpose"]
    db_widths = [Inches(1.4), Inches(1.0), Inches(1.4), Inches(2.7)]
    db_data = [
        ["users", "id (UUID)", "None", "email (UNIQUE), password_hash, email_verified, auth_provider, last_login_at."],
        ["refresh_tokens", "id (UUID)", "user_id → users.id", "family_id, token_hash, issued_at, expires_at, revoked_at (implements token family reuse detection)."],
        ["profiles", "id (UUID)", "user_id → users.id (UNIQUE)", "version (optimistic lock), full_name, phone, location, linkedin_url, preferred_roles (JSONB), work_auth."],
        ["resumes", "id (UUID)", "user_id → users.id", "storage_key, original_filename, mime_type, checksum (SHA-256), parsed_text, parser_version."],
        ["skills", "id (UUID)", "user_id, source_resume_id", "name, normalized_name, confidence score (extracted from resume or user-added)."],
        ["experiences", "id (UUID)", "user_id, source_resume_id", "company, title, start_date, end_date, description."],
        ["educations", "id (UUID)", "user_id, source_resume_id", "institution, degree, field, start_date, end_date."],
        ["projects", "id (UUID)", "user_id, source_resume_id", "name, description, technologies (JSONB array)."],
        ["jobs", "id (UUID)", "source_id → job_sources.id", "external_id, title, company, description, location, application_url, ats, content_hash, deadline, logo_url."],
        ["job_matches", "id (UUID)", "user_id, job_id", "semantic_score, skill_score, final_score, explanation_payload (JSONB structured evidence)."],
        ["applications", "id (UUID)", "user_id, job_id, resume_id", "status (created..submitted), revision, review_token, review_snapshot (JSONB), submitted_at, outcome."],
        ["application_fields", "id (UUID)", "application_id → applications.id", "field_key, label, input_type, required, normalized_intent, source_locator, options (JSONB)."],
        ["application_answers", "field_id (UUID)", "field_id → application_fields.id", "value (JSONB), value_source ('profile', 'user', 'jev_profile'), user_confirmed (bool)."],
        ["saved_answers", "id (UUID)", "user_id → users.id", "question_key (hash of intent/label), value (JSONB). Enables 'Answer Once' across multiple applications."],
        ["application_events", "id (UUID)", "application_id → applications.id", "event_type, event_data (JSONB), created_at. Immutable audit ledger of all transitions."],
        ["idempotency_records", "key (String)", "user_id → users.id", "request_hash, response (JSONB snapshot), created_at. Guarantees safe replay of identical requests."]
    ]
    tbl_db = doc.add_table(rows=len(db_data) + 1, cols=4)
    style_table(tbl_db, db_widths, db_headers, db_data)

    add_body_paragraph(doc, "", space_after=10)
    add_heading_2(doc, "3.1 The Application State Machine")
    add_body_paragraph(
        doc,
        "Every application follows a strict finite state machine (FSM). Applications cannot transition into submitted "
        "states without an immutable review snapshot approved by the applicant:"
    )

    fsm_steps = [
        ("created: ", "Application draft instantiated for a job posting; no fields mapped yet."),
        ("preparing: ", "Playwright worker actively inspecting ATS URL or mapping candidate profile data."),
        ("needs_input: ", "Form fields extracted, but at least one required field lacks a confirmed value."),
        ("ready_for_review: ", "100% of required fields populated and confirmed. A cryptographic review_token is generated."),
        ("approved_for_submission: ", "Applicant explicitly approved the review snapshot; valid for 15 minutes."),
        ("submitting: ", "Guarded browser automation actively executing form submission."),
        ("submitted: ", "Remote ATS confirmed receipt with verified success payload (FormSubmitSuccess)."),
        ("verification_failed: ", "Submission encountered an unconfirmed outcome or network failure; locked against automatic retry.")
    ]
    for b_title, b_desc in fsm_steps:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    # Insert FSM Lifecycle Diagram
    fsm_path = r"D:\College\4-2 project\docs\images\fsm_lifecycle.png"
    if os.path.exists(fsm_path):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_before = Pt(12)
        p_img2.paragraph_format.space_after = Pt(4)
        run_img2 = p_img2.add_run()
        run_img2.add_picture(fsm_path, width=Inches(6.2))

        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.paragraph_format.space_before = Pt(0)
        p_cap2.paragraph_format.space_after = Pt(12)
        r_cap2 = p_cap2.add_run("Figure 2: Turio Application Lifecycle Finite State Machine (FSM)")
        r_cap2.font.name = 'Calibri'
        r_cap2.font.size = Pt(8.5)
        r_cap2.font.italic = True
        r_cap2.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================
    # SECTION 4: RESUME & ML MATCHING PIPELINE
    # ==========================================
    doc.add_page_break()
    add_heading_1(doc, "4. Multi-Modal Resume Parsing & Semantic Matching Engine")

    add_body_paragraph(
        doc,
        "Turio's recommendation core uses a multi-stage hybrid matching algorithm that balances broad lexical recall "
        "with deep semantic precision. Rather than treating resumes as flat strings, Turio parses positional text "
        "layouts and compares representations using Sentence-BERT embeddings."
    )

    add_heading_2(doc, "4.1 Deterministic Resume Layout Extraction")
    add_body_paragraph(
        doc,
        "Modern resumes feature multi-column layouts, character-spaced headers ('E X P E R I E N C E'), and complex tables. "
        "Turio implements an in-house layout parser (backend/app/services/resume_layout.py) that:"
    )
    parser_pts = [
        ("Horizontal Gap Detection: ", "Segments multi-column pages into independent column streams based on whitespace clustering."),
        ("Heading Normalization: ", "Collapses spaced headers and matches against 40+ semantic alias sets (Education, Experience, Projects, Skills)."),
        ("Entity Association: ", "Extracts date ranges (e.g., 'May 2022 - Aug 2023'), company names, and bulleted achievements without LLM latency."),
        ("Privacy Boundary: ", "100% of text extraction occurs locally. Only opt-in generative classifications use external APIs (OpenRouter).")
    ]
    for b_title, b_desc in parser_pts:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    add_heading_2(doc, "4.2 Mathematical Formulation of Semantic Matching")
    add_body_paragraph(
        doc,
        "The overall matching score S(c, j) between candidate c and job posting j is computed as a weighted combination "
        "of semantic embedding similarity, structured skill overlap, education alignment, and experience depth:"
    )

    add_callout(
        doc,
        "S(c, j) = w_s · S_semantic(c, j) + w_k · S_skills(c, j) + w_e · S_exp(c, j) + w_d · S_edu(c, j)\n\n"
        "Where:\n"
        "• S_semantic = cosine_similarity(e_candidate, e_job) using Sentence-BERT all-MiniLM-L6-v2 (384-dimensional dense vectors).\n"
        "• S_skills = Jaccard_similarity(Skills_candidate, Skills_job_required) with TF-IDF importance weighting.\n"
        "• S_exp = min(1.0, Years_candidate / Years_job_required).\n"
        "• Baseline weights: w_s = 0.50, w_k = 0.30, w_e = 0.15, w_d = 0.05.",
        title="HYBRID MATCHING EQUATION",
        style_type="info"
    )

    add_body_paragraph(
        doc,
        "Embeddings are computed once upon resume upload and cached in the PostgreSQL database using content-addressed hashes. "
        "During job discovery, vector similarity is computed across candidate vectors and pre-indexed job descriptions, "
        "delivering sub-second recommendation retrieval across 56,000+ job opportunities."
    )

    # ==========================================
    # SECTION 5: APPLICATION AUTOMATION & ATS ADAPTERS
    # ==========================================
    doc.add_page_break()
    add_heading_1(doc, "5. Guarded Application Automation & ATS Integration")

    add_body_paragraph(
        doc,
        "Automating job applications presents substantial technical hurdles: anti-bot protections (Cloudflare, reCAPTCHA), "
        "complex dynamic single-page applications, and the risk of submitting incorrect candidate information. "
        "Turio implements an audited, safety-first automation framework centered on the Ashby Hosted v2 adapter."
    )

    add_heading_2(doc, "5.1 The Ashby Hosted v2 Architecture")
    add_body_paragraph(
        doc,
        "Rather than relying on brittle CSS selectors or free-form LLM agents clicking around the screen, "
        "Turio's Ashby adapter reverse-engineers the underlying GraphQL form-state RPC protocol utilized by Ashby job portals:"
    )

    ashby_steps = [
        ("Public Form Schema Inspection: ", "Intercepts ApiJobPosting and ApiOrganizationFromHostedJobsPageName GraphQL queries to construct the exact form field definition."),
        ("Discrete RPC Field Updates: ", "Executes ApiSetFormValue mutations for scalar fields (Text, Phone, URL, Boolean, Select) and ApiSetFormValueToFile for resume uploads."),
        ("Cryptographic Form Audit: ", "Before triggering final submission, calls audit_forms() to verify that every single value returned by the employer matches the candidate-approved review snapshot exactly."),
        ("Single-Use Submission Permit: ", "Issues a JsonPermit strictly bound to the ApiSubmitSingleApplicationFormAction or ApiSubmitMultipleFormsAction mutation. Any altered request body is instantly blocked."),
        ("Verification Confirmation: ", "Awaits the employer's server response verifying that FormSubmitSuccess was returned for the application and all attached surveys before marking the application as submitted.")
    ]
    for b_title, b_desc in ashby_steps:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    add_callout(
        doc,
        "Anti-Bot & CAPTCHA Policy: Turio strictly adheres to ethical automation standards. The platform never bypasses "
        "CAPTCHA challenges or fabricates user consent. If an employer ATS issues a CAPTCHA challenge or requires custom "
        "widgets, Turio transitions the application to 'manual_submission_required' and launches a visible browser handoff "
        "for the user to complete.",
        title="ETHICAL AUTOMATION & RECAPTCHA COMPLIANCE",
        style_type="warning"
    )

    add_heading_2(doc, "5.2 Shared-Answer Reuse & Bulk Applications")
    add_body_paragraph(
        doc,
        "Turio's bulk application workflow (implemented in frontend/components/bulk-applications.tsx and "
        "backend/app/services/applications.py) allows job seekers to apply to multiple companies efficiently:"
    )
    bulk_pts = [
        ("Answer Once Workflow: ", "Common application questions (e.g., 'Do you require sponsorship?', 'LinkedIn Profile', 'Notice Period') are grouped across selected drafts. Answering them once stores the values in saved_answers and updates all matching drafts simultaneously."),
        ("Profile Auto-Synchronization: ", "When a candidate enters or edits contact facts (LinkedIn URL, phone number, location) in an application review, the system automatically synchronizes the updates back to the master Profile table."),
        ("Independent Snapshot Isolation: ", "Each application retains its own immutable review snapshot and cryptographic hash. Modifying one draft never corrupts or invalidates already-submitted applications.")
    ]
    for b_title, b_desc in bulk_pts:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    # ==========================================
    # SECTION 6: API SPECIFICATION
    # ==========================================
    doc.add_page_break()
    add_heading_1(doc, "6. RESTful API Specification & Endpoints")

    add_body_paragraph(
        doc,
        "The Turio backend exposes a versioned RESTful API under the /api/v1 prefix. All endpoints enforce JSON envelope "
        "structures, Pydantic v2 data validation, and bearer token authorization."
    )

    api_headers = ["Method & Path", "Request Payload", "Response Envelope", "Description & Security"]
    api_widths = [Inches(2.0), Inches(1.4), Inches(1.4), Inches(1.7)]
    api_data = [
        ["POST /api/v1/auth/signup", "email, password", "{ user, tokens }", "Creates candidate account, hashes password via Argon2/Bcrypt, sets HTTP-only cookies."],
        ["POST /api/v1/auth/login", "email, password", "{ user, tokens }", "Validates credentials, issues access/refresh tokens with family rotation."],
        ["GET /api/v1/profiles/me", "None", "{ profile, skills, exp }", "Retrieves complete structured profile for authenticated user."],
        ["PATCH /api/v1/profiles/me", "ProfileUpdateRequest", "{ profile }", "Updates user profile fields and increments profile.version."],
        ["POST /api/v1/resumes/upload", "multipart/form-data (PDF)", "{ resume_id, parsed_facts }", "Uploads PDF to S3, parses layout, populates profile, triggers vector cache."],
        ["GET /api/v1/jobs", "page, limit, search, ats", "{ jobs, total, page }", "Paginated job search across 56,000+ indexed opportunities."],
        ["GET /api/v1/matches", "page, limit, min_score", "{ matches, explanations }", "Retrieves ranked recommendations tailored to candidate profile."],
        ["POST /api/v1/applications", "{ job_id, resume_id }", "{ application }", "Initializes application draft for specific job posting."],
        ["POST /api/v1/applications/{id}/prepare", "{ ai_assist: bool }", "{ application, fields }", "Inspects remote ATS form schema, maps profile answers, detects missing items."],
        ["POST /api/v1/applications/{id}/answers", "{ answers: [{field_id, val}] }", "{ application }", "Submits user answers, supports save_for_reuse flag."],
        ["POST /api/v1/applications/{id}/review", "None", "{ review_token, snapshot }", "Locks application into immutable review snapshot ready for approval."],
        ["POST /api/v1/applications/{id}/approve", "{ review_token }", "{ status: 'submitted' }", "Authorizes Playwright worker to execute remote form submission."],
        ["POST /api/v1/applications/{id}/handoff", "{ review_token }", "{ ready: true }", "Launches visible browser session for user to complete manual/CAPTCHA forms."]
    ]
    tbl_api = doc.add_table(rows=len(api_data) + 1, cols=4)
    style_table(tbl_api, api_widths, api_headers, api_data)

    # ==========================================
    # SECTION 7: TESTING & VERIFICATION
    # ==========================================
    doc.add_page_break()
    add_heading_1(doc, "7. Quality Assurance, Test Coverage & Verification Evidence")

    add_body_paragraph(
        doc,
        "Turio is developed with rigorous engineering verification standards. In accordance with project policy, "
        "every architectural feature, bug fix, and security guard is backed by automated unit, integration, and E2E regression suites."
    )

    test_headers = ["Test Suite / Verification Layer", "Scope & Runner", "Passing Checks", "Evidence File"]
    test_widths = [Inches(1.8), Inches(1.6), Inches(1.2), Inches(1.9)]
    test_data = [
        ["Backend Core Suite", "pytest backend/tests -q", "385 passed (43 skips)", "docs/evidence/bug-audit-fixes-2026-10-14.json"],
        ["PostgreSQL Concurrency Suite", "python .runtime/verify-audit-postgres.py", "64 passed (Selector Loop)", "docs/evidence/postgresql-regression-2026-09-15.xml"],
        ["Hosted Browser Transport", "pytest backend/tests/test_hosted_transport_browser.py", "40 passed (Chromium)", "docs/evidence/hosted-rpc-guard-2026-10-14.json"],
        ["Playwright Full QA Usability Audit", "python scratch/playwright_audit.py", "33 verified checkpoints", "docs/evidence/qa_audit_20261014/final_audit_report.json"],
        ["Frontend UI Contract Suite", "npm run test / scripts/smoke_ui.py", "17 pass / 6 bulk groups", "docs/evidence/workflow-fixes-2026-10-14.json"],
        ["Job Catalog CSV Ingestion", "scripts/verify_stack.py", "55,189 jobs ingested", "docs/evidence/postgresql-job-import-2026-09-16.json"]
    ]
    tbl_test = doc.add_table(rows=len(test_data) + 1, cols=4)
    style_table(tbl_test, test_widths, test_headers, test_data)

    add_body_paragraph(doc, "", space_after=10)
    add_heading_2(doc, "7.1 Summary of October 14 Bug Audit & Remediation")
    add_body_paragraph(
        doc,
        "On October 14, 2026, a comprehensive usability audit was performed across all user workflows. Nine distinct "
        "functional and usability defects were identified in BUG_AUDIT.md and systematically resolved:"
    )
    bugs = [
        ("BUG-APP-001 (Contact Field Re-Prompting): ", "Resolved by expanding regex patterns in resume_parser.py to capture short and non-standard LinkedIn URLs, ensuring contact facts populate candidate profiles immediately."),
        ("BUG-APP-002 (Answer Persistence & Profile Sync): ", "Resolved by updating applications.py so confirmed contact answers automatically sync to the master Profile table upon saving, eliminating duplicate user prompts."),
        ("BUG-APP-003 (Uncertain Submission Lockout): ", "Added safe reset-to-review endpoints requiring explicit applicant confirmation that no employer application was received, clearing blocked verification_failed states."),
        ("BUG-APP-004 (Inline Answer Overrides): ", "Implemented local draft overrides in applications.tsx allowing candidates to customize profile-derived answers for specific job postings without altering global records."),
        ("BUG-UX-001 (Bulk Controls Availability): ", "Extracted shared bulk-applications.tsx component, bringing 'Answer Once' and batch approval features to both /jobs and /applications tracker routes."),
        ("BUG-GUARD-001 (Hosted RPC Guard False Rejection): ", "Corrected JsonPermit tracking in ashby.py so consumed valid form-state RPCs remain accepted even when later unrelated POST requests are blocked.")
    ]
    for b_title, b_desc in bugs:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    # ==========================================
    # SECTION 8: INSTALLATION & OPERATIONAL GUIDE
    # ==========================================
    doc.add_page_break()
    add_heading_1(doc, "8. Installation, Local Deployment & Operational Playbook")

    add_body_paragraph(
        doc,
        "Turio is engineered to run seamlessly on native Windows development environments without virtualization overhead. "
        "All services are managed via unified PowerShell orchestration scripts."
    )

    add_heading_2(doc, "8.1 Prerequisites & System Requirements")
    prereqs = [
        ("Operating System: ", "Windows 10/11 (64-bit)."),
        ("Python Environment: ", "Python 3.11.x with pip and virtualenv."),
        ("Node.js Runtime: ", "Node.js v18.x or v20.x with npm."),
        ("Database Engine: ", "PostgreSQL 16 (Installed natively or located under .runtime/native/pgsql)."),
        ("Object Storage: ", "Node-based S3rver (Located under .runtime/native/s3rver).")
    ]
    for b_title, b_desc in prereqs:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    add_heading_2(doc, "8.2 One-Command Stack Startup")
    add_body_paragraph(
        doc,
        "To start the entire local stack (PostgreSQL, S3rver, FastAPI backend, Next.js frontend, and background worker), "
        "execute the following command in PowerShell:"
    )

    add_callout(
        doc,
        "cd \"D:\\College\\4-2 project\"\n"
        "powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -SkipBuild\n\n"
        "Active Service Endpoints:\n"
        "• Frontend Web Interface:  http://127.0.0.1:13000\n"
        "• FastAPI Documentation:   http://127.0.0.1:18080/docs\n"
        "• API Health Endpoint:     http://127.0.0.1:18080/api/v1/health\n"
        "• PostgreSQL Database:     127.0.0.1:18543 (turio_dev)\n"
        "• Object Storage Service:  http://127.0.0.1:19000",
        title="STARTUP COMMAND & PORTS",
        style_type="success"
    )

    add_heading_2(doc, "8.3 Running the Automated Test Suite")
    add_body_paragraph(doc, "To verify system health and run the complete backend regression test suite:")
    test_cmds = [
        ("Run Default Unit Tests: ", "python -m pytest backend/tests -q"),
        ("Run with Browser Tests: ", "$env:TURIO_BROWSER_TESTS=\"1\"; python -m pytest backend/tests/test_hosted_transport_browser.py"),
        ("Run Full Playwright Audit: ", "python scratch/playwright_audit.py")
    ]
    for b_title, b_desc in test_cmds:
        add_bullet_point(doc, b_desc, bold_prefix=b_title)

    # Save Document
    output_path = r"D:\College\4-2 project\TURIO_PROJECT_DOCUMENTATION.docx"
    print(f"Saving documentation to {output_path}...")
    doc.save(output_path)
    print("Document successfully created and saved.")

if __name__ == "__main__":
    build_documentation()
