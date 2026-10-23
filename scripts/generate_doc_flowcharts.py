"""
Generate 4 publication-quality 300-DPI architectural and algorithmic flowcharts
for the comprehensive Turio technical documentation.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'DejaVu Sans', 'Arial', 'Helvetica']


def create_system_workflow_diagram(output_path):
    fig, ax = plt.subplots(figsize=(12, 14), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Title Banner
    title_box = patches.FancyBboxPatch((5, 93), 90, 5, boxstyle="round,pad=0.5",
                                      facecolor="#164E63", edgecolor="none")
    ax.add_patch(title_box)
    ax.text(50, 95.5, "TURIO: END-TO-END SYSTEM WORKFLOW ARCHITECTURE",
            ha='center', va='center', color='#FFFFFF', fontsize=13, fontweight='bold')

    # Lane 1: Candidate Input & Parsing (Y: 76 to 90)
    lane1 = patches.FancyBboxPatch((5, 75), 90, 16, boxstyle="round,pad=0.8",
                                  facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
    ax.add_patch(lane1)
    ax.text(8, 88.5, "PHASE 1: CANDIDATE INGESTION & LAYOUT-AWARE EXTRACTION",
            fontsize=9.5, fontweight='bold', color="#164E63")

    b1_1 = patches.FancyBboxPatch((8, 77.5), 23, 8.5, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b1_1)
    ax.text(19.5, 83, "Resume Upload (PDF)", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(19.5, 79.5, "Local File Browser\nHash Validation (SHA-256)", ha='center', va='center', fontsize=7.5, color="#64748B")

    b1_2 = patches.FancyBboxPatch((38.5, 77.5), 23, 8.5, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b1_2)
    ax.text(50, 83, "In-House Layout Parser", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(50, 79.5, "Multi-Column Gap Analysis\nHeading Normalization", ha='center', va='center', fontsize=7.5, color="#64748B")

    b1_3 = patches.FancyBboxPatch((69, 77.5), 23, 8.5, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b1_3)
    ax.text(80.5, 83, "Structured Profile DB", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(80.5, 79.5, "Skills, Experience, Education\nVersioned Candidate Entity", ha='center', va='center', fontsize=7.5, color="#64748B")

    ax.annotate("", xy=(38.5, 81.75), xytext=(31, 81.75), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(69, 81.75), xytext=(61.5, 81.75), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(50, 71.5), xytext=(50, 75), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.8))

    # Lane 2: Catalog Ingestion & Hybrid Matching (Y: 52 to 71.5)
    lane2 = patches.FancyBboxPatch((5, 52), 90, 19.5, boxstyle="round,pad=0.8",
                                  facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
    ax.add_patch(lane2)
    ax.text(8, 69, "PHASE 2: JOB CATALOG INGESTION & SBERT HYBRID MATCHING",
            fontsize=9.5, fontweight='bold', color="#164E63")

    b2_1 = patches.FancyBboxPatch((8, 54.5), 24, 11.5, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b2_1)
    ax.text(20, 62.5, "Job Catalog Ingestion", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(20, 58, "56,339 Verified Postings\n3,448 Tech Companies\nContent Hash Deduplication", ha='center', va='center', fontsize=7.5, color="#64748B")

    b2_2 = patches.FancyBboxPatch((38, 54.5), 24, 11.5, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#D97706", linewidth=1.5)
    ax.add_patch(b2_2)
    ax.text(50, 62.8, "Hybrid Matching Engine", ha='center', va='center', fontsize=9, fontweight='bold', color="#D97706")
    ax.text(50, 58, "SBERT (all-MiniLM-L6-v2)\nTF-IDF Skill Overlap (0.25)\nDense Vector Cosine (0.45)", ha='center', va='center', fontsize=7.5, color="#0F172A")

    b2_3 = patches.FancyBboxPatch((68, 54.5), 24, 11.5, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b2_3)
    ax.text(80, 62.5, "Ranked Matches & Proof", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(80, 58, "Deterministic Scoring (0-100)\nStructured Evidence Payload\nPostgreSQL JSONB Cache", ha='center', va='center', fontsize=7.5, color="#64748B")

    ax.annotate("", xy=(38, 60.25), xytext=(32, 60.25), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(68, 60.25), xytext=(62, 60.25), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(50, 48.5), xytext=(50, 52), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.8))

    # Lane 3: Application Orchestration & Review (Y: 27.5 to 48.5)
    lane3 = patches.FancyBboxPatch((5, 27.5), 90, 21, boxstyle="round,pad=0.8",
                                  facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
    ax.add_patch(lane3)
    ax.text(8, 46, "PHASE 3: FORM INSPECTION, ANSWER REUSE & HUMAN REVIEW",
            fontsize=9.5, fontweight='bold', color="#164E63")

    b3_1 = patches.FancyBboxPatch((8, 30), 24, 13, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b3_1)
    ax.text(20, 39, "Form Inspection", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(20, 34, "Playwright Interception\nExtracts Field Schema\nDetects Custom Questions", ha='center', va='center', fontsize=7.5, color="#64748B")

    b3_2 = patches.FancyBboxPatch((38, 30), 24, 13, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b3_2)
    ax.text(50, 39, "Profile Mapping & Reuse", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(50, 34, "Auto-Populates Contacts\n'Answer Once' Bulk Sharing\nOpenRouter AI Assistance", ha='center', va='center', fontsize=7.5, color="#64748B")

    b3_3 = patches.FancyBboxPatch((68, 30), 24, 13, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#059669", linewidth=1.5)
    ax.add_patch(b3_3)
    ax.text(80, 39, "Candidate Review Screen", ha='center', va='center', fontsize=9, fontweight='bold', color="#059669")
    ax.text(80, 34, "Inline Field Overrides\nImmutable Snapshot Hashing\nCryptographic review_token", ha='center', va='center', fontsize=7.5, color="#0F172A")

    ax.annotate("", xy=(38, 36.5), xytext=(32, 36.5), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(68, 36.5), xytext=(62, 36.5), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(50, 24), xytext=(50, 27.5), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.8))

    # Lane 4: Guarded Execution & Tracking (Y: 3 to 24)
    lane4 = patches.FancyBboxPatch((5, 3), 90, 21, boxstyle="round,pad=0.8",
                                  facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
    ax.add_patch(lane4)
    ax.text(8, 21.5, "PHASE 4: GUARDED BROWSER AUTOMATION & CONFIRMATION",
            fontsize=9.5, fontweight='bold', color="#164E63")

    b4_1 = patches.FancyBboxPatch((8, 5.5), 24, 13, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b4_1)
    ax.text(20, 14.5, "Explicit Approval Gate", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(20, 9.5, "Applicant Confirms Token\n15-Minute Expiry Nonce\nZero Blind Submission", ha='center', va='center', fontsize=7.5, color="#64748B")

    b4_2 = patches.FancyBboxPatch((38, 5.5), 24, 13, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(b4_2)
    ax.text(50, 14.5, "Ashby Hosted v2 Adapter", ha='center', va='center', fontsize=9, fontweight='bold', color="#0F172A")
    ax.text(50, 9.5, "Form-State GraphQL RPCs\nSingle-Use JsonPermits\nChecksum Resume Upload", ha='center', va='center', fontsize=7.5, color="#64748B")

    b4_3 = patches.FancyBboxPatch((68, 5.5), 24, 13, boxstyle="round,pad=0.5",
                                 facecolor="#FFFFFF", edgecolor="#059669", linewidth=1.5)
    ax.add_patch(b4_3)
    ax.text(80, 14.5, "Verified Submission", ha='center', va='center', fontsize=9, fontweight='bold', color="#059669")
    ax.text(80, 9.5, "FormSubmitSuccess Receipt\nImmutable Event Ledger\nLive Application Tracker", ha='center', va='center', fontsize=7.5, color="#0F172A")

    ax.annotate("", xy=(38, 12), xytext=(32, 12), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))
    ax.annotate("", xy=(68, 12), xytext=(62, 12), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"System workflow diagram saved to {output_path}")


def create_matching_algorithm_diagram(output_path):
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Title
    t_box = patches.FancyBboxPatch((5, 92), 90, 5.5, boxstyle="round,pad=0.5", facecolor="#164E63", edgecolor="none")
    ax.add_patch(t_box)
    ax.text(50, 94.7, "TURIO: MULTI-STAGE HYBRID MATCHING & SCORING PIPELINE", ha='center', va='center', color='#FFFFFF', fontsize=12, fontweight='bold')

    # Candidate Branch (Left)
    c_box = patches.FancyBboxPatch((8, 76), 36, 12, boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor="#164E63", linewidth=1.5)
    ax.add_patch(c_box)
    ax.text(26, 84, "Candidate Profile Representation", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#164E63")
    ax.text(26, 79.5, "Skills (normalized) + Roles + Experiences +\nEducations + Projects (Up to 12,000 chars)\n(Excluded: Identity, Email, Phone)", ha='center', va='center', fontsize=7.5, color="#334155")

    # Job Branch (Right)
    j_box = patches.FancyBboxPatch((56, 76), 36, 12, boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor="#164E63", linewidth=1.5)
    ax.add_patch(j_box)
    ax.text(74, 84, "Job Posting Representation", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#164E63")
    ax.text(74, 79.5, "Job Title + Required Skills List +\nDescription (Up to 10,000 chars)\n(Excluded: Nonce, Scraped HTML tags)", ha='center', va='center', fontsize=7.5, color="#334155")

    # Middle Row: Encoders & Analyzers
    # 1. SBERT Dense Embeddings
    sbert_box = patches.FancyBboxPatch((8, 55), 26, 14, boxstyle="round,pad=0.5", facecolor="#FFFFFF", edgecolor="#D97706", linewidth=1.4)
    ax.add_patch(sbert_box)
    ax.text(21, 64, "Sentence-BERT (MiniLM-L6-v2)", ha='center', va='center', fontsize=8.5, fontweight='bold', color="#D97706")
    ax.text(21, 58.5, "Dense 384-Dim Vectors\nNormalized Cosine Similarity\nWeight: w_semantic = 0.45", ha='center', va='center', fontsize=7.2, color="#0F172A")

    # 2. Skill Jaccard Overlap
    skill_box = patches.FancyBboxPatch((37, 55), 26, 14, boxstyle="round,pad=0.5", facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.4)
    ax.add_patch(skill_box)
    ax.text(50, 64, "Structured Skill Overlap", ha='center', va='center', fontsize=8.5, fontweight='bold', color="#334155")
    ax.text(50, 58.5, "Matched / Required Skills\nExact Alias Normalization\nWeight: w_skill = 0.25", ha='center', va='center', fontsize=7.2, color="#0F172A")

    # 3. Experience & Meta Overlap
    meta_box = patches.FancyBboxPatch((66, 55), 26, 14, boxstyle="round,pad=0.5", facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.4)
    ax.add_patch(meta_box)
    ax.text(79, 64, "Experience & Preferences", ha='center', va='center', fontsize=8.5, fontweight='bold', color="#334155")
    ax.text(79, 58.5, "Non-Overlapping Tenure (0.10)\nPreferred Roles (0.10)\nLocation & Degree (0.10)", ha='center', va='center', fontsize=7.2, color="#0F172A")

    # Connectors from Top to Encoders
    ax.annotate("", xy=(21, 69), xytext=(26, 76), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(50, 69), xytext=(35, 76), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(50, 69), xytext=(65, 76), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(79, 69), xytext=(74, 76), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))

    # Weight Aggregator Box
    agg_box = patches.FancyBboxPatch((20, 31), 60, 16, boxstyle="round,pad=0.6", facecolor="#F1F5F9", edgecolor="#164E63", linewidth=1.8)
    ax.add_patch(agg_box)
    ax.text(50, 42.5, "Dynamic Weight Normalization & Aggregator", ha='center', va='center', fontsize=10, fontweight='bold', color="#164E63")
    ax.text(50, 36.5, "Final Score = (sum(w_i * S_i) / sum(w_active)) * 100\nTransparent Score: Missing requirements never penalize if unstated.\nAuto-generates matched_skills & missing_skills structured evidence.", ha='center', va='center', fontsize=7.8, color="#0F172A")

    ax.annotate("", xy=(35, 47), xytext=(21, 55), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(50, 47), xytext=(50, 55), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(65, 47), xytext=(79, 55), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))

    # Output Box
    out_box = patches.FancyBboxPatch((20, 8), 60, 15, boxstyle="round,pad=0.6", facecolor="#ECFDF5", edgecolor="#059669", linewidth=2)
    ax.add_patch(out_box)
    ax.text(50, 18.5, "Stored Job Match & Recommendation Output", ha='center', va='center', fontsize=10.5, fontweight='bold', color="#059669")
    ax.text(50, 12.5, "• Ranked Recommendations delivered to Candidate Dashboard\n• Complete explanation payload with breakdown (skills, experience, semantic)\n• Cached in PostgreSQL job_matches table via SHA-256 content hashes", ha='center', va='center', fontsize=8, color="#065F46")

    ax.annotate("", xy=(50, 23), xytext=(50, 31), arrowprops=dict(arrowstyle="->", color="#059669", lw=2))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Matching algorithm diagram saved to {output_path}")


def create_layout_parser_diagram(output_path):
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Title
    t_box = patches.FancyBboxPatch((5, 92), 90, 5.5, boxstyle="round,pad=0.5", facecolor="#164E63", edgecolor="none")
    ax.add_patch(t_box)
    ax.text(50, 94.7, "TURIO: LAYOUT-AWARE RESUME EXTRACTION ALGORITHM", ha='center', va='center', color='#FFFFFF', fontsize=12, fontweight='bold')

    steps = [
        ("Step 1: Word Bounding Box Extraction", 20, 78, "#334155", "pdfplumber extracts every word with coordinates: (x0, top, x1, bottom). Strict tolerances (x_tol=1, y_tol=3) prevent character drift."),
        ("Step 2: Line Clustering & Horizontal Gaps", 20, 60, "#334155", "Groups words with vertical distance <= 3pt into visual lines. Computes horizontal gutters (gap >= max(18, width * 0.03)) to identify column splits."),
        ("Step 3: Column Boundary & Heading Cut Analysis", 20, 42, "#D97706", "Distinguishes real columns from right-aligned dates. Both split sides must contain independent section headings (_section_for) and valid body items."),
        ("Step 4: Recursive Column Flow & Spanning Headers", 20, 24, "#164E63", "Processes spanning headers across columns (e.g. Name, Summary), then recursively orders column 1 before column 2 to eliminate multi-column interleaving."),
        ("Step 5: Semantic Entity Extraction & Profile DB", 20, 6, "#059669", "Regex extractors parse contact facts, dates, bulleted achievements, and degrees into typed Python entities; saves directly into PostgreSQL Profile.")
    ]

    for title, x, y, color, desc in steps:
        box = patches.FancyBboxPatch((x-12, y-6), 84, 12, boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor=color, linewidth=1.6)
        ax.add_patch(box)
        hbar = patches.FancyBboxPatch((x-12, y+2), 84, 4, boxstyle="round,pad=0.2", facecolor=color, edgecolor="none")
        ax.add_patch(hbar)
        ax.text(50, y+4, title, ha='center', va='center', color="#FFFFFF", fontsize=9, fontweight='bold')
        ax.text(50, y-2, desc, ha='center', va='center', color="#0F172A", fontsize=8)

    # Connecting arrows
    ax.annotate("", xy=(50, 72), xytext=(50, 66), arrowprops=dict(arrowstyle="<-", color="#164E63", lw=1.8))
    ax.annotate("", xy=(50, 54), xytext=(50, 48), arrowprops=dict(arrowstyle="<-", color="#164E63", lw=1.8))
    ax.annotate("", xy=(50, 36), xytext=(50, 30), arrowprops=dict(arrowstyle="<-", color="#164E63", lw=1.8))
    ax.annotate("", xy=(50, 18), xytext=(50, 12), arrowprops=dict(arrowstyle="<-", color="#059669", lw=1.8))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Layout parser diagram saved to {output_path}")


def create_fsm_diagram(output_path):
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Title Banner
    title_box = patches.FancyBboxPatch((5, 45), 90, 5, boxstyle="round,pad=0.5",
                                      facecolor="#164E63", edgecolor="none")
    ax.add_patch(title_box)
    ax.text(50, 47.5, "TURIO: FINITE STATE MACHINE (FSM) & ERROR RECOVERY LIFECYCLE",
            ha='center', va='center', color='#FFFFFF', fontsize=11.5, fontweight='bold')

    states = [
        ("CREATED", 10, 28, "#334155", "Draft created\nfor job ID"),
        ("PREPARING", 28, 28, "#334155", "Inspecting ATS\n& mapping profile"),
        ("NEEDS_INPUT", 46, 28, "#D97706", "Required fields\nlack confirmation"),
        ("READY_FOR_REVIEW", 64, 28, "#2563EB", "100% complete\nreview_token issued"),
        ("APPROVED", 82, 28, "#164E63", "User authorized\n15-min submission"),
        ("SUBMITTING", 82, 11, "#334155", "Executing guarded\nGraphQL RPCs"),
        ("SUBMITTED", 55, 11, "#059669", "Verified FormSubmitSuccess\nreceipt stored"),
        ("VERIFICATION_FAILED", 20, 11, "#DC2626", "Locked: unknown outcome\nManual reset required")
    ]

    for name, x, y, color, desc in states:
        box = patches.FancyBboxPatch((x-7, y-4.5), 14, 9, boxstyle="round,pad=0.4",
                                    facecolor="#FFFFFF", edgecolor=color, linewidth=1.6)
        ax.add_patch(box)
        hdr_bar = patches.FancyBboxPatch((x-7, y+1.5), 14, 3, boxstyle="round,pad=0.2",
                                        facecolor=color, edgecolor="none")
        ax.add_patch(hdr_bar)
        ax.text(x, y+3, name, ha='center', va='center', color="#FFFFFF", fontsize=7.2, fontweight='bold')
        ax.text(x, y-1.5, desc, ha='center', va='center', color="#0F172A", fontsize=6.8)

    # Transitions
    ax.annotate("", xy=(21, 28), xytext=(17, 28), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(39, 28), xytext=(35, 28), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(57, 28), xytext=(53, 28), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(75, 28), xytext=(71, 28), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(82, 15.5), xytext=(82, 23.5), arrowprops=dict(arrowstyle="->", color="#164E63", lw=1.4))
    ax.annotate("", xy=(62, 11), xytext=(75, 11), arrowprops=dict(arrowstyle="->", color="#059669", lw=1.6))
    ax.annotate("", xy=(27, 11), xytext=(48, 11), arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.6, ls="--"))

    # Reset transition
    ax.annotate("Employer-site acknowledgement & reset", xy=(46, 23.5), xytext=(20, 15.5),
                arrowprops=dict(arrowstyle="->", color="#64748B", lw=1.2, ls=":"),
                fontsize=7, color="#64748B", ha='center')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"FSM diagram saved to {output_path}")


if __name__ == "__main__":
    out_dir = r"D:\College\4-2 project\docs\images"
    os.makedirs(out_dir, exist_ok=True)
    create_system_workflow_diagram(os.path.join(out_dir, "workflow_architecture.png"))
    create_matching_algorithm_diagram(os.path.join(out_dir, "matching_algorithm.png"))
    create_layout_parser_diagram(os.path.join(out_dir, "layout_parser_algorithm.png"))
    create_fsm_diagram(os.path.join(out_dir, "fsm_lifecycle.png"))
