import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import os, shutil

FIG_DIR = r"c:\Users\sruth\crime analysis\research_paper\figures"
OUT_PATH = r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_Paper_IIT_Kanpur_Final.docx"
DESKTOP_PATH = r"c:\Users\sruth\Desktop\CrimeSense_IEEE_Paper_IIT_Kanpur_Final.docx"
OUT_PATH_ORIG = r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_0PercentAI_IIT_Kanpur.docx"
DESKTOP_PATH_ORIG = r"c:\Users\sruth\Desktop\CrimeSense_IEEE_0PercentAI_IIT_Kanpur.docx"

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

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("CrimeSense: A Unified Crime Hotspot Visualization, Zone Classification and Personal Safety Platform with Pattern Recurrence Analysis for Vellore, India")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(21)
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
            from PIL import Image
            try:
                with Image.open(path) as im:
                    w_px, h_px = im.size
                aspect = h_px / w_px
                # If scaled height at 3.35 in width is > 1.75 inches, constrain by height
                if aspect * 3.35 > 1.75:
                    target_h = Inches(1.75)
                    target_w = None
                else:
                    target_w = Inches(3.35)
                    target_h = None
            except Exception:
                target_w = Inches(3.35)
                target_h = None

            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(2)
            p_img.paragraph_format.space_after = Pt(1)
            p_img.paragraph_format.keep_with_next = True
            run = p_img.add_run()
            if target_h:
                run.add_picture(path, height=target_h)
            else:
                run.add_picture(path, width=target_w)

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_cap.paragraph_format.space_before = Pt(0)
            p_cap.paragraph_format.space_after = Pt(2)
            p_cap.paragraph_format.line_spacing = 1.0
            p_cap.paragraph_format.keep_with_next = False
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
        p1.paragraph_format.space_before = Pt(4)
        p1.paragraph_format.space_after = Pt(1)
        p1.paragraph_format.keep_with_next = True
        r1 = p1.add_run(f"TABLE {num_str}")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(8)

        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(title_str.upper())
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(7.5)

    # =========================================================================
    # ABSTRACT (Aligned with reviewer recommendations, grounded in implementation)
    # =========================================================================
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
        "This study presents CrimeSense, a system designed to help users explore crime reports in Vellore and examine reported incidents around a selected location. "
        "The current system uses an SQLite database containing 596 news-derived incident records and includes an administrative dashboard "
        "for viewing and managing these records. The paper introduces an interpretable zone classification model that marks locations green, yellow, or red "
        "using spatial and temporal decay. To support pedestrian safety, design specifications are formulated for a pre-visit destination advisory, "
        "an OpenStreetMap-based safe haven finder relying on natural surveillance, and an automated red-zone inactivity state machine. In addition, "
        "a pattern recurrence formulation applying Knox space-time permutation tests and association rules is described to identify sequential crime trends. "
        "Finally, the paper reports database verification audits, role-separated authentication checks, and privacy safeguards conforming to the Indian "
        "Digital Personal Data Protection Act, followed by a formal evaluation protocol."
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
    r_kwt = p_kw.add_run("crime hotspot visualization, zone classification, near repeat analysis, personal safety application, SOS alerting, news derived crime data, safe haven finder, spatio-temporal risk")
    r_kwt.font.name = 'Times New Roman'
    r_kwt.font.size = Pt(9)

    # =========================================================================
    # I. INTRODUCTION
    # =========================================================================
    add_h1("I. INTRODUCTION")
    add_p("Crime is not spread evenly across a city. It clusters on certain streets, dark alleys, and crowded transit hubs [1]. Criminologists have documented this phenomenon for decades [2], [3]. The routine activity perspective shows that predatory offenses happen when a motivated offender encounters a vulnerable target without a capable guardian [3]. In addition, crime pattern theory explains that criminals look for targets along the daily routes they travel between home, work, and recreational spots [4]. Police departments routinely use computer-generated hotspot maps to assign patrol cars to these problem corners [5], [6].")
    add_p("Even so, a student or night-shift worker walking alone through Vellore cannot benefit from any of this police data. There are two straightforward reasons for this gap. First, official crime statistics in India are gathered for administrative record-keeping rather than public awareness. The National Crime Records Bureau publishes district totals [7], but those reports aggregate data across entire years and wide regions. They cannot tell someone whether Katpadi railway junction or Bagayam bus stop has a recent history of chain snatchings after 9 PM. Second, existing civilian safety applications are purely reactive [8]. Most commercial tools offer a red SOS button or listen for handset shakes. If someone is surprised, cornered, or physically pinned down, they cannot unlock their screen to tap a button anyway. Worse, these apps possess zero knowledge about whether the user is standing in a quiet residential lane or a recognized danger spot.")
    add_p("To address these gaps, a prototype was developed that connects a news-derived crime database to an administrative dashboard and a proposed set of resident-facing safety features. Because city police stations in Tamil Nadu do not provide open API feeds of daily First Information Reports, the dataset was constructed from regional digital news coverage, following data collection practices proven in earlier spatial research [9], [10] while keeping journalistic reporting biases in mind [11]. Two interfaces were built over this shared data layer. The administrative console provides spatial heatmaps, DBSCAN cluster grouping, multi-year charts, user account controls, and emergency alert tables. The proposed resident web interface is designed with an address search bar, a three-color safety badge (green, yellow, or red), an SOS dispatch button, saved places, and privacy switches.")
    add_p("This paper carefully differentiates fully verified software components from theoretical modules undergoing validation. Section III presents the system architecture. Section IV reports the current verification status across all components. Section V analyzes the 596-record empirical dataset. Section VI sets out an open evaluation protocol, and Section VII examines ethical implications, data limitations, and privacy compliance. The primary contributions are:")
    add_bullet("A multi-tier architecture linking a 596-record news-derived SQLite database with an administrative GIS console and proposed citizen mobile views.")
    add_bullet("A transparent spatio-temporal zone classification model that explains local evidence clearly rather than issuing opaque risk scores or declaring any place completely safe.")
    add_bullet("A pattern recurrence formulation combining Knox space-time permutation tests and association rules to detect repeating crime sequences.")
    add_bullet("A safe haven ranking formulation that evaluates candidate public shelters by operational status, distance, institutional guardianship weight, and surrounding crime exposure.")
    add_bullet("An automated emergency escalation state machine design that detects prolonged inactivity within designated high-risk zones.")
    add_bullet("A documented verification report of the active SQLite database (596 sourced records across 11 tables) and an empirical testing protocol for unvalidated modules.")

    # =========================================================================
    # II. RELATED WORK
    # =========================================================================
    add_h1("II. RELATED WORK")
    add_h2("A. Crime Concentration and Hotspot Mapping")
    add_para("Decades of field criminology show that urban offenses gather in micro-places [1], [2]. Research teams visualize these concentrations using point maps, regular spatial grids, and kernel density surfaces [5], [12]. Adding time-decay weights to older offenses helps improve short-range hotspot forecasts [13]. Density-based clustering algorithms such as DBSCAN [14] discover irregular incident clusters without forcing points into square cells, treating one-off outliers as noise. Randomized trials demonstrate that stationing police foot patrols at known hotspots noticeably lowers crime rates [6]. However, these GIS systems remain closed inside police stations, offering no guidance to a solitary walker on a dark street.")

    add_h2("B. Spatial Forecasting and Risk Terrain Modeling")
    add_para("Point-process models use self-exciting mathematics borrowed from earthquake aftershock analysis to estimate how one incident temporarily increases nearby crime odds [15]. Risk terrain modeling connects crime probability to physical urban fixtures such as liquor vends, bus terminals, and unlit pathways [16], with meta-analyses confirming its predictive value [17]. Broader surveys of predictive policing [18] and machine learning models [19], [20] point out that almost every published model assumes direct access to detailed municipal police dispatch logs. In India, such logs are simply not available to the public. Because of this limitation, CrimeSense relies on transparent arithmetic weighting formulas and leaves heavy machine learning algorithms for offline benchmarking.")

    add_h2("C. Repeat and Near-Repeat Victimization")
    add_para("The near-repeat hypothesis observes that after a property or street offense occurs, neighboring locations face elevated risk for a short window of time [21]. Applying the Knox space-time interaction test to home burglaries showed that neighboring houses experience heightened risk for roughly three weeks after the initial break-in [22], [23]. Prior research has restricted these findings to academic journals and police briefings. No commercial or open-source mobile safety app was identified that turns near-repeat mathematics into direct pedestrian advice.")

    add_h2("D. News-Derived Crime Data and Geocoding")
    add_para("When police departments do not publish public computer-aided dispatch feeds, online newspapers and social media feeds offer the best alternative records of street crime [9], [10]. While news reports provide useful situational text, they naturally reflect journalistic priorities, giving more attention to sensational or violent events while ignoring routine petty theft [11]. Furthermore, converting descriptive locality names to map coordinates introduces spatial uncertainty [24], making it essential for software systems to indicate geocoding confidence explicitly [25]. These constraints are taken into account directly in the CrimeSense user interface.")

    add_h2("E. Safe Routing and Environmental Guardianship")
    add_para("Previous pedestrian routing studies have framed safe navigation as a graph optimization problem that trades extra walking distance against lower cumulative crime exposure along a route [26]. CrimeSense handles user safety differently. Instead of computing long, winding detour routes, the system provides direct destination risk checks, steers distressed pedestrians toward immediate safe havens, and triggers automated alerts when users become stationary in dangerous areas. The safe haven concept builds directly on Jane Jacobs' observation of natural surveillance, which shows that active commercial street fronts and shop staff act as informal 'eyes on the street' [27]. Oscar Newman's defensible space studies similarly showed that daily human presence discourages criminal opportunity [28]. Candidate safe havens can be gathered from OpenStreetMap [29]. Finally, automated safety systems must avoid reinforcing neighborhood stigma [30], [31], [32], which CrimeSense addresses through neutral language and strict opt-in location tracking.")

    # Table I
    add_tbl_hdr("I", "Comparison of Existing Literature Categories Relative to CrimeSense")
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
        ("Hotspot mapping [5], [13]", "Spatial density surfaces for analysts", "Resident zone badges and automated warnings"),
        ("Forecasting, RTM [15], [16]", "Risk surfaces derived from police CAD feeds", "Civilian interface, news scale adaptation, dwell alerts"),
        ("Near repeat analysis [21], [22]", "Space-time clustering on burglary data", "Delivery of recurring crime patterns to mobile users"),
        ("News derived crime [9], [10]", "Text extraction and incident harvesting", "Zone classification, haven recovery, emergency dispatch"),
        ("Safe routing [26]", "Distance versus path risk trade-offs", "Immediate haven recovery, dwell alerts, analyst views"),
        ("Panic button apps [8]", "Physical trigger sending location SMS", "Area risk intelligence, automated dwell escalation, analytics")
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

    add_p("Table I groups prior studies by their primary focus, including hotspot mapping, forecasting, near-repeat analysis, and safety applications. These categories help explain how CrimeSense combines crime visualization with resident-facing features.")

    # =========================================================================
    # III. SYSTEM DESIGN
    # =========================================================================
    add_h1("III. SYSTEM DESIGN")
    add_h2("A. Architecture Overview")
    add_para("CrimeSense is built as a multi-tier web application consisting of a frontend interface tier, a Flask REST API tier, a business logic service layer, an SQLite database, and an offline news processing pipeline (Fig. 1). The frontend serves both the mobile resident view and the administrative console from a single codebase. Both communicate over HTTPS with Flask, which enforces role permissions, validates Google OAuth tokens, and records audit logs for administrative queries. All backend services read and write to an SQLite database running with Write Ahead Logging turned on.")
    add_pic("fig1_architecture.png", "1", "System architecture of CrimeSense. Solid boxes show verified modules; dashed boxes mark proposed components.")

    add_h2("B. Data Acquisition, Schema, and Role Separation")
    add_para("Incident records are collected from verified regional news articles. An offline Python script standardizes crime names, discards duplicates, geocodes named localities, assigns severity ratings, and loads the records into SQLite. Fig. 2 illustrates this processing pipeline. Records whose locality cannot be resolved to coordinates are not discarded; instead, they are carried forward with an explicit uncertainty flag in the location_confidence column. The crimes table stores original news URLs, geocoding confidence levels, and locality tags to ensure full source provenance. Any crime entered by an administrator writes to this same table and generates a timestamped audit entry.")
    add_para("The remaining ten tables manage user accounts, settings, and safety interactions. User rows store names, verified email addresses, password hashes, optional Google identifiers, roles, and account status flags. Related tables track user preferences, emergency contacts, saved places, location heartbeats, red-zone dwell states, and dispatched SOS alerts. Application middleware ensures residents can only access their own records, while administrative routes block unprivileged accounts.")
    add_pic("fig2_pipeline.png", "2", "CrimeSense processing pipeline. Records with unresolved locality are carried forward with uncertainty flags.")

    add_h2("C. Zone Classification (Green, Yellow, Red)")
    add_para("The zone service measures crime exposure for an arbitrary coordinate q (such as a GPS fix, searched address, or map click). Fig. 3 traces this evaluation pipeline. A bounding box filter first prunes distant incidents, followed by great-circle distance calculation using the Haversine equation [33]:")
    add_eq("d = 2R arcsin √( sin²(Δφ/2) + cos φ₁ cos φ₂ sin²(Δλ/2) )", "1")
    add_para("where R is Earth's mean radius (6371 km). For incidents within search radius ρ, each record i contributes a risk increment based on its severity rating s_i, distance d_i, and age a_i. Total raw risk R(q) is calculated as:")
    add_eq("R(q) = Σ_{i ∈ N(q)} s_i · δ(d_i) · w(a_i),   δ(d) = 1 − d/ρ", "2")
    add_para("where w(a) applies step-down weights based on the age of the report (1.0 for incidents within 6 months, 0.7 for 6 to 24 months, and 0.4 for older records). The raw risk R(q) is then normalized against a reference saturation constant R_ref:")
    add_eq("Z(q) = min{100, 100 · R(q) / R_ref}", "3")
    add_para("and map the resulting score Z(q) into three practical safety badges (Table II). In the current running prototype, raw risk is clamped directly to 100 (R_ref = 100). Because 469 incidents sit at the primary Vellore centroid where raw risk exceeds 1900, the score reaches the saturation ceiling of 100.0 (Red); empirical calibration of R_ref (Section VI) is required to restore variance across dense zones. If no incidents exist within radius ρ, CrimeSense displays green alongside an explicit low data confidence note, reminding the user that lack of news coverage is not the same as guaranteed physical safety. The API response returns incident counts, top crime types, the nearest recorded incident, and direct source links.")
    add_pic("fig3_zone_pipeline.png", "3", "Zone classification pipeline for an arbitrary query coordinate.")

    # Table II
    add_tbl_hdr("II", "Zone Model Parameters and Baseline Configuration")
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
        ("Search radius", "ρ", "1000 m (user adjustable 500–1000 m)"),
        ("Severity score", "s", "2–10 based on crime category table"),
        ("Distance decay", "δ(d)", "Linear: 1 − d/ρ"),
        ("Recency weight", "w(a)", "1.0 (≤6 mo); 0.7 (6–24 mo); 0.4 (>24 mo)"),
        ("Saturation cap", "R_ref", "Calibrated empirically (Section VI)"),
        ("Zone boundaries", "Z", "Red: ≥60; Yellow: 30 to <60; Green: <30")
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

    add_para("Because news coordinates point to locality centers rather than specific house numbers, distance decay captures neighborhood variations. Severity scores follow a transparent category lookup table, evaluated on held-out temporal splits in Section VI.")

    add_h2("D. Hotspot Detection and Administrator Visualization")
    add_para("The administrator dashboard provides color-coded incident markers, density heatmaps, and flexible filters across districts, localities, crime categories, and date ranges. While DBSCAN [14] with Haversine distance is formulated as the target spatial clustering algorithm (using neighborhood radius ε and minimum points m), the active backend service currently groups incidents by identical coordinates using database aggregation, and the dashboard's active hotspot counter shows 24 (the count of distinct localities with at least one high-severity crime). Full DBSCAN execution is part of the evaluation protocol in Section VI.")

    add_h2("E. Pattern-Recurrence Analysis (Proposed)")
    add_para("To examine repeating spatial crime patterns, CrimeSense formulates three analytical routines (Fig. 4). First, the Knox space-time interaction test calculates statistic X across incident pairs (i, j):")
    add_eq("X = Σ_{i < j} 1[d_ij ≤ Δs] · 1[|t_i − t_j| ≤ Δt]", "4")
    add_para("tested across distance bounds Δs ∈ {250, 500, 1000} m and time windows Δt ∈ {7, 14, 30} days against 999 Monte Carlo date permutations. Second, sequential association rules treat locality-week bins as transactions, evaluating rule A → B via lift [35]:")
    add_eq("lift(A → B) = P(B | A) / P(B)", "5")
    add_para("Third, the locality recurrence index measures the share of offenses in locality L of type T that have a prior occurrence within Δt:")
    add_eq("RI(L, T) = |{i ∈ I(L, T) : ∃ j, 0 < t_i − t_j ≤ Δt}| / |I(L, T)|", "6")
    add_pic("fig4_recurrence.png", "4", "Proposed pattern recurrence pipeline. Modules are formulated for evaluation.")

    add_h2("F. Pre-Visit Advisory and Safe-Haven Finder (Proposed)")
    add_para("These modules support the resident application search bar and 'I Feel Unsafe' features (Fig. 5). The pre-visit check converts local incident records into clear advisory cards (Table III) using rule templates rather than large language models, ensuring that every sentence traces back directly to source news reports.")
    add_pic("fig5_resident_flows.png", "5", "Resident user flows: (a) pre-visit destination check; (b) nearest safe haven search.")

    # Table III
    add_tbl_hdr("III", "Advisory Rules (Zone Status to Message Content)")
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
        ("Green, some in ρ", "Few low-severity reports; top types listed; standard precautions advised"),
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

    add_para("In the haven flow, candidate public locations within walking distance are queried from OpenStreetMap (Table IV) and ranked by utility score H(p):")
    add_eq("H(p) = w_c · o(p, t) · exp(−d_p / λ) · (1 − Z_p / 100)", "7")
    add_para("where w_c reflects institutional guardianship, o(p, t) indicates opening status (1.0 if open, 0.0 if closed, and 0.5 if unlisted), d_p is walking distance, decay constant λ = 500 m, and Z_p penalizes shelters located inside crime hotspots. The top five havens are displayed with walking times, telephone buttons, and navigation links.")

    # Table IV
    add_tbl_hdr("IV", "Safe Haven Categories and Baseline Guardianship Weights")
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

    add_h2("G. SOS Alerting and Red-Zone Dwell Escalation")
    add_para("Users can add one to five emergency contacts, marking one as primary. The manual SOS trigger requires a continuous two-second button press and provides a five-second cancel countdown to stop false dispatches. Activation sends an emergency alert with coordinates, timestamps, and zone status to contacts and the analyst console via Twilio or local provider abstractions.")
    add_para("The automated escalation path handles emergencies where victims cannot operate their handsets. While the app is open and location sharing is active, client heartbeats send coordinates every 30 seconds. A per-user finite state machine (Fig. 6) transitions from SAFE to IN_RED upon entering a red zone. If stationary for T minutes (default 10, configurable from 5 to 30 min) without touch input, an 'Are you safe?' prompt rings for 60 seconds. If unanswered, an automated emergency payload is sent to primary contacts with last known coordinates. A 30-minute cooldown prevents repeated alerts.")
    add_pic("fig6_state_machine.png", "6", "Red-zone dwell and inactivity state machine for automated emergency escalation.")

    add_h2("H. Privacy, Consent, and Security Safeguards")
    add_para("GPS coordinates are sensitive personal information [40]. In CrimeSense, location capture requires explicit user consent, and administrative live map tracking functions only for consenting accounts with active heartbeats, logging every view event immutably. Turning off location sharing suspends heartbeats and dwell alerting while leaving manual search operative. Sign-in supports salted password hashes and Google OAuth with audience and verified email validation [41]. The architecture aligns with India's Digital Personal Data Protection Act [42], supporting complete data deletion upon request.")

    # =========================================================================
    # IV. IMPLEMENTATION STATUS AND VERIFICATION
    # =========================================================================
    add_h1("IV. IMPLEMENTATION STATUS AND VERIFICATION")
    add_para("Table V summarizes the current state of system components. Verified components have passed test scripts and health queries, partial components are functional but awaiting field deployment, while designed and planned modules represent theoretical formulations.")

    # Table V
    add_tbl_hdr("V", "Implementation Status of CrimeSense System Components")
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
        ("Email signup and login", "Verified", "End-to-end flow verification tests"),
        ("Role separated access guard", "Partial", "Roles stored; access middleware active"),
        ("Google OAuth 2.0 integration", "Verified", "Sign-in test script and deduplication"),
        ("Admin KPIs, charts, and CRUD", "Verified", "Database-backed live queries"),
        ("Consent gated live map, audit log", "Verified", "Audit trail records verified"),
        ("Contacts, saved places persistence", "Verified", "Full flow database test scripts"),
        ("Notification provider (Twilio/Log)", "Partial", "Local logging tested; live trial pending"),
        ("Red-zone dwell state monitoring", "Partial", "State table verified; hardware trial pending"),
        ("Zone classification with Table II", "Designed", "Formulated; parameter tuning pending"),
        ("Hotspot clustering (DBSCAN)", "Partial", "KPI uses coordinate aggregation proxy"),
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

    add_para("System verification executed on 11 October 2026 confirmed 596 crime rows in SQLite, single administrator initialization, and 11 relational tables. In this audit, 'verified' indicates that each record has a validated source news URL, geocoded coordinates inside study bounds, standardized dates, and zero duplicate articles. The health endpoint returned database connected status with zero lingering test records.")

    # Table VI
    add_tbl_hdr("VI", "Verification Summary of the Crimes Table (N = 596)")
    t6 = doc.add_table(rows=11, cols=2)
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
        ("Unique coordinate pairs (entire dataset)", "25 unique coordinates (16 in Vellore district)"),
        ("Primary centroid concentration", "469 of 596 records (78.69%) at (12.9165, 79.1325)"),
        ("District distribution", "552 Vellore (92.62%), 44 regional/external (7.38%)"),
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

    # =========================================================================
    # V. DATASET AND CURRENT RESULTS
    # =========================================================================
    add_h1("V. DATASET AND CURRENT RESULTS")
    add_para("The database contains 596 verified crime incidents. Fig. 7(a) depicts the categorical breakdown: general offenses comprise 277 records (46.5%), followed by murder and homicide (49), contraband and smuggling (46), a distinct murder tag (37), and cyber fraud (28). Fig. 7(b) displays the risk split: 25.2% High risk, 23.2% Medium risk, and 51.7% Low risk.")
    add_pic("fig7_dataset_charts.png", "7", "Current database summary: (a) crime-type labels; (b) risk-level split.")
    add_para("Four critical observations follow from these empirical figures. First, the dominance of general offenses (46.5%) highlights the necessity of finer taxonomies for granular recurrence modeling. Second, merging overlapping murder labels consolidates 86 severe offenses under a single tag. Third, geocoding operates at locality scale: 469 out of 596 records (78.69%) share the central coordinate pair (12.9165, 79.1325) representing generic 'Vellore' or 'Vellore District' references in news reporting, yielding only 25 unique coordinate pairs across the entire database (and 16 within Vellore district). This creates a sharp spatial cliff: a query within 1000 m of this centroid aggregates 477 incidents (raw score > 1900), saturating the zone score to 100.0 (Red), whereas moving just 100 m further (1100 m from the centroid) drops the incident count to 8 and the score to 10.5 (Green). The model in its current form functions as a categorical proximity detector to known geocoded locality centroids, rather than a continuous micro-place risk field. Fourth, the database includes 44 records from neighboring or external districts (Chennai 16, Ranipet 13, Tiruvannamalai 5, etc.) that should be filtered when conducting pure municipal Vellore analysis.")

    # =========================================================================
    # VI. PROPOSED EVALUATION PROTOCOL
    # =========================================================================
    add_h1("VI. PROPOSED EVALUATION PROTOCOL")
    add_para("To ensure reproducible benchmarking, evaluation metrics and thresholds are pre-defined (Table VII). Predictive evaluations use rolling temporal splits: records before cutoff date t0 form the training surface, and incidents in the subsequent three months serve as test sets. On a 500 m grid, hit rate measures the fraction of test incidents falling within red cells, compared via the Predictive Accuracy Index [5]:")
    add_eq("PAI = (n / N) / (a / A)", "8")
    add_para("where n of N test crimes fall in red cells covering area a out of total area A. Thresholds are calibrated on initial splits and reported where red cells cover at most 10% of the urban terrain.")

    # Table VII
    add_tbl_hdr("VII", "Standardized Experimental Evaluation Protocol")
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
        ("Recurrence", "Near repeat ratio; permutation p (999 runs); lift", "Candidate space-time windows on deduplicated data"),
        ("Haven finder", "Valid@5 accuracy; median walk to first open haven", "Field verification audit across sampled query points"),
        ("SOS escalation", "Trigger to dispatch latency (p50, p95); false alarms", "Scripted GPS trajectory playback on sandbox database"),
        ("Access control", "Cross-account reads blocked; 403 on admin routes", "Two test resident accounts plus one administrator"),
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

    # =========================================================================
    # VII. DISCUSSION
    # =========================================================================
    add_h1("VII. DISCUSSION")
    add_h2("A. What Is New")
    add_para("Core elements of spatial crime analysis, near repeat testing, safe routing, and emergency alerting possess established research literatures. CrimeSense organizes these concepts around a single shared evidence base. The current database supports the administrative dashboard. The proposed resident advisory, safe-haven finder, and automated red-zone escalation would use the same incident records if implemented and validated. The haven finder and pre-visit advisory are designed to convert spatial data into immediate pedestrian guidance, while dwell escalation aims to address scenarios where victims are physically incapacitated.")

    add_h2("B. Ethics and Responsible Use")
    add_para("Assigning risk labels to urban sectors risks stigmatizing communities and amplifying data biases [30], [31], [32]. CrimeSense mitigates these harms by framing zones objectively as 'reported incidents', displaying report counts and source links transparently, avoiding pejorative terms like 'unsafe', stating clearly that green zones do not guarantee absolute safety, and excluding automated outputs from punitive policing loops [32]. Confirmation challenges and cooldown timers prevent alert fatigue.")

    add_h2("C. Limitations and Threats to Validity")
    add_para("News sourced datasets reflect journalistic coverage choices, which over represent unusual or severe offenses relative to minor infractions [11]. Locality centroid coordinates limit spatial precision [24], [25]. The severity score table is expert assigned rather than calibrated on longitudinal outcome metrics. OpenStreetMap haven records inherit volunteer mapping variations, and automated browser push notifications depend upon active browser lifecycles and mobile connectivity.")

    # =========================================================================
    # VIII. CONCLUSION AND FUTURE WORK
    # =========================================================================
    add_h1("VIII. CONCLUSION AND FUTURE WORK")
    add_para("This study presents CrimeSense, a prototype for visualizing news-reported crime incidents in Vellore. The database structure and selected application functions were verified using 596 records. The resident safety modules and pattern-recurrence methods remain to be evaluated as described in the implementation-status and evaluation sections. Database integrity, authentication, and persistence have been verified, while role enforcement remains partially active. Future work will execute rolling temporal evaluations, refine geocoding resolution, conduct physical safe haven audits, and evaluate user cognitive load through structured field usability trials.")

    # =========================================================================
    # REFERENCES
    # =========================================================================
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

    paper_dir = os.path.dirname(OUT_PATH)
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    
    candidates = [
        ("CrimeSense_IEEE_Paper_IIT_Kanpur_Final.docx", OUT_PATH, DESKTOP_PATH),
        ("CrimeSense_IEEE_Paper_IIT_Kanpur_Latest.docx", os.path.join(paper_dir, "CrimeSense_IEEE_Paper_IIT_Kanpur_Latest.docx"), os.path.join(desktop_dir, "CrimeSense_IEEE_Paper_IIT_Kanpur_Latest.docx")),
        ("CrimeSense_IEEE_Paper_IIT_Kanpur_NoGaps.docx", os.path.join(paper_dir, "CrimeSense_IEEE_Paper_IIT_Kanpur_NoGaps.docx"), os.path.join(desktop_dir, "CrimeSense_IEEE_Paper_IIT_Kanpur_NoGaps.docx")),
        ("CrimeSense_IEEE_0PercentAI_IIT_Kanpur.docx", OUT_PATH_ORIG, DESKTOP_PATH_ORIG),
    ]

    saved_paths = []
    for name, r_path, d_path in candidates:
        try:
            doc.save(r_path)
            saved_paths.append(r_path)
            print(f"Successfully saved repo copy: {r_path}")
        except Exception as e:
            print(f"Could not save repo copy for {name}: {e}")

        try:
            doc.save(d_path)
            saved_paths.append(d_path)
            print(f"Successfully saved desktop copy: {d_path}")
        except Exception as e:
            print(f"Could not save desktop copy for {name}: {e}")

    print("Successfully built fully aligned, evidence-grounded IEEE document!")
    print(f"Total active saved targets: {len(saved_paths)}")

if __name__ == "__main__":
    build_paper()
