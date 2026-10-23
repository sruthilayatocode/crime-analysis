import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import shutil

def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
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
    # IEEE tables: single top line (1/2 pt), single bottom line (1/2 pt), no vertical borders
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

def make_ieee_paper(out_path):
    doc = docx.Document()

    # SECTION 1: Header (Title & Authors) - Single Column
    sec1 = doc.sections[0]
    sec1.top_margin = Inches(0.75)
    sec1.bottom_margin = Inches(1.0)
    sec1.left_margin = Inches(0.625)
    sec1.right_margin = Inches(0.625)

    # Base Normal font
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = RGBColor(0, 0, 0)

    # Paper Title (24 pt Times New Roman, Centered)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("CrimeSense: A Unified Crime-Hotspot Visualization, Zone-Classification and Personal-Safety Platform with Pattern-Recurrence Analysis for Vellore, India")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(24)
    r_title.font.bold = False

    # Authors (11 pt Times New Roman, Centered)
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(2)
    r_auth = p_auth.add_run("Sruthilaya J D, Mahithaa R, Sujeetha S")
    r_auth.font.name = 'Times New Roman'
    r_auth.font.size = Pt(11)

    # Student IDs
    p_ids = doc.add_paragraph()
    p_ids.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ids.paragraph_format.space_after = Pt(2)
    r_ids = p_ids.add_run("24MID0184, 24MID0239, 24MID0163")
    r_ids.font.name = 'Times New Roman'
    r_ids.font.size = Pt(10)

    # Institution
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(14)
    r_inst = p_inst.add_run("School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India")
    r_inst.font.name = 'Times New Roman'
    r_inst.font.size = Pt(10)

    # SECTION 2: Body - Continuous Section Break with 2 COLUMNS
    sec2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    sec2.top_margin = Inches(0.75)
    sec2.bottom_margin = Inches(1.0)
    sec2.left_margin = Inches(0.625)
    sec2.right_margin = Inches(0.625)
    
    # 2 columns with 0.25 inch (360 dxa) spacing
    sectPr = sec2._sectPr
    cols = parse_xml(f'<w:cols {nsdecls("w")} w:num="2" w:space="360"/>')
    sectPr.append(cols)

    # Helper functions for strict IEEE formatting
    def add_para(text, indent=True):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.14)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.bold = False
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.italic = True
        return p

    def add_equation(eq_text, num_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        # Using spaces to push equation number to right
        run_eq = p.add_run(f"    {eq_text}")
        run_eq.font.name = 'Times New Roman'
        run_eq.font.italic = True
        run_eq.font.size = Pt(9.5)
        run_num = p.add_run(f"\t\t({num_str})")
        run_num.font.name = 'Times New Roman'
        run_num.font.italic = False
        run_num.font.size = Pt(9.5)

    def add_table_header(num_str, title_str):
        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(8)
        p1.paragraph_format.space_after = Pt(1)
        p1.paragraph_format.keep_with_next = True
        r1 = p1.add_run(f"TABLE {num_str}")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(8)
        r1.font.bold = False

        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(4)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(title_str.upper())
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(7.5)
        r2.font.bold = False

    def add_fig_caption(num_str, text_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(6)
        r_bold = p.add_run(f"Fig. {num_str}. ")
        r_bold.font.name = 'Times New Roman'
        r_bold.font.size = Pt(8)
        r_bold.font.bold = False
        r_text = p.add_run(text_str)
        r_text.font.name = 'Times New Roman'
        r_text.font.size = Pt(8)

    # 1. ABSTRACT
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_before = Pt(0)
    p_abs.paragraph_format.space_after = Pt(4)
    p_abs.paragraph_format.line_spacing = 1.0
    r_absh = p_abs.add_run("Abstract—")
    r_absh.font.name = 'Times New Roman'
    r_absh.font.bold = True
    r_absh.font.size = Pt(9)
    r_abst = p_abs.add_run(
        "Residents of Tier II Indian cities rarely have an easy way to learn how a street, a market or a bus stop has featured in recent "
        "crime reporting, and the safety applications they do have tend to wait for a panic-button press. CrimeSense is a platform that joins analyst-side "
        "crime visualization with a resident-side safety assistant for Vellore, Tamil Nadu. A database of 596 news-sourced incident records, "
        "each with a source link, a locality-level coordinate, a type-based severity score and a risk level, drives a three-colour zone classifier (green, "
        "yellow, red), a hotspot and heatmap view for administrators, and a consent-gated live map. For residents the design adds a pre-visit "
        "advisory that explains what has been reported near a destination, a nearest safe-haven finder that ranks police stations, hospitals, shops "
        "and other staffed places, and an SOS channel that alerts chosen contacts on demand or when the user stays inactive inside a red zone. A "
        "pattern-recurrence module based on near-repeat statistics and association rules is proposed to find crimes that tend to follow one another. "
        "We report what has been verified (database integrity, e-mail and Google authentication, role-separated interfaces, persistence of user "
        "data) and mark the zone calibration, recurrence analysis, haven finder and advisory generator as designed but not yet evaluated, with a "
        "protocol for evaluating them. We also discuss reporting bias, labelling harms and location privacy."
    )
    r_abst.font.name = 'Times New Roman'
    r_abst.font.bold = True
    r_abst.font.size = Pt(9)

    # Keywords
    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(2)
    p_kw.paragraph_format.space_after = Pt(8)
    r_kwh = p_kw.add_run("Keywords—")
    r_kwh.font.name = 'Times New Roman'
    r_kwh.font.bold = True
    r_kwh.font.italic = True
    r_kwh.font.size = Pt(9)
    r_kwt = p_kw.add_run("crime hotspot visualization, zone classification, near-repeat analysis, personal safety application, SOS alerting, news-derived crime data, geospatial uncertainty, safe haven")
    r_kwt.font.name = 'Times New Roman'
    r_kwt.font.size = Pt(9)

    # I. INTRODUCTION
    add_h1("I. INTRODUCTION")
    add_para("Crime is not spread evenly over a city. A small number of street segments and neighbourhoods account for a large share of incidents, and this regularity is strong enough to have been described as a law of crime concentration [1], [2]. Routine activity theory explains why: offences occur where motivated offenders, suitable targets and a lack of capable guardians coincide in space and time [3], and crime pattern theory adds that offenders act in the places they pass through and know [4]. Hotspot maps built on these ideas are now a standard instrument of policing and have been linked to crime reductions in small target areas [5], [6].")
    add_para("The person who actually has to decide whether to wait at a bus stop at nine in the evening rarely sees any of this. Two gaps stand out. First, evidence about a place is produced for analysts and police, not for residents, and official statistics are published as annual aggregates [7] that cannot answer a question about one street. Second, the safety applications that residents do use are mostly reactive. A typical example sends the user’s coordinates to the police and to chosen contacts after a shake or a panic-button press [8]. Such a tool does nothing if the user cannot press the button, and it knows nothing about the place the user is standing in.")
    add_para("CrimeSense is our attempt to close both gaps in one platform for Vellore, Tamil Nadu. For a Tier II city, incident-level open data is scarce, so the platform builds its evidence base from publicly reported crime news, an approach used before for crime analysis [9], [10] but known to inherit the selection habits of the press [11]. On that base we place two interfaces. The administrator interface offers maps, heatmaps, hotspots, yearly histories, user management, a live map and an alert console. The resident interface is deliberately small: a search bar, a colour-coded zone result (green, yellow or red), an SOS button, saved places and settings. Beyond these, we design three features that we have not seen combined in the works we reviewed: a pattern-recurrence analysis that asks whether crimes follow one another in space and time, a safe-haven finder that points an uneasy user to the nearest staffed or busy place, and a pre-visit advisory that tells the user what has been reported around a destination and whether going with company is sensible.")
    add_para("This paper separates what exists from what is designed. Section III describes the architecture and each module. Section IV reports the implementation status, with every item marked as verified, partial, designed or planned. Section V summarizes the current database. Section VI gives an evaluation protocol with explicit definitions and operating points for the modules that have not yet been validated, and Section VII discusses ethics, privacy and threats to validity. The contributions are:")
    add_para("1) An integrated, role-separated architecture that connects a database-backed crime store, an analyst dashboard and a resident safety application.", indent=False)
    add_para("2) A transparent, configurable zone-classification model with explicit parameters, and an advisory format that reports evidence and never declares a place safe.", indent=False)
    add_para("3) A proposed pattern-recurrence module (near-repeat testing, association rules and a recurrence index) for finding repeating crime patterns.", indent=False)
    add_para("4) A proposed safe-haven finder that ranks police stations, hospitals, shops and similar places by category, opening status, distance and the zone score of the place itself.", indent=False)
    add_para("5) An SOS design that combines manual triggering with a dwell-and-inactivity escalation state machine, with consent-gated location handling and audit logging.", indent=False)
    add_para("6) A verified account of the running implementation (596 incident records, 11 tables) and an evaluation protocol for everything not yet validated.", indent=False)

    # II. RELATED WORK
    add_h1("II. RELATED WORK")
    add_h2("A. Crime Concentration and Hotspot Mapping")
    add_para("Micro-place studies show that crime clusters at very small geographic scales [1], [2]. Hotspots can be drawn as points, grid cells, ellipses or kernel density surfaces [5], [12], and adding time to the kernel estimate improves predictive hotspot maps [13]. DBSCAN [14] needs no predefined grid and labels isolated points as noise, but its output depends on the radius and minimum-points settings. Systematic evidence supports concentrating police effort on such places [6]. These methods are built for analysts and do not, by themselves, answer a resident’s question about one destination.")

    add_h2("B. Forecasting and Risk Terrain Modelling")
    add_para("Self-exciting point processes capture the way recent events raise the short-term rate of further events nearby [15]. Risk terrain modelling links crime to features of the built environment [16], and a recent meta-analysis found it effective at identifying places of elevated risk [17]. Reviews of spatial crime forecasting [18] and of machine-learning methods [19], [20] show how varied the study designs are, and Kounadi et al. call for reporting standards. Most of this work assumes incident registers that are far richer than a news-derived corpus. We therefore start from an interpretable weighted score and keep learned models for later, when data volume permits a held-out comparison.")

    add_h2("C. Repeat and Near-Repeat Patterns")
    add_para("The Knox test checks whether pairs of events that are close in space are also close in time more often than chance would suggest [21]. Applied to burglary, it revealed near-repeat victimization, where a burgled home and its neighbours face raised risk for a short period [22], [23]. These results are normally presented to analysts. In the works we reviewed we did not find one that passes such patterns to a resident-facing application, which is the gap our recurrence module addresses.")

    add_h2("D. News-Derived Crime Data and Geocoding")
    add_para("When official records are unavailable, social media and news archives have been mined for crime information [9], [10]. Newspaper data are useful but selective, because what gets reported depends on editorial priorities [11]. Turning place names into coordinates is itself error-prone [24], and positional accuracy should be reported with any analysis built on it [25]. We carry both cautions into our design and into the limitations in Section VII.")

    add_h2("E. Safe Routing, Natural Surveillance and Personal-Safety Applications")
    add_para("Galbrun et al. cast urban navigation as a bi-objective problem that trades path length against crime risk, using public crime data [26]. Our work is complementary: they route between two known points, whereas we label a place, find a nearby haven and escalate when the user cannot act. The idea of a haven rests on the observation that busy, staffed places are protected by 'eyes on the street' [27] and by territorial surveillance [28]. Candidate places can be drawn from OpenStreetMap, a volunteered geographic dataset of uneven completeness [29]. Finally, the risk that predictive systems reproduce the bias of their input records is well documented [30]–[32], and we treat it as a design constraint.")

    # Table I
    add_table_header("I", "Prior Work by Category and What Each Lacks for Resident Safety")
    t1 = doc.add_table(rows=7, cols=3)
    set_ieee_table_borders(t1)
    t1_headers = ["Category", "Typical scope", "Missing relative to CrimeSense"]
    for i, h in enumerate(t1_headers):
        cell = t1.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 40, 40, 60, 60)

    t1_rows = [
        ("Hotspot mapping, KDE [5], [13]", "Analyst maps of concentration", "Place labels for residents; alerts"),
        ("Forecasting, risk terrain [15], [16]", "Predicted risk surfaces from rich police data", "Resident interface; news-scale data; escalation"),
        ("Near-repeat analysis [21], [22]", "Space–time clustering tests on burglary", "Delivery of patterns to users or dashboards"),
        ("News-derived crime data [9], [10]", "Data acquisition and mining", "Zone labels, SOS, haven finding"),
        ("Safe routing [26]", "Route trade-off between length and risk", "SOS, dwell alerts, haven finder, analyst view"),
        ("Panic-button apps [8]", "Trigger plus location message", "Area evidence; automatic escalation; analytics")
    ]
    for r_idx, r_data in enumerate(t1_rows, 1):
        row = t1.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 30, 30, 50, 50)

    add_para("Table I summarizes the scope of the cited works as described by their authors. It is not an exhaustive survey, and the entries describe typical emphasis, not limitations of every individual paper.")

    # III. SYSTEM DESIGN
    add_h1("III. SYSTEM DESIGN")
    add_h2("A. Architecture Overview")
    add_para("CrimeSense has a client layer, an API layer, a service layer, a data layer and an offline ingestion pipeline (Fig. 1). The client layer holds two separate applications served from one code base: a mobile-first resident app and a desktop-first administrator dashboard. Both talk to a Flask REST API that authenticates users, enforces a role check (user or administrator), verifies Google ID tokens, and writes an audit entry for sensitive administrator actions. Services read and write a single SQLite database, which is the only data source. Modules shown with dashed outlines in Fig. 1 are proposed and are described as such throughout.")
    add_fig_caption("1", "Layered architecture of CrimeSense. Dashed boxes are proposed modules; solid boxes are implemented.")

    add_h2("B. Data Acquisition, Schema and Role Separation")
    add_para("Incident records come from publicly reported crime news. The offline pipeline tags the crime type, removes duplicate reports, attaches a locality and a coordinate, maps the type to a severity score and risk level, validates the record and exports a file that is imported into the crimes table. The table keeps the source name and link of every record, and also location_confidence and location_source fields so that positional certainty is never lost. Incidents entered by an administrator go into the same table and are written to the audit log.")
    add_para("The remaining tables hold user accounts and everything a user does (Fig. 2). A user row stores a name, a unique e-mail address, an optional password hash, an optional Google identifier, a role and an active flag. Settings, SOS contacts, saved places, location heartbeats, red-zone monitoring state, SOS events and alerts each reference the user. Role separation is designed to be enforced on the server: resident accounts reach only their own rows and the zone service, and the administrator routes reject non-administrators. Cross-account access tests are part of Table VII.")
    add_fig_caption("2", "Database schema. Child tables reference users.id; crimes is independent of any user.")

    add_h2("C. Zone Classification (Green, Yellow, Red)")
    add_para("The zone service answers one question for a query point q (a GPS fix, a searched address or a typed latitude and longitude): how heavily has the surrounding area featured in recent crime reports? Fig. 3 shows the pipeline. A bounding-box filter first narrows the candidate incidents, and the great-circle distance d between q and each candidate is then computed with the haversine formula [33],")
    add_equation("d = 2R arcsin √( sin²(Δφ/2) + cos φ₁ cos φ₂ sin²(Δλ/2) )", "1")
    add_para("with R = 6371 km. Let N(q) be the incidents with d ≤ ρ. Each incident i has a severity score s_i from the type table, a distance d_i and an age a_i. The raw risk is")
    add_equation("R(q) = Σ_{i ∈ N(q)} s_i · δ(d_i) · w(a_i),   δ(d) = 1 − d/ρ", "2")
    add_para("where w(a) is a recency weight that falls in steps with age. The score is bounded by a saturation constant R_ref,")
    add_equation("Z(q) = min{100, 100 · R(q) / R_ref}", "3")
    add_para("and mapped to a zone with two thresholds (Table II). As an arithmetic illustration, one severity-8 incident 200 m away and 3 months old, with ρ = 1000 m, contributes 8 × 0.8 × 1.0 = 6.4 to R. When N(q) is empty the service returns green with a low-confidence flag and a note that data coverage is limited, so that an empty result is never presented as proof of safety. The response also carries the incident count, the three most frequent crime types, the nearest incident, the most severe recent incident with its source link, and the date range of the data.")
    add_fig_caption("3", "Zone classification pipeline for a query point.")

    # Table II
    add_table_header("II", "Zone-Model Parameters (Design Defaults)")
    t2 = doc.add_table(rows=7, cols=3)
    set_ieee_table_borders(t2)
    t2_headers = ["Parameter", "Symbol", "Default / rule"]
    for i, h in enumerate(t2_headers):
        cell = t2.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t2_rows = [
        ("Search radius", "ρ", "1000 m (user-adjustable 500–1000 m)"),
        ("Severity", "s", "2–10 from the crime-type table"),
        ("Distance decay", "δ(d)", "1 − d/ρ"),
        ("Recency weight", "w(a)", "1.0 (≤ 6 mo); 0.7 (6–24 mo); 0.4 (> 24 mo)"),
        ("Saturation constant", "R_ref", "To be calibrated (Sec. VI)"),
        ("Red / yellow / green", "Z", "≥ 60 / 30 to < 60 / < 30")
    ]
    for r_idx, r_data in enumerate(t2_rows, 1):
        row = t2.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 30, 30, 50, 50)

    add_para("Two properties of the data constrain the model. Coordinates are locality-level, so many incidents in one locality share a position and the distance decay is meaningful only at scales above a neighbourhood. Severity comes from a crime-type lookup, which is auditable but not empirically calibrated. In the running prototype, raw risk is clamped directly to 100 (R_ref = 100). Because 469 incidents sit at the central Vellore centroid where raw risk exceeds 1900, the zone score immediately reaches the saturation cap of 100.0 (Red); empirical calibration of R_ref (Section VI) is needed to restore variance across dense zones. Both are reasons why the thresholds in Table II are design defaults, and why Section VI calibrates them against held-out incidents before any claim of predictive value is made.")

    add_h2("D. Hotspot Detection and Administrator Visualization")
    add_para("For analysts, the dashboard draws severity-coloured markers and a density heatmap, and it filters by district, locality, crime type, severity and date. While DBSCAN with the haversine metric [14], [34] is formulated as our target spatial clustering algorithm (with radius ε and minimum points m as configuration values), the active live service currently groups incidents by identical coordinates using database aggregation, and the dashboard’s 'active hotspots' counter is a simpler proxy (the number of localities with at least one high-severity incident), not a DBSCAN cluster count. Full DBSCAN execution is part of the evaluation protocol in Section VI.")

    add_h2("E. Pattern-Recurrence Analysis (Proposed)")
    add_para("To find out whether history repeats, we propose three complementary analyses over stored incidents (Fig. 4). The first is a near-repeat test in the style of Knox [21], [22]. For incident pairs (i, j) with spatial distance d_ij and time gap |t_i − t_j|, the statistic")
    add_equation("X = Σ_{i < j} 1[d_ij ≤ Δs] · 1[|t_i − t_j| ≤ Δt]", "4")
    add_para("counts pairs inside a space–time window. Its significance comes from a Monte Carlo test that permutes the event dates 999 times while holding the locations fixed, and the near-repeat ratio is the observed count divided by the permutation mean. Candidate windows are Δs ∈ {250, 500, 1000} m and Δt ∈ {7, 14, 30} days. Because coordinates are locality-level, pairs inside one locality have zero distance, so we also report a same-locality variant.")
    add_para("The second analysis mines sequential association rules between crime types. Treating each (locality, week) as a transaction, a rule A → B is scored by support, confidence and lift [35],")
    add_equation("lift(A → B) = P(B | A) / P(B)", "5")
    add_para("and retained only when lift exceeds 1 and survives the same permutation check. The third is a recurrence index, the share of incidents of type T in locality L that have an earlier incident of the same type in L within Δt,")
    add_equation("RI(L, T) = |{i ∈ I(L, T) : ∃ j, 0 < t_i − t_j ≤ Δt}| / |I(L, T)|", "6")
    add_para("Descriptions of incidents that share a modus operandi can additionally be linked by TF-IDF cosine similarity [36]. Outputs appear to administrators as pattern cards (for example, 'same type recurs within 500 m and 14 days') with links to the supporting incidents. Two cautions apply. Several articles about one incident can create false near-repeats, so de-duplication quality directly limits this module. And a recurrence weight may be fed into the zone score only after it has been validated on held-out data.")
    add_fig_caption("4", "Proposed pattern-recurrence analysis. All boxes are proposed and unvalidated.")

    add_h2("F. Pre-Visit Advisory and Safe-Haven Finder (Proposed)")
    add_para("Both features sit behind the resident app’s search and 'I feel unsafe' actions (Fig. 5). In the pre-visit flow, the user searches a place by name, street, landmark or exact latitude and longitude, the zone service is queried, and a rule-based generator turns the result into a short card (Table III). We use rules instead of free text generation so that every sentence can be traced to a number in the response. The card always shows the count and date range of the underlying reports and links to the source articles, and it states that reported incidents are not all incidents. Wording is chosen to inform and not to alarm: the app says 'recommended to go with company' and never says 'unsafe'.")
    add_fig_caption("5", "Resident-side flows: (a) pre-visit check; (b) nearest-haven search.")

    # Table III
    add_table_header("III", "Advisory Rules (Zone → Message Content)")
    t3 = doc.add_table(rows=7, cols=2)
    set_ieee_table_borders(t3)
    t3_headers = ["Condition", "Advisory content"]
    for i, h in enumerate(t3_headers):
        cell = t3.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t3_rows = [
        ("Green, none in ρ", "No reports within ρ in our data; coverage is limited; usual precautions"),
        ("Green, some in ρ", "Few or low-severity reports; list top types; usual precautions"),
        ("Yellow", "Moderate reports; stay on busy roads, avoid isolated stretches, tell a contact; show nearest havens"),
        ("Red", "Dense or severe recent reports; consider company, prefer daylight, enable live sharing; show nearest haven"),
        ("Violent type in top 3", "Add: going with a companion is advised"),
        ("Theft or fraud on top", "Add: secure belongings; beware unsolicited payment requests")
    ]
    for r_idx, r_data in enumerate(t3_rows, 1):
        row = t3.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 30, 30, 50, 50)

    add_para("In the haven flow, the app takes the current position and queries OpenStreetMap for staffed or busy public places within walking distance (Table IV). Each candidate p is scored by")
    add_equation("H(p) = w_c · o(p, t) · exp(−d_p/λ) · (1 − Z_p/100)", "7")
    add_para("where w_c is a category weight reflecting expected staffing and guardianship, o(p, t) is 1 if the place is open at time t (0 if closed, 0.5 if its hours are unknown), d_p is the walking distance, λ = 500 m is a length scale, and Z_p is the zone score at the haven itself, so that a haven inside a red zone is demoted. The top five are listed with distance, estimated walking time, a call button and a navigation link. Crowding is approximated by category and opening hours, because live footfall is not available to us. OpenStreetMap coverage of a Tier II city can be incomplete [29], so the evaluation includes a field audit (Section VI).")

    # Table IV
    add_table_header("IV", "Safe-Haven Categories and Initial Weights")
    t4 = doc.add_table(rows=7, cols=3)
    set_ieee_table_borders(t4)
    t4_headers = ["Category", "OpenStreetMap tag (example)", "Initial w_c"]
    for i, h in enumerate(t4_headers):
        cell = t4.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t4_rows = [
        ("Police station", "amenity=police", "1.0"),
        ("Hospital or clinic", "amenity=hospital, clinic", "0.9"),
        ("Government office", "office=government", "0.7"),
        ("Supermarket, mall", "shop=supermarket, mall", "0.7"),
        ("Pharmacy; fuel station", "amenity=pharmacy, fuel", "0.6"),
        ("Bus station; convenience shop", "amenity=bus_station; shop=convenience", "0.5")
    ]
    for r_idx, r_data in enumerate(t4_rows, 1):
        row = t4.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 30, 30, 50, 50)

    add_para("The weights are expert-assigned design values and will be revised after the validation in Section VI.")

    add_h2("G. SOS and Red-Zone Dwell Escalation")
    add_para("A resident must add at least one and at most five SOS contacts before using the app, with one marked as primary. The SOS button on the home screen requires a two-second press and offers a five-second cancel window, to avoid accidental alerts. On a trigger the service records an SOS event with the current position, sends each contact a message with the user’s name, the time, a map link and the current zone, and notifies the administrator console. Delivery goes through a provider abstraction that uses Twilio when credentials exist and a logging provider otherwise. An 'I’m safe' action resolves the event and sends an all-clear.")
    add_para("The automatic path covers the case in which the user cannot press anything. While the app is open and location sharing is on, the client sends a heartbeat every 30 s. A per-user state machine (Fig. 6) moves from SAFE to IN_RED when the zone is red. If the user then stays inactive for T minutes (default 10, adjustable 5–30), meaning no movement beyond 30 m and no touch interaction, the app asks 'Are you safe?' and waits 60 s. With no reply, an SOS event of type automatic is created and the contacts are alerted exactly as for a manual SOS, using the last known location. A 30-minute cooldown prevents repeated alerts, and a heartbeat that goes stale for more than 15 minutes while the last zone was red is treated as a trigger candidate with wording that says 'last known location'. The browser cannot track location reliably when the app is closed. The prompt is therefore delivered as a web push notification [37], [38], and the position comes from the browser geolocation interface [39]. Full background protection would need a native application.")
    add_fig_caption("6", "Red-zone dwell and inactivity state machine for automatic SOS.")

    add_h2("H. Privacy, Consent and Security")
    add_para("Location is sensitive data [40]. Resident location is stored only when the user has switched sharing on, and a separate setting controls whether administrators may see it. The administrator live map queries only users who have consented and whose latest heartbeat is recent, and each viewing is written to the audit log with the administrator’s identity and the number of users shown. Turning location access off stops tracking and heartbeats and disables the automatic alert, with a warning that safety alerts then do not work. Manual search still functions. Sign-in supports e-mail and password, with salted password hashes, and Google Sign-In: the server verifies the ID token’s audience, issuer, expiry and verified-email claim [41], links the Google identifier to an existing account with the same e-mail, and rejects deactivated accounts. The design follows the consent and erasure principles of India’s Digital Personal Data Protection Act [42], including account deletion with removal of personal data and a retention limit on location history.")

    # IV. IMPLEMENTATION STATUS AND VERIFICATION
    add_h1("IV. IMPLEMENTATION STATUS AND VERIFICATION")
    add_para("Table V states the status of each component. 'Verified' means that it was exercised by the project’s verification scripts, namely the database verifier, the flow tests and the Google sign-in test, or confirmed through the health endpoint. 'Partial' means that part of the component exists and has been exercised. 'Designed' and 'Planned' mean that no results are claimed.")

    # Table V
    add_table_header("V", "Implementation Status of CrimeSense Components")
    t5 = doc.add_table(rows=17, cols=3)
    set_ieee_table_borders(t5)
    t5_headers = ["Component", "Status", "Basis"]
    for i, h in enumerate(t5_headers):
        cell = t5.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t5_rows = [
        ("Crime database, 596 records, single source of truth", "Verified", "Database verifier; health endpoint"),
        ("Record quality checks (links, coordinates, dates, duplicates)", "Verified", "Quality audit, Table VI"),
        ("E-mail sign-up and login", "Verified", "Flow tests"),
        ("Role separation (user vs. admin routes)", "Partial", "Roles stored; access tests pending"),
        ("Google Sign-In, linking, deactivation check", "Verified", "Sign-in test script"),
        ("Admin KPIs, charts, incident table, create incident", "Verified", "Database-backed queries"),
        ("Consent-gated live map; audit log", "Verified", "Audit rows present"),
        ("Settings, SOS contacts, saved places persistence", "Verified", "Flow tests"),
        ("Notification provider (Twilio or logging)", "Partial", "Logging path exercised; no delivery trial"),
        ("Red-zone monitoring state and timed escalation", "Partial", "State table exists; no field trial"),
        ("Zone classification with Table II defaults", "Designed", "Uncalibrated"),
        ("Hotspot clustering (DBSCAN) in dashboard", "Partial", "KPI uses a proxy count"),
        ("Link sharing and WhatsApp share", "Partial", "Shared-links table exists"),
        ("Pre-visit advisory generator", "Designed", "Rules in Table III"),
        ("Safe-haven finder", "Designed", "Score in Eq. (7)"),
        ("Pattern-recurrence analysis", "Planned", "Protocol in Sec. VI")
    ]
    for r_idx, r_data in enumerate(t5_rows, 1):
        row = t5.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 25, 25, 40, 40)

    add_para("The checks reported next were produced by the project’s own scripts on 11 October 2026. Unlike an earlier prototype report, in which the numbers were re-derived independently, we did not recompute them for this version, and we state this so that readers can weigh the evidence accordingly. The health endpoint returned a connected database with 596 crime rows, one user and no SOS events. The database verifier found 11 tables. Besides the crimes table, the only populated tables were the single administrator account, its settings row and six audit entries; every other user-data table was empty at the time of the check. We read this as showing that no test users or events remain in the database, not as evidence about resident behaviour.")

    # Table VI
    add_table_header("VI", "Verification Summary of the Crimes Table (N = 596)")
    t6 = doc.add_table(rows=11, cols=2)
    set_ieee_table_borders(t6)
    t6_headers = ["Check", "Result"]
    for i, h in enumerate(t6_headers):
        cell = t6.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t6_rows = [
        ("Records with a valid source link", "596 of 596"),
        ("Coordinates inside the study bounds", "596 of 596 (lat 9.93–13.08, lng 76.96–80.27)"),
        ("Unique coordinate pairs (entire dataset)", "25 unique coordinates (16 in Vellore district)"),
        ("Primary centroid concentration", "469 of 596 records (78.69%) at (12.9165, 79.1325)"),
        ("District distribution", "552 Vellore (92.62%), 44 regional/external (7.38%)"),
        ("Valid ISO dates", "596 of 596"),
        ("Duplicate article identifiers", "0"),
        ("Severity score range; mean", "2.0 to 10.0; 5.92"),
        ("Risk level High / Medium / Low", "150 / 138 / 308"),
        ("Rows in other tables (users, settings, audit)", "1, 1, 6")
    ]
    for r_idx, r_data in enumerate(t6_rows, 1):
        row = t6.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 30, 30, 50, 50)

    # V. DATASET AND CURRENT RESULTS
    add_h1("V. DATASET AND CURRENT RESULTS")
    add_para("The database holds 596 incidents. Fig. 7(a) shows the crime-type labels. The largest label, general crime or offence, covers 277 records (46.5%), the next four are murder and homicide (49), contraband and mining (46), a separate murder label (37) and cybercrime and fraud (28). Fig. 7(b) shows that 25.2% of the records are High risk, 23.2% Medium and 51.7% Low.")
    add_fig_caption("7", "Current database: (a) crime-type labels; (b) risk-level split.")
    add_para("Four critical observations follow from these figures, and each limits what can be claimed. First, the dominance of the general label (46.5%) means that crime-type analysis, the pattern-recurrence module in particular, needs a finer and consistent taxonomy before it can say much. Second, the two murder labels overlap in meaning, and merging them would give 86 records under one label. Third, geocoding operates at locality scale: 469 out of 596 records (78.69%) share the central coordinate pair (12.9165, 79.1325) corresponding to generic 'Vellore' or 'Vellore District' mentions in news stories, yielding only 25 unique coordinate pairs across the dataset (16 in Vellore district). This creates a sharp spatial cliff: a query within 1000 m of this centroid aggregates 477 incidents (raw score > 1900), saturating the zone score to 100.0 (Red), whereas moving just 100 m further (1100 m from the centroid) drops the incident count to 8 and the score to 10.5 (Green). The model in its current form functions as a categorical proximity detector to known geocoded locality centroids, rather than a continuous micro-place risk field. Fourth, the database includes 44 records from neighboring or external districts (Chennai 16, Ranipet 13, Tiruvannamalai 5, etc.) that should be filtered when conducting pure municipal Vellore analysis.")
    add_para("The dashboard’s hotspot counter shows 24, which is the number of localities with at least one high-severity incident. It is not a count of DBSCAN clusters, and we do not present it as one. We report no accuracy or predictive result in this paper, because none of the proposed modules has been evaluated.")

    # VI. PROPOSED EVALUATION PROTOCOL
    add_h1("VI. PROPOSED EVALUATION PROTOCOL")
    add_para("A common weakness of crime-mapping studies is an unstated operating point. We therefore fix the metrics and thresholds in advance (Table VII). All predictive checks use a temporal split: incidents up to a cutoff date t0 are used to label zones, and incidents in the following three months are the test set, with the cutoff rolled forward in monthly steps. Because coordinates are locality-level, area is measured on a 500 m grid. The hit rate is the share of test incidents falling inside red cells. The predictive accuracy index [5] compares that share with the share of area labelled red,")
    add_equation("PAI = (n/N) / (a/A)", "8")
    add_para("where n test incidents out of N fall in red cells covering area a of a total study area A. Thresholds and R_ref are tuned on early windows and then reported at a fixed operating point, namely red cells covering at most 10% of the study area, so that results can be compared across settings.")

    # Table VII
    add_table_header("VII", "Evaluation Protocol")
    t7 = doc.add_table(rows=8, cols=3)
    set_ieee_table_borders(t7)
    t7_headers = ["Module", "Metric (definition)", "Protocol"]
    for i, h in enumerate(t7_headers):
        cell = t7.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(7.5)
        p.runs[0].font.bold = True
        set_cell_margins(cell, 30, 30, 50, 50)
    t7_rows = [
        ("Zone model", "Hit rate, PAI at red area ≤ 10%; Cohen’s κ vs. resident ratings", "Rolling temporal split; ≥ 2 local raters on sampled places"),
        ("Hotspots", "Cluster count and size vs. (ε, m) grid", "Sweep ε, m; report stability"),
        ("Recurrence", "Near-repeat ratio; permutation p (999 runs); lift", "Windows in Sec. III-E; de-duplicated data"),
        ("Haven finder", "Valid@5: share of top-5 that exist, are open and accessible; median walk to first valid", "Field audit of sampled query points"),
        ("SOS", "Trigger-to-delivery latency (p50, p95); false-alarm rate per red-zone hour", "Scripted trajectories on a sandbox database"),
        ("Access control", "Cross-account reads blocked; admin routes return 403 to residents", "Two test residents plus one admin"),
        ("Usability", "SUS score [43]; task completion", "≥ 15 participants; search, save, SOS tasks")
    ]
    for r_idx, r_data in enumerate(t7_rows, 1):
        row = t7.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(7.5)
            set_cell_margins(cell, 30, 30, 50, 50)

    add_para("Reporting these quantities with confidence intervals, together with the full parameter set, would also answer a general criticism of the spatial forecasting literature, that studies omit the information needed to compare them [18].")

    # VII. DISCUSSION
    add_h1("VII. DISCUSSION")
    add_h2("A. What Is New")
    add_para("Individual ingredients of CrimeSense are established: hotspot mapping, near-repeat testing, safe routing and SOS applications each have a literature. What we propose is their combination around one evidence store, so that the same incident record serves an analyst looking at a map, a resident checking a destination and a monitoring service watching for inactivity in a red zone. The haven finder and the pre-visit advisory turn area-level evidence into an action available at the moment of need, and the dwell escalation addresses the case, absent from the panic-button design we cite [8], in which the user cannot act.")

    add_h2("B. Ethics and Responsible Use")
    add_para("A colour label attached to a neighbourhood can stigmatize it, and a system trained or tuned on reported incidents can amplify the bias of those reports [30]–[32]. Our safeguards are to describe zones as 'reported incidents', to show counts, dates and source links on every card, to avoid the word 'unsafe', to state that green does not mean safe, and to keep the system out of enforcement decisions, where feedback loops are most harmful [32]. A 'report incorrect zone' action and periodic review of labels are planned. An opposite risk is alert fatigue and false alarms to contacts, which the confirmation prompt and cooldown are meant to limit and which Table VII measures.")

    add_h2("C. Limitations and Threats to Validity")
    add_para("The evidence base is news-derived, so it reflects what reporters chose to cover, serious or unusual incidents may be over-represented, and recent years may be better covered than earlier ones [11]. Locality-level coordinates limit spatial precision [24], [25]. The severity table is expert-assigned and not calibrated on outcomes. The corpus covers one district and mostly one city, so the thresholds may not transfer. The recurrence analysis is vulnerable to duplicate coverage of one incident. The safe-haven finder inherits the uneven completeness of OpenStreetMap and approximates crowding by category. The automatic SOS works only while the browser is alive, and delivery depends on third-party messaging providers and on network coverage. Finally, the project checks cited in Section IV were not independently recomputed for this paper, and none of the proposed modules has been evaluated.")

    # VIII. CONCLUSION AND FUTURE WORK
    add_h1("VIII. CONCLUSION AND FUTURE WORK")
    add_para("CrimeSense joins an analyst-side crime visualization environment to a resident-side safety assistant on a single database of 596 sourced incident records for Vellore. The database-backed core, role-separated interfaces, Google and e-mail sign-in, consent-gated live map and persistence of user data have been verified. The zone classifier, the pre-visit advisory, the safe-haven finder and the pattern-recurrence analysis are specified here with explicit formulas, parameters and evaluation metrics, and they are the next steps. Future work is to calibrate and evaluate the zone model on a rolling temporal split, refine the crime-type taxonomy, add finer-grained geocoding, run the near-repeat and rule-mining analyses on de-duplicated data, audit haven coverage in the field, trial the SOS path end to end, and study usability with residents.")

    # REFERENCES
    add_h1("REFERENCES")
    refs = [
        "[1] D. Weisburd, “The law of crime concentration and the criminology of place,” Criminology, vol. 53, no. 2, pp. 133–157, 2015.",
        "[2] L. W. Sherman, P. R. Gartin, and M. E. Buerger, “Hot spots of predatory crime: Routine activities and the criminology of place,” Criminology, vol. 27, no. 1, pp. 27–56, 1989.",
        "[3] L. E. Cohen and M. Felson, “Social change and crime rate trends: A routine activity approach,” Amer. Sociol. Rev., vol. 44, no. 4, pp. 588–608, 1979.",
        "[4] P. J. Brantingham and P. L. Brantingham, Patterns in Crime. New York, NY, USA: Macmillan, 1984.",
        "[5] S. Chainey, L. Tompson, and S. Uhlig, “The utility of hotspot mapping for predicting spatial patterns of crime,” Secur. J., vol. 21, no. 1–2, pp. 4–28, 2008.",
        "[6] A. A. Braga, B. S. Turchan, A. V. Papachristos, and D. M. Hureau, “Hot spots policing of small geographic areas effects on crime,” Campbell Syst. Rev., vol. 15, no. 3, Art. no. e1046, 2019.",
        "[7] National Crime Records Bureau, “Crime in India 2022,” Ministry of Home Affairs, Government of India, New Delhi, India, 2023.",
        "[8] D. Chand, S. Nayak, K. S. Bhat, S. Parikh, Y. Singh, and A. A. Kamath, “A mobile application for women’s safety: WoSApp,” in Proc. IEEE Region 10 Conf. (TENCON), 2016.",
        "[9] M. S. Gerber, “Predicting crime using Twitter and kernel density estimation,” Decis. Support Syst., vol. 61, pp. 115–125, 2014.",
        "[10] A. Umair, M. S. Sarfraz, M. Ahmad, U. Habib, M. H. Ullah, and M. Mazzara, “Spatiotemporal analysis of web news archives for crime prediction,” Appl. Sci., vol. 10, no. 22, Art. no. 8220, 2020.",
        "[11] J. Earl, A. Martin, J. D. McCarthy, and S. A. Soule, “The use of newspaper data in the study of collective action,” Annu. Rev. Sociol., vol. 30, pp. 65–80, 2004.",
        "[12] B. W. Silverman, Density Estimation for Statistics and Data Analysis. London, U.K.: Chapman & Hall, 1986.",
        "[13] Y. Hu, F. Wang, C. Guin, and H. Zhu, “A spatio-temporal kernel density estimation framework for predictive crime hotspot mapping and evaluation,” Appl. Geogr., vol. 99, pp. 89–97, 2018.",
        "[14] M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, “A density-based algorithm for discovering clusters in large spatial databases with noise,” in Proc. 2nd Int. Conf. Knowl. Discovery Data Mining (KDD), 1996, pp. 226–231.",
        "[15] G. O. Mohler, M. B. Short, P. J. Brantingham, F. P. Schoenberg, and G. E. Tita, “Self-exciting point process modeling of crime,” J. Amer. Statist. Assoc., vol. 106, no. 493, pp. 100–108, 2011.",
        "[16] J. M. Caplan, L. W. Kennedy, and J. Miller, “Risk terrain modeling: Brokering criminological theory and GIS methods for crime forecasting,” Justice Quart., vol. 28, no. 2, pp. 360–381, 2011.",
        "[17] Z. Marchment and P. Gill, “Systematic review and meta-analysis of risk terrain modelling (RTM) as a spatial forecasting method,” Crime Sci., vol. 10, 2021, doi: 10.1186/s40163-021-00149-6.",
        "[18] O. Kounadi, A. Ristea, A. Araujo, and M. Leitner, “A systematic review on spatial crime forecasting,” Crime Sci., vol. 9, 2020, doi: 10.1186/s40163-020-00116-7.",
        "[19] V. Mandalapu, L. Elluri, P. Vyas, and N. Roy, “Crime prediction using machine learning and deep learning: A systematic review and future directions,” IEEE Access, vol. 11, pp. 60153–60170, 2023.",
        "[20] X. Zhang, L. Liu, M. Lan, G. Song, L. Xiao, and J. Chen, “Comparison of machine learning algorithms for predicting crime hotspots,” IEEE Access, vol. 8, 2020.",
        "[21] E. G. Knox, “The detection of space-time interactions,” J. Roy. Statist. Soc. C (Appl. Statist.), vol. 13, no. 1, pp. 25–29, 1964.",
        "[22] M. Townsley, R. Homel, and J. Chaseling, “Infectious burglaries: A test of the near repeat hypothesis,” Brit. J. Criminol., vol. 43, no. 3, pp. 615–633, 2003.",
        "[23] S. D. Johnson et al., “Space–time patterns of risk: A cross national assessment of residential burglary victimization,” J. Quant. Criminol., vol. 23, no. 3, pp. 201–219, 2007.",
        "[24] M. Gritta, M. T. Pilehvar, and N. Collier, “A pragmatic guide to geoparsing evaluation: Toponyms, named entity recognition and pragmatics,” Lang. Resour. Eval., 2020.",
        "[25] P. A. Zandbergen, “Geocoding quality and implications for spatial analysis,” Geogr. Compass, vol. 3, no. 2, pp. 647–680, 2009.",
        "[26] E. Galbrun, K. Pelechrinis, and E. Terzi, “Safe navigation in urban environments,” in Proc. 3rd Int. Workshop Urban Comput. (UrbComp), KDD, New York, NY, USA, 2014.",
        "[27] J. Jacobs, The Death and Life of Great American Cities. New York, NY, USA: Random House, 1961.",
        "[28] O. Newman, Defensible Space: Crime Prevention Through Urban Design. New York, NY, USA: Macmillan, 1972.",
        "[29] M. Haklay and P. Weber, “OpenStreetMap: User-generated street maps,” IEEE Pervasive Comput., vol. 7, no. 4, pp. 12–18, Oct.–Dec. 2008.",
        "[30] K. Lum and W. Isaac, “To predict and serve?,” Significance, vol. 13, no. 5, pp. 14–19, 2016.",
        "[31] R. Richardson, J. M. Schultz, and K. Crawford, “Dirty data, bad predictions: How civil rights violations impact police data, predictive policing systems, and justice,” New York Univ. Law Rev. Online, vol. 94, p. 15, 2019.",
        "[32] D. Ensign, S. A. Friedler, S. Neville, C. Scheidegger, and S. Venkatasubramanian, “Runaway feedback loops in predictive policing,” in Proc. Conf. Fairness, Accountability Transparency (FAT*), PMLR vol. 81, 2018, pp. 160–171.",
        "[33] R. W. Sinnott, “Virtues of the haversine,” Sky Telescope, vol. 68, no. 2, p. 159, 1984.",
        "[34] F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” J. Mach. Learn. Res., vol. 12, pp. 2825–2830, 2011.",
        "[35] R. Agrawal and R. Srikant, “Fast algorithms for mining association rules,” in Proc. 20th Int. Conf. Very Large Data Bases (VLDB), 1994, pp. 487–499.",
        "[36] G. Salton and C. Buckley, “Term-weighting approaches in automatic text retrieval,” Inf. Process. Manage., vol. 24, no. 5, pp. 513–523, 1988.",
        "[37] M. Thomson, E. Damaggio, and B. Raymor, Eds., “Generic event delivery using HTTP push,” IETF RFC 8030, Dec. 2016.",
        "[38] M. Thomson and P. Beverloo, “Voluntary application server identification (VAPID) for web push,” IETF RFC 8292, Nov. 2017.",
        "[39] A. Popescu, “Geolocation API specification, 2nd ed.,” W3C Recommendation, 2016.",
        "[40] A. R. Beresford and F. Stajano, “Location privacy in pervasive computing,” IEEE Pervasive Comput., vol. 2, no. 1, pp. 46–55, 2003.",
        "[41] N. Sakimura, J. Bradley, M. Jones, B. de Medeiros, and C. Mortimer, “OpenID Connect Core 1.0 incorporating errata set 1,” OpenID Foundation, Nov. 2014.",
        "[42] Government of India, “The Digital Personal Data Protection Act, 2023,” Act No. 22 of 2023, Aug. 2023.",
        "[43] J. Brooke, “SUS: A quick and dirty usability scale,” in Usability Evaluation in Industry, P. W. Jordan et al., Eds. London, U.K.: Taylor & Francis, 1996, pp. 189–194."
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

    doc.save(out_path)
    print(f"Strict IEEE Word document successfully created at: {out_path}")

if __name__ == "__main__":
    out_file = r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_Paper_IIT_Kanpur.docx"
    make_ieee_paper(out_file)
    # Also update Desktop
    shutil.copy2(out_file, r"c:\Users\sruth\Desktop\CrimeSense_IEEE_Paper_IIT_Kanpur.docx")
    print("Updated Desktop copy as well.")
