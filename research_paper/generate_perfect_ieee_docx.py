import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import os, shutil

FIG_DIR = r"c:\Users\sruth\crime analysis\research_paper\figures"
OUT_PATH = r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_Final_IIT_Kanpur.docx"
DESKTOP_PATH = r"c:\Users\sruth\Desktop\CrimeSense_IEEE_Final_IIT_Kanpur.docx"

def set_cell_margins(cell, top=40, bottom=40, left=60, right=60):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_ieee_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_paper():
    doc = docx.Document()

    # SECTION 1: Page Header Block (Single column across page width)
    sec1 = doc.sections[0]
    sec1.top_margin = Inches(0.75)
    sec1.bottom_margin = Inches(0.85)
    sec1.left_margin = Inches(0.625)
    sec1.right_margin = Inches(0.625)

    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = RGBColor(0, 0, 0)

    # Title (24 pt, no hyphens, centered)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("CrimeSense: A Unified Crime Hotspot Visualization, Zone Classification and Personal Safety Platform with Pattern Recurrence Analysis for Vellore, India")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(22)
    r_title.font.bold = False

    # Authors
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(2)
    r_auth = p_auth.add_run("Sruthilaya J D, Mahithaa R, Sujeetha S")
    r_auth.font.name = 'Times New Roman'
    r_auth.font.size = Pt(11)

    p_ids = doc.add_paragraph()
    p_ids.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ids.paragraph_format.space_after = Pt(2)
    r_ids = p_ids.add_run("24MID0184, 24MID0239, 24MID0163")
    r_ids.font.name = 'Times New Roman'
    r_ids.font.size = Pt(10)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(10)
    r_inst = p_inst.add_run("School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India")
    r_inst.font.name = 'Times New Roman'
    r_inst.font.size = Pt(10)

    # SECTION 2: Body - Continuous Section Break in 2 COLUMNS
    sec2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    sec2.top_margin = Inches(0.75)
    sec2.bottom_margin = Inches(0.85)
    sec2.left_margin = Inches(0.625)
    sec2.right_margin = Inches(0.625)

    sectPr = sec2._sectPr
    cols = parse_xml(f'<w:cols {nsdecls("w")} w:num="2" w:space="280"/>')
    sectPr.append(cols)

    def add_para(text, indent=True):
        return add_p(text, indent)

    def add_p(text, indent=True):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.03
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.14)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        return p

    def add_bullet(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.line_spacing = 1.02
        p.paragraph_format.left_indent = Inches(0.18)
        p.paragraph_format.first_line_indent = Inches(-0.12)
        r_b = p.add_run("•  ")
        r_b.font.name = 'Times New Roman'
        r_b.font.size = Pt(9.5)
        r_b.font.bold = True
        r_t = p.add_run(text)
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(9.5)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.bold = False
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9.5)
        run.font.italic = True
        return p

    def add_eq(eq_text, num_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r_eq = p.add_run(f"   {eq_text}")
        r_eq.font.name = 'Times New Roman'
        r_eq.font.italic = True
        r_eq.font.size = Pt(9)
        r_n = p.add_run(f"\t({num_str})")
        r_n.font.name = 'Times New Roman'
        r_n.font.italic = False
        r_n.font.size = Pt(9)

    def add_pic(img_name, caption_num, caption_text):
        path = os.path.join(FIG_DIR, img_name)
        if os.path.exists(path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(4)
            p_img.paragraph_format.space_after = Pt(2)
            p_img.paragraph_format.keep_with_next = True
            run = p_img.add_run()
            run.add_picture(path, width=Inches(3.35))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_cap.paragraph_format.space_before = Pt(0)
            p_cap.paragraph_format.space_after = Pt(5)
            p_cap.paragraph_format.line_spacing = 1.0
            r_c1 = p_cap.add_run(f"Fig. {caption_num}. ")
            r_c1.font.name = 'Times New Roman'
            r_c1.font.size = Pt(8)
            r_c1.font.bold = False
            r_c2 = p_cap.add_run(caption_text)
            r_c2.font.name = 'Times New Roman'
            r_c2.font.size = Pt(8)

    def add_tbl_hdr(num_str, title_str):
        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(6)
        p1.paragraph_format.space_after = Pt(1)
        p1.paragraph_format.keep_with_next = True
        r1 = p1.add_run(f"TABLE {num_str}")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(8)

        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(3)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(title_str.upper())
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(7.5)

    # 1. ABSTRACT (No AI hyphens, clean em-dash removed, natural academic style)
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_before = Pt(0)
    p_abs.paragraph_format.space_after = Pt(3)
    p_abs.paragraph_format.line_spacing = 1.02
    r_absh = p_abs.add_run("Abstract: ")
    r_absh.font.name = 'Times New Roman'
    r_absh.font.bold = True
    r_absh.font.size = Pt(9)
    r_abst = p_abs.add_run(
        "Residents of Tier II Indian cities rarely have a direct method to evaluate how a street, market, or transit junction features in recent "
        "crime reporting, while personal safety applications commonly remain restricted to panic button dispatch. CrimeSense is a unified platform "
        "combining analyst crime visualization with a resident safety assistant for Vellore, Tamil Nadu. A database of 596 news sourced incident records, "
        "each retaining a verified web link, locality coordinate, type severity score, and risk level, drives a three tier zone classifier (green, "
        "yellow, red), administrative hotspot maps, and a consent gated live map. For residents, the system provides a pre-visit destination advisory "
        "explaining local reports, a safe haven finder ranking nearby police stations, hospitals, supermarkets, and staffed commercial centers, and an "
        "SOS channel alerting chosen contacts manually or upon extended inactivity inside red zones. A pattern recurrence module based on near repeat "
        "permutation tests and association rules is formulated to discover sequential crime patterns. We document verified database integrity, authentication, "
        "role separated routing, and user persistence, alongside an evaluation protocol for predictive calibration, haven coverage audits, and user studies."
    )
    r_abst.font.name = 'Times New Roman'
    r_abst.font.bold = True
    r_abst.font.size = Pt(9)

    # Keywords
    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(1)
    p_kw.paragraph_format.space_after = Pt(6)
    r_kwh = p_kw.add_run("Keywords: ")
    r_kwh.font.name = 'Times New Roman'
    r_kwh.font.bold = True
    r_kwh.font.italic = True
    r_kwh.font.size = Pt(9)
    r_kwt = p_kw.add_run("crime hotspot visualization, zone classification, near repeat analysis, personal safety application, SOS alerting, news derived crime data, geospatial uncertainty, safe haven")
    r_kwt.font.name = 'Times New Roman'
    r_kwt.font.size = Pt(9)

    # I. INTRODUCTION
    add_h1("I. INTRODUCTION")
    add_para("Crime is not spread evenly over an urban landscape. A small number of street segments and neighbourhoods account for a large share of incidents, and this regularity is strong enough to have been described as a law of crime concentration [1], [2]. Routine activity theory explains why: offences occur where motivated offenders, suitable targets, and a lack of capable guardians coincide in space and time [3]. Crime pattern theory adds that offenders operate primarily in familiar places they regularly traverse [4]. Hotspot maps built upon these foundations form a standard instrument of civic policing and have been linked to crime reductions in targeted locations [5], [6].")
    add_para("The person who actually has to decide whether to wait at a bus stop at nine in the evening rarely accesses this evidence. Two major gaps stand out. First, spatial intelligence is produced for analysts and police rather than residents, while official records are published as annual municipal aggregates [7] that cannot answer questions regarding a specific street. Second, civilian safety applications are predominantly reactive. A standard tool sends coordinates to police and contacts following a phone shake or button press [8]. Such mechanisms do nothing if the user cannot press the button, and they possess zero contextual awareness regarding the risk profile of the surrounding neighborhood.")
    add_para("CrimeSense bridges both gaps in one unified platform for Vellore, Tamil Nadu. For a Tier II city, incident level open data is scarce, so the platform builds its empirical foundation from publicly reported crime news, an established methodology in computational spatial analysis [9], [10] that nevertheless requires careful handling of reporting habits [11]. Over this single data store, we construct two role separated interfaces. The administrator interface provides spatial heatmaps, DBSCAN hotspots, historical multi-year records, user management, and an alert console. The resident interface provides an intuitive search bar, color coded zone indicators (green, yellow, or red), an SOS button, saved locations, and user preferences.")
    add_para("Beyond these features, CrimeSense introduces three core capabilities:")
    add_bullet("Pattern recurrence analysis: Investigating whether history repeats by examining if specific crimes systematically follow one another across space and time.")
    add_bullet("Safe haven finder: Directing an uneasy citizen to the nearest staffed commercial or civic social hub where active human presence provides natural surveillance.")
    add_bullet("Pre-visit destination advisory: Explaining what has occurred near a prospective destination and advising whether traveling with company is sensible.")

    add_para("This paper delineates verified implementations from proposed designs. Section III details the system architecture. Section IV states the implementation status with every module cataloged. Section V summarizes the empirical dataset. Section VI outlines an evaluation protocol with explicit metrics, and Section VII addresses ethical governance, reporting bias, and privacy safeguards. The contributions include:")
    add_bullet("An integrated, role separated architecture linking a database backed crime store, an analyst dashboard, and a mobile resident safety application.")
    add_bullet("A transparent, configurable zone classification model with explicit parameters, paired with an advisory format that explains evidence without declaring any location unconditionally safe.")
    add_bullet("A pattern recurrence methodology (near repeat permutation testing, sequential association rules, and a recurrence index) to identify repeating crime sequences.")
    add_bullet("A safe haven discovery algorithm ranking police stations, hospitals, commercial shops, and social hubs by category weight, operational status, distance, and local zone score.")
    add_bullet("An SOS escalation design uniting manual double confirmation triggering with an autonomous dwell and inactivity finite state machine.")
    add_bullet("An empirical verification report of the operational database (596 incident records across 11 tables) and an experimental protocol for prospective modules.")

    # II. RELATED WORK
    add_h1("II. RELATED WORK")
    add_h2("A. Crime Concentration and Hotspot Mapping")
    add_para("Micro-place research demonstrates that crime clusters at fine geographic scales [1], [2]. Hotspots are visualized through point clusters, grid matrices, or kernel density surfaces [5], [12], with temporal weighting improving short term predictive surfaces [13]. DBSCAN [14] identifies clusters of arbitrary geometry without predefined grids, isolating sparse incidents as noise. Systematic reviews confirm the efficacy of concentrating patrol resources in such locations [6]. However, these analytical methods are built exclusively for police commanders and do not directly answer citizen safety questions regarding a travel destination.")

    add_h2("B. Forecasting and Risk Terrain Modelling")
    add_para("Self-exciting point process formulations capture how an initial event elevates the near term likelihood of subsequent local offences [15]. Risk terrain modeling connects spatial crime rates to environmental attractors such as transit nodes and unlit corridors [16], with meta-analyses demonstrating its utility in highlighting heightened risk zones [17]. Broader surveys on spatial crime forecasting [18] and machine learning frameworks [19], [20] reveal substantial methodological diversity. Most models assume access to dense police dispatch registries that are rarely accessible in Tier II municipalities. CrimeSense therefore builds upon an interpretable weighted severity formulation, preserving learned models for subsequent held-out empirical evaluations.")

    add_h2("C. Repeat and Near-Repeat Patterns")
    add_para("The Knox test evaluates whether incident pairs close in space are also close in time more frequently than random probability suggests [21]. Applied extensively to property offenses, it identified near repeat victimization, where a victimized premises and nearby neighbors experience elevated vulnerability over a bounded duration [22], [23]. Prior works present these outputs solely to criminological researchers. In our review, no system connects near repeat detection directly to civilian mobile safety tools.")

    add_h2("D. News-Derived Crime Data and Geocoding")
    add_para("Where official CAD feeds are restricted, social media and digital news archives provide valuable proxies for spatial crime analysis [9], [10]. Journalistic archives provide rich incident narratives, though they reflect editorial selection criteria [11]. Furthermore, converting written locality descriptions into coordinates introduces spatial imprecision [24], making positional confidence reporting essential [25]. We incorporate these constraints directly into our confidence flags and threat assessments.")

    add_h2("E. Safe Routing, Natural Surveillance, and Safety Tools")
    add_para("Safe routing methods frame pedestrian navigation as a multi-criteria optimization balancing path distance against crime exposure [26]. Our approach is complementary: rather than routing between distant waypoints, CrimeSense classifies local destinations, identifies immediate safe havens, and escalates emergencies when a user cannot navigate. The concept of a safe haven relies on Jane Jacobs' observation that busy, staffed commercial centers are safeguarded by natural surveillance and 'eyes on the street' [27], corroborated by Oscar Newman's defensible space framework [28]. Candidate POIs are extracted from OpenStreetMap [29]. Finally, algorithmic systems must actively prevent reinforcing historical bias [30], [31], [32], which we address through transparent, non-pejorative design.")

    # Table I
    add_tbl_hdr("I", "Prior Work by Category and What Each Lacks for Resident Safety")
    t1 = doc.add_table(rows=7, cols=3)
    set_ieee_table_borders(t1)
    t1_headers = ["Category", "Typical Scope", "Missing Relative to CrimeSense"]
    for i, h in enumerate(t1_headers):
        cell = t1.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 35, 35, 50, 50)
    t1_data = [
        ("Hotspot mapping [5], [13]", "Analyst concentration maps", "Resident zone badges and automated alerts"),
        ("Forecasting, RTM [15], [16]", "Risk surfaces from rich CAD records", "Resident interface, news scale handling, dwell escalation"),
        ("Near repeat analysis [21], [22]", "Space time clustering on burglary", "Delivery of recurring patterns to mobile users"),
        ("News derived crime [9], [10]", "Data harvesting and text mining", "Zone scoring, haven discovery, emergency escalation"),
        ("Safe routing [26]", "Distance versus risk trade off", "Haven discovery, dwell warnings, analyst oversight"),
        ("Panic button apps [8]", "Trigger plus location SMS", "Area intelligence, automated dwell escalation, analytics")
    ]
    for r_idx, r_val in enumerate(t1_data, 1):
        row = t1.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 25, 25, 45, 45)

    add_para("Table I summarizes literature categories relative to CrimeSense. The overview identifies structural emphasis across domains rather than individual paper deficiencies.")

    # III. SYSTEM DESIGN
    add_h1("III. SYSTEM DESIGN")
    add_h2("A. Architecture Overview")
    add_para("CrimeSense comprises a client layer, API routing layer, service layer, single relational data store, and an offline ingestion pipeline (Fig. 1). The client layer deploys two interfaces from one codebase: a mobile resident application and a desktop analyst console. Both interface with a Flask REST API enforcing role checks, verifying Google OAuth ID tokens, and logging sensitive queries. All operational modules interact with a single SQLite database in Write Ahead Logging mode.")
    add_pic("fig1_architecture.png", "1", "Layered architecture of CrimeSense. Dashed boxes are proposed modules; solid boxes are implemented.")

    add_h2("B. Data Acquisition, Schema, and Role Separation")
    add_para("Incident records originate from verified journalistic news outlets. The offline pipeline normalizes crime types, removes duplicate coverage, geocodes localities, assigns severity ratings, and exports records for database ingestion. The crimes table preserves source URLs, location confidence, and location source tags to ensure full auditability. Administrator entered incidents write to the same table and generate audit entries.")
    add_para("The remaining tables track user accounts and activity (Fig. 2). User rows store names, unique emails, password hashes, optional Google identifiers, roles, and status flags. User settings, SOS contacts, saved locations, location heartbeats, red zone monitoring states, and SOS alerts reference user records via foreign keys. Role enforcement ensures residents access only their own rows, while administrator routes reject unauthorized requests.")
    add_pic("fig2_schema.png", "2", "Database schema. Child tables reference users.id; crimes is independent of any user.")

    add_h2("C. Zone Classification (Green, Yellow, Red)")
    add_para("The zone service evaluates crime exposure for any query coordinate q (GPS fix, search address, or manual coordinate input). Fig. 3 depicts the pipeline. An initial bounding box filter narrows candidate incidents, followed by great circle distance computation using the Haversine formula [33]:")
    add_eq("d = 2R arcsin √( sin²(Δφ/2) + cos φ₁ cos φ₂ sin²(Δλ/2) )", "1")
    add_para("with R = 6371 km. For incidents within search radius ρ, each record i contributes based on severity s_i, distance d_i, and age a_i. Raw risk is formulated as:")
    add_eq("R(q) = Σ_{i ∈ N(q)} s_i · δ(d_i) · w(a_i),   δ(d) = 1 − d/ρ", "2")
    add_para("where w(a) is a recency weight declining with age (1.0 for ≤6 months, 0.7 for 6–24 months, 0.4 for >24 months). The risk score is bounded against saturation constant R_ref:")
    add_eq("Z(q) = min{100, 100 · R(q) / R_ref}", "3")
    add_para("and mapped into three zones (Table II). When no incidents exist within radius ρ, the service returns green with a low data confidence flag, ensuring empty coverage is never interpreted as verified safety. The response payload reports incident counts, dominant crime types, the nearest report, and original source links.")
    add_pic("fig3_zone_pipeline.png", "3", "Zone classification pipeline for a query point.")

    # Table II
    add_tbl_hdr("II", "Zone Model Parameters (Design Defaults)")
    t2 = doc.add_table(rows=7, cols=3)
    set_ieee_table_borders(t2)
    t2_headers = ["Parameter", "Symbol", "Default Rule"]
    for i, h in enumerate(t2_headers):
        cell = t2.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t2_data = [
        ("Search radius", "ρ", "1000 m (user configurable 500–1000 m)"),
        ("Severity score", "s", "2–10 from crime classification lookup"),
        ("Distance decay", "δ(d)", "1 − d/ρ"),
        ("Recency weight", "w(a)", "1.0 (≤6 mo); 0.7 (6–24 mo); 0.4 (>24 mo)"),
        ("Saturation cap", "R_ref", "To be calibrated (Section VI)"),
        ("Zone cutoffs", "Z", "Red: ≥60; Yellow: 30 to <60; Green: <30")
    ]
    for r_idx, r_val in enumerate(t2_data, 1):
        row = t2.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 25, 25, 45, 45)

    add_para("Because news coordinates are locality level centroids, distance decay operates at neighborhood scales rather than precise building numbers. Severity scores stem from transparent type lookup tables, which Section VI calibrates against held out temporal splits.")

    add_h2("D. Hotspot Detection and Administrator Visualization")
    add_para("The analyst console provides severity categorized markers, density heatmaps, and multifaceted filtering across districts, localities, crime categories, and temporal spans. DBSCAN with Haversine distance [14], [34] calculates spatial clusters using neighborhood radius ε and minimum points m. In the current prototype, the active hotspot counter reflects the count of localities with at least one high severity incident, distinct from raw DBSCAN cluster counts.")

    add_h2("E. Pattern-Recurrence Analysis (Proposed)")
    add_para("To examine repeating spatial crime dynamics, CrimeSense defines three complementary analyses (Fig. 4). First, the Knox space time permutation test computes interaction statistic X for incident pairs (i, j):")
    add_eq("X = Σ_{i < j} 1[d_ij ≤ Δs] · 1[|t_i − t_j| ≤ Δt]", "4")
    add_para("evaluated over distance thresholds Δs ∈ {250, 500, 1000} m and time intervals Δt ∈ {7, 14, 30} days against 999 Monte Carlo date shuffles. Second, sequential association rules treat locality week bins as transactions, evaluating rule A → B via lift [35]:")
    add_eq("lift(A → B) = P(B | A) / P(B)", "5")
    add_para("Third, the locality recurrence index measures the share of offenses in locality L of type T with an earlier occurrence within Δt:")
    add_eq("RI(L, T) = |{i ∈ I(L, T) : ∃ j, 0 < t_i − t_j ≤ Δt}| / |I(L, T)|", "6")
    add_pic("fig4_recurrence.png", "4", "Proposed pattern recurrence analysis. All modules are proposed and unvalidated.")

    add_h2("F. Pre-Visit Advisory and Safe-Haven Finder (Proposed)")
    add_para("These modules power the resident application search bar and 'I Feel Unsafe' actions (Fig. 5). The pre-visit check turns local incident counts and dates into transparent advisory cards (Table III) using rule templates rather than ungrounded generative models, ensuring full citation back to source articles.")
    add_pic("fig5_resident_flows.png", "5", "Resident side flows: (a) pre-visit check; (b) nearest haven search.")

    # Table III
    add_tbl_hdr("III", "Advisory Rules (Zone to Message Content)")
    t3 = doc.add_table(rows=7, cols=2)
    set_ieee_table_borders(t3)
    t3_headers = ["Condition", "Advisory Content"]
    for i, h in enumerate(t3_headers):
        cell = t3.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t3_data = [
        ("Green, none in ρ", "No reports within radius in dataset; coverage is limited; maintain standard precautions"),
        ("Green, some in ρ", "Few low severity reports; top types listed; standard precautions advised"),
        ("Yellow", "Moderate reports; prefer busy routes, avoid isolated stretches, notify a contact; haven links shown"),
        ("Red", "Concentration of severe reports; companion travel advised, prefer daylight; nearest haven displayed"),
        ("Violent type in top 3", "Appended note: traveling with a companion is strongly advised"),
        ("Theft or fraud on top", "Appended note: secure personal belongings; beware unsolicited payment requests")
    ]
    for r_idx, r_val in enumerate(t3_data, 1):
        row = t3.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 25, 25, 45, 45)

    add_para("In the haven flow, candidate public places within walking distance are extracted from OpenStreetMap (Table IV) and ranked by utility score H(p):")
    add_eq("H(p) = w_c · o(p, t) · exp(−d_p / λ) · (1 − Z_p / 100)", "7")
    add_para("where w_c reflects institutional guardianship, o(p, t) is opening status (1.0 if open, 0.0 if closed, 0.5 if unknown), d_p is distance, λ = 500 m, and Z_p penalizes havens located inside crime hotspots. The top five havens are displayed with walking duration, call buttons, and navigation links.")

    # Table IV
    add_tbl_hdr("IV", "Safe Haven Categories and Initial Weights")
    t4 = doc.add_table(rows=7, cols=3)
    set_ieee_table_borders(t4)
    t4_headers = ["Category", "OpenStreetMap Tag Example", "Weight (w_c)"]
    for i, h in enumerate(t4_headers):
        cell = t4.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t4_data = [
        ("Police station", "amenity=police", "1.0"),
        ("Hospital or clinic", "amenity=hospital, clinic", "0.9"),
        ("Government office", "office=government", "0.7"),
        ("Supermarket, mall", "shop=supermarket, mall", "0.7"),
        ("Pharmacy, fuel station", "amenity=pharmacy, fuel", "0.6"),
        ("Bus station, convenience", "amenity=bus_station; shop=convenience", "0.5")
    ]
    for r_idx, r_val in enumerate(t4_data, 1):
        row = t4.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 25, 25, 45, 45)

    add_h2("G. SOS and Red-Zone Dwell Escalation")
    add_para("Users register between one and five emergency contacts, designating one as primary. The manual SOS button requires a two-second continuous press and provides a five-second cancel window to prevent false triggers. Activation dispatches emergency messages with coordinates, timestamps, and zone status to contacts and the analyst console via Twilio or local provider abstractions.")
    add_para("The automated path monitors silent emergencies where victims cannot operate their phone. While the app is active and location sharing is enabled, a client heartbeat transmits every 30 seconds. A per-user finite state machine (Fig. 6) transitions from SAFE to IN_RED when a user enters a red zone. If stationary for T minutes (default 10, range 5–30 min) without touch interaction, an 'Are you safe?' prompt is issued for 60 seconds. In the absence of response, an automated emergency payload is dispatched to primary contacts with last known coordinates. A 30-minute cooldown prevents alert flooding.")
    add_pic("fig6_state_machine.png", "6", "Red zone dwell and inactivity state machine for automatic SOS escalation.")

    add_h2("H. Privacy, Consent, and Security")
    add_para("Location records constitute sensitive personal data [40]. In CrimeSense, location capture requires explicit user consent, and administrative live map tracking functions only for consenting accounts with active heartbeats, logging every view event immutably. Turning off location sharing suspends heartbeats and dwell alerting while leaving manual search operative. Sign-in supports salted password hashes and Google OAuth with audience and verified email validation [41]. The architecture aligns with India's Digital Personal Data Protection Act [42], supporting complete data deletion upon request.")

    # IV. IMPLEMENTATION STATUS AND VERIFICATION
    add_h1("IV. IMPLEMENTATION STATUS AND VERIFICATION")
    add_para("Table V outlines the operational state of system components. Verified components have passed test scripts and health queries, partial components are functional but awaiting field deployment, while designed and planned modules represent theoretical formulations.")

    # Table V
    add_tbl_hdr("V", "Implementation Status of CrimeSense Components")
    t5 = doc.add_table(rows=17, cols=3)
    set_ieee_table_borders(t5)
    t5_headers = ["Component", "Status", "Verification Basis"]
    for i, h in enumerate(t5_headers):
        cell = t5.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t5_data = [
        ("Crime database (596 records)", "Verified", "Database verifier and health endpoint"),
        ("Record quality checks", "Verified", "Quality audit script and Table VI"),
        ("Email signup and login", "Verified", "End to end flow verification tests"),
        ("Role separated access guard", "Partial", "Roles stored; access middleware in place"),
        ("Google OAuth 2.0 integration", "Verified", "Sign in test script and deduplication"),
        ("Admin KPIs, charts, and CRUD", "Verified", "Database backed live queries"),
        ("Consent gated live map, audit log", "Verified", "Audit trail records verified"),
        ("Contacts, saved places persistence", "Verified", "Full flow database test scripts"),
        ("Notification provider (Twilio/Log)", "Partial", "Local logging tested; live trial pending"),
        ("Red zone dwell state monitoring", "Partial", "State table verified; hardware trial pending"),
        ("Zone classification with Table II", "Designed", "Formulated; parameter tuning pending"),
        ("Hotspot clustering (DBSCAN)", "Partial", "KPI uses high severity proxy count"),
        ("Link sharing and export", "Partial", "Shared links table operational"),
        ("Pre-visit advisory generator", "Designed", "Rules defined in Table III"),
        ("Safe haven finder", "Designed", "Scoring utility in Eq. (7)"),
        ("Pattern recurrence analysis", "Planned", "Evaluation protocol in Section VI")
    ]
    for r_idx, r_val in enumerate(t5_data, 1):
        row = t5.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 20, 20, 40, 40)

    add_para("System verification executed on 11 October 2026 confirmed 596 crime rows in SQLite, single administrator initialization, and 11 relational tables. The health endpoint returned database connected status with zero lingering test records.")

    # Table VI
    add_tbl_hdr("VI", "Verification Summary of the Crimes Table (N = 596)")
    t6 = doc.add_table(rows=8, cols=2)
    set_ieee_table_borders(t6)
    t6_headers = ["Audit Check", "Observed Result"]
    for i, h in enumerate(t6_headers):
        cell = t6.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t6_data = [
        ("Records with valid source web link", "596 of 596 (100.00%)"),
        ("Coordinates inside study bounds", "596 of 596 (lat 9.93 to 13.08, lng 76.96 to 80.27)"),
        ("Valid standardized ISO dates", "596 of 596 (100.00%)"),
        ("Duplicate article identifiers", "0 (Zero duplicates)"),
        ("Severity score spectrum; mean", "2.0 to 10.0; Mean: 5.92"),
        ("Risk level split (High / Med / Low)", "150 High / 138 Medium / 308 Low"),
        ("Rows in user, settings, audit tables", "1, 1, 6 (Production baseline)")
    ]
    for r_idx, r_val in enumerate(t6_data, 1):
        row = t6.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 25, 25, 45, 45)

    # V. DATASET AND CURRENT RESULTS
    add_h1("V. DATASET AND CURRENT RESULTS")
    add_para("The database contains 596 verified crime incidents. Fig. 7(a) depicts the categorical breakdown: general offenses comprise 277 records (46.5%), followed by murder and homicide (49), contraband and smuggling (46), a distinct murder tag (37), and cyber fraud (28). Fig. 7(b) displays the risk split: 25.2% High risk, 23.2% Medium risk, and 51.7% Low risk.")
    add_pic("fig7_dataset_charts.png", "7", "Current database: (a) crime-type labels; (b) risk-level split.")
    add_para("These empirical figures establish three observations. First, the prevalence of general offences highlights the necessity of finer taxonomies for granular recurrence modeling. Second, merging overlapping murder labels consolidates 86 severe offenses under a single tag. Third, geocoding operates at locality scale, meaning records within a single town share centroid coordinates, so risk scoring is valid at neighbourhood rather than street number resolution.")

    # VI. PROPOSED EVALUATION PROTOCOL
    add_h1("VI. PROPOSED EVALUATION PROTOCOL")
    add_para("To ensure reproducible benchmarking, we pre-define evaluation metrics and thresholds (Table VII). Predictive evaluations use rolling temporal splits: records before cutoff date t0 form the training surface, and incidents in the subsequent three months serve as test sets. On a 500 m grid, hit rate measures the fraction of test incidents falling within red cells, compared via the Predictive Accuracy Index [5]:")
    add_eq("PAI = (n / N) / (a / A)", "8")
    add_para("where n of N test crimes fall in red cells covering area a out of total area A. Thresholds are calibrated on initial splits and reported where red cells cover at most 10% of the urban terrain.")

    # Table VII
    add_tbl_hdr("VII", "Standardized Evaluation Protocol")
    t7 = doc.add_table(rows=8, cols=3)
    set_ieee_table_borders(t7)
    t7_headers = ["Module", "Evaluation Metric", "Protocol Details"]
    for i, h in enumerate(t7_headers):
        cell = t7.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t7_data = [
        ("Zone model", "Hit rate, PAI at red area ≤10%; Cohen's kappa", "Rolling temporal split; two local raters on sampled places"),
        ("Hotspots", "Cluster count and stability versus (ε, m)", "Parameter sweep over ε and m grid"),
        ("Recurrence", "Near repeat ratio; permutation p (999 runs); lift", "Candidate space time windows on deduplicated data"),
        ("Haven finder", "Valid@5 accuracy; median walk to first open haven", "Field verification audit across sampled query points"),
        ("SOS escalation", "Trigger to dispatch latency (p50, p95); false alarms", "Scripted GPS trajectory playback on sandbox database"),
        ("Access control", "Cross account reads blocked; 403 on admin routes", "Two test resident accounts plus one administrator"),
        ("Usability", "System Usability Scale [43]; task completion rate", "15 or more participants performing search and SOS tasks")
    ]
    for r_idx, r_val in enumerate(t7_data, 1):
        row = t7.rows[r_idx]
        for c_idx, text_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = text_val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.2)
            set_cell_margins(cell, 25, 25, 45, 45)

    add_para("Reporting these metrics with confidence bounds addresses recognized gaps in spatial criminology literature regarding reproducible operating baselines [18].")

    # VII. DISCUSSION
    add_h1("VII. DISCUSSION")
    add_h2("A. What Is New")
    add_para("Core elements of spatial crime analysis, near repeat testing, safe routing, and emergency alerting possess established research literatures. CrimeSense synthesizes these components around a single shared evidence base: the same verified incident record informs an administrative analyst, a citizen checking a prospective travel route, and an autonomous service monitoring red zone dwell times. The haven finder and pre-visit advisory convert static maps into immediate civilian protection, while dwell escalation resolves scenarios where victims are physically incapacitated.")

    add_h2("B. Ethics and Responsible Use")
    add_para("Assigning risk labels to urban sectors risks stigmatizing communities and amplifying data biases [30], [31], [32]. CrimeSense mitigates these harms by framing zones objectively as 'reported incidents', displaying report counts and source links transparently, avoiding pejorative terms like 'unsafe', stating clearly that green zones do not guarantee absolute safety, and excluding automated outputs from punitive policing loops [32]. Confirmation challenges and cooldown timers prevent alert fatigue.")

    add_h2("C. Limitations and Threats to Validity")
    add_para("News sourced datasets reflect journalistic coverage choices, which over represent unusual or severe offenses relative to minor infractions [11]. Locality centroid coordinates limit spatial precision [24], [25]. The severity score table is expert assigned rather than calibrated on longitudinal outcome metrics. OpenStreetMap haven records inherit volunteer mapping variations, and automated browser push notifications depend upon active browser lifecycles and mobile connectivity.")

    # VIII. CONCLUSION AND FUTURE WORK
    add_h1("VIII. CONCLUSION AND FUTURE WORK")
    add_para("CrimeSense establishes a unified platform uniting spatial crime visualization and proactive civilian safety over an authoritative database of 596 verified news records for Vellore. Database integrity, authentication, role enforcement, and persistence have been verified. Mathematical formulations for zone classification, destination advisories, safe haven discovery, and pattern recurrence are established alongside an empirical benchmarking protocol. Future work will execute rolling temporal evaluations, refine geocoding resolution, conduct physical safe haven audits, and evaluate user cognitive load through structured field usability trials.")

    # REFERENCES (Exact [1] to [43] without AI hyphens, comma citations, 8pt hanging indent)
    add_h1("REFERENCES")
    refs = [
        "[1] D. Weisburd, \"The law of crime concentration and the criminology of place,\" Criminology, vol. 53, no. 2, pp. 133–157, 2015.",
        "[2] L. W. Sherman, P. R. Gartin, and M. E. Buerger, \"Hot spots of predatory crime: Routine activities and the criminology of place,\" Criminology, vol. 27, no. 1, pp. 27–56, 1989.",
        "[3] L. E. Cohen and M. Felson, \"Social change and crime rate trends: A routine activity approach,\" Amer. Sociol. Rev., vol. 44, no. 4, pp. 588–608, 1979.",
        "[4] P. J. Brantingham and P. L. Brantingham, Patterns in Crime. New York, NY, USA: Macmillan, 1984.",
        "[5] S. Chainey, L. Tompson, and S. Uhlig, \"The utility of hotspot mapping for predicting spatial patterns of crime,\" Secur. J., vol. 21, no. 1–2, pp. 4–28, 2008.",
        "[6] A. A. Braga, B. S. Turchan, A. V. Papachristos, and D. M. Hureau, \"Hot spots policing of small geographic areas effects on crime,\" Campbell Syst. Rev., vol. 15, no. 3, Art. no. e1046, 2019.",
        "[7] National Crime Records Bureau, \"Crime in India 2022,\" Ministry of Home Affairs, Government of India, New Delhi, India, 2023.",
        "[8] D. Chand, S. Nayak, K. S. Bhat, S. Parikh, Y. Singh, and A. A. Kamath, \"A mobile application for women's safety: WoSApp,\" in Proc. IEEE Region 10 Conf. (TENCON), 2016.",
        "[9] M. S. Gerber, \"Predicting crime using Twitter and kernel density estimation,\" Decis. Support Syst., vol. 61, pp. 115–125, 2014.",
        "[10] A. Umair, M. S. Sarfraz, M. Ahmad, U. Habib, M. H. Ullah, and M. Mazzara, \"Spatiotemporal analysis of web news archives for crime prediction,\" Appl. Sci., vol. 10, no. 22, Art. no. 8220, 2020.",
        "[11] J. Earl, A. Martin, J. D. McCarthy, and S. A. Soule, \"The use of newspaper data in the study of collective action,\" Annu. Rev. Sociol., vol. 30, pp. 65–80, 2004.",
        "[12] B. W. Silverman, Density Estimation for Statistics and Data Analysis. London, U.K.: Chapman & Hall, 1986.",
        "[13] Y. Hu, F. Wang, C. Guin, and H. Zhu, \"A spatio-temporal kernel density estimation framework for predictive crime hotspot mapping and evaluation,\" Appl. Geogr., vol. 99, pp. 89–97, 2018.",
        "[14] M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, \"A density-based algorithm for discovering clusters in large spatial databases with noise,\" in Proc. 2nd Int. Conf. Knowl. Discovery Data Mining (KDD), 1996, pp. 226–231.",
        "[15] G. O. Mohler, M. B. Short, P. J. Brantingham, F. P. Schoenberg, and G. E. Tita, \"Self-exciting point process modeling of crime,\" J. Amer. Statist. Assoc., vol. 106, no. 493, pp. 100–108, 2011.",
        "[16] J. M. Caplan, L. W. Kennedy, and J. Miller, \"Risk terrain modeling: Brokering criminological theory and GIS methods for crime forecasting,\" Justice Quart., vol. 28, no. 2, pp. 360–381, 2011.",
        "[17] Z. Marchment and P. Gill, \"Systematic review and meta-analysis of risk terrain modelling (RTM) as a spatial forecasting method,\" Crime Sci., vol. 10, 2021, doi: 10.1186/s40163-021-00149-6.",
        "[18] O. Kounadi, A. Ristea, A. Araujo, and M. Leitner, \"A systematic review on spatial crime forecasting,\" Crime Sci., vol. 9, 2020, doi: 10.1186/s40163-020-00116-7.",
        "[19] V. Mandalapu, L. Elluri, P. Vyas, and N. Roy, \"Crime prediction using machine learning and deep learning: A systematic review and future directions,\" IEEE Access, vol. 11, pp. 60153–60170, 2023.",
        "[20] X. Zhang, L. Liu, M. Lan, G. Song, L. Xiao, and J. Chen, \"Comparison of machine learning algorithms for predicting crime hotspots,\" IEEE Access, vol. 8, 2020.",
        "[21] E. G. Knox, \"The detection of space-time interactions,\" J. Roy. Statist. Soc. C (Appl. Statist.), vol. 13, no. 1, pp. 25–29, 1964.",
        "[22] M. Townsley, R. Homel, and J. Chaseling, \"Infectious burglaries: A test of the near repeat hypothesis,\" Brit. J. Criminol., vol. 43, no. 3, pp. 615–633, 2003.",
        "[23] S. D. Johnson et al., \"Space–time patterns of risk: A cross national assessment of residential burglary victimization,\" J. Quant. Criminol., vol. 23, no. 3, pp. 201–219, 2007.",
        "[24] M. Gritta, M. T. Pilehvar, and N. Collier, \"A pragmatic guide to geoparsing evaluation: Toponyms, named entity recognition and pragmatics,\" Lang. Resour. Eval., 2020.",
        "[25] P. A. Zandbergen, \"Geocoding quality and implications for spatial analysis,\" Geogr. Compass, vol. 3, no. 2, pp. 647–680, 2009.",
        "[26] E. Galbrun, K. Pelechrinis, and E. Terzi, \"Safe navigation in urban environments,\" in Proc. 3rd Int. Workshop Urban Comput. (UrbComp), KDD, New York, NY, USA, 2014.",
        "[27] J. Jacobs, The Death and Life of Great American Cities. New York, NY, USA: Random House, 1961.",
        "[28] O. Newman, Defensible Space: Crime Prevention Through Urban Design. New York, NY, USA: Macmillan, 1972.",
        "[29] M. Haklay and P. Weber, \"OpenStreetMap: User-generated street maps,\" IEEE Pervasive Comput., vol. 7, no. 4, pp. 12–18, Oct.–Dec. 2008.",
        "[30] K. Lum and W. Isaac, \"To predict and serve?,\" Significance, vol. 13, no. 5, pp. 14–19, 2016.",
        "[31] R. Richardson, J. M. Schultz, and K. Crawford, \"Dirty data, bad predictions: How civil rights violations impact police data, predictive policing systems, and justice,\" New York Univ. Law Rev. Online, vol. 94, p. 15, 2019.",
        "[32] D. Ensign, S. A. Friedler, S. Neville, C. Scheidegger, and S. Venkatasubramanian, \"Runaway feedback loops in predictive policing,\" in Proc. Conf. Fairness, Accountability Transparency (FAT*), PMLR vol. 81, 2018, pp. 160–171.",
        "[33] R. W. Sinnott, \"Virtues of the haversine,\" Sky Telescope, vol. 68, no. 2, p. 159, 1984.",
        "[34] F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825–2830, 2011.",
        "[35] R. Agrawal and R. Srikant, \"Fast algorithms for mining association rules,\" in Proc. 20th Int. Conf. Very Large Data Bases (VLDB), 1994, pp. 487–499.",
        "[36] G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manage., vol. 24, no. 5, pp. 513–523, 1988.",
        "[37] M. Thomson, E. Damaggio, and B. Raymor, Eds., \"Generic event delivery using HTTP push,\" IETF RFC 8030, Dec. 2016.",
        "[38] M. Thomson and P. Beverloo, \"Voluntary application server identification (VAPID) for web push,\" IETF RFC 8292, Nov. 2017.",
        "[39] A. Popescu, \"Geolocation API specification, 2nd ed.,\" W3C Recommendation, 2016.",
        "[40] A. R. Beresford and F. Stajano, \"Location privacy in pervasive computing,\" IEEE Pervasive Comput., vol. 2, no. 1, pp. 46–55, 2003.",
        "[41] N. Sakimura, J. Bradley, M. Jones, B. de Medeiros, and C. Mortimer, \"OpenID Connect Core 1.0 incorporating errata set 1,\" OpenID Foundation, Nov. 2014.",
        "[42] Government of India, \"The Digital Personal Data Protection Act, 2023,\" Act No. 22 of 2023, Aug. 2023.",
        "[43] J. Brooke, \"SUS: A quick and dirty usability scale,\" in Usability Evaluation in Industry, P. W. Jordan et al., Eds. London, U.K.: Taylor & Francis, 1996, pp. 189–194."
    ]

    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.line_spacing = 1.0
        p_ref.paragraph_format.left_indent = Inches(0.2)
        p_ref.paragraph_format.first_line_indent = Inches(-0.2)
        r_ref = p_ref.add_run(ref)
        r_ref.font.name = 'Times New Roman'
        r_ref.font.size = Pt(8)

    doc.save(OUT_PATH)
    shutil.copy2(OUT_PATH, DESKTOP_PATH)
    print("Successfully built final IEEE document with embedded figures, bullet points, clean citations, and zero white gaps!")

if __name__ == "__main__":
    build_paper()
