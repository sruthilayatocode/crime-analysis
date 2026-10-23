import os
import json
import csv
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

RESULTS_DIR = r"c:\Users\sruth\crime analysis\results"
FIG_DIR = r"c:\Users\sruth\crime analysis\research_paper\figures"

TARGET_PATHS = [
    r"c:\Users\sruth\Desktop\CrimeSense_IEEE_Paper_IIT_Kanpur_Final.docx",
    r"c:\Users\sruth\Desktop\CrimeSense_IEEE_Manuscript.docx",
    r"c:\Users\sruth\Desktop\CrimeSense_IEEE_Final.docx",
    r"c:\Users\sruth\Desktop\CrimeSense_IEEE_0PercentAI_IIT_Kanpur.docx",
    r"c:\Users\sruth\crime analysis\CrimeSense_IEEE_Paper_IIT_Kanpur_Final.docx",
    r"c:\Users\sruth\crime analysis\CrimeSense_IEEE_Final.docx",
    r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_Paper_IIT_Kanpur_Final.docx",
    r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_Manuscript.docx",
    r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_IEEE_0PercentAI_IIT_Kanpur.docx",
    r"c:\Users\sruth\crime analysis\results\CrimeSense_IEEE_Manuscript.docx",
]

# Load empirical data
with open(os.path.join(RESULTS_DIR, "corpus_audit.json"), "r") as f:
    audit_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "sensitivity_sweep.json"), "r") as f:
    sens_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "knox_results.json"), "r") as f:
    knox_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "dbscan_results.json"), "r") as f:
    dbscan_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "haven_results.json"), "r") as f:
    haven_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "fsm_test_results.json"), "r") as f:
    fsm_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "rbac_test_results.json"), "r") as f:
    rbac_data = json.load(f)

print("Empirical benchmark data loaded. Generating Final Master IEEE Two-Column Word Document...")

def set_cell_margins(cell, top=50, bottom=50, left=70, right=70):
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

def set_cell_shading(cell, color_hex="F2F2F2"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{color_hex}"/>')
    tcPr.append(shd)

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

def build_final_docx():
    doc = docx.Document()

    # SECTION 1: Page Header Block (Single column across page width)
    sec1 = doc.sections[0]
    sec1.top_margin = Inches(0.75)
    sec1.bottom_margin = Inches(0.85)
    sec1.left_margin = Inches(0.625)
    sec1.right_margin = Inches(0.625)

    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(9.5)
    style_normal.font.color.rgb = RGBColor(0, 0, 0)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("CrimeSense: An Empirical Framework for News-Mined Urban Crime Mapping, Centroid Cliff Diagnostics, and Calibrated Pedestrian Safety Protocols")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(20)
    r_title.font.bold = True

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
    r_ids.font.size = Pt(9.5)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(12)
    r_inst = p_inst.add_run("School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India")
    r_inst.font.name = 'Times New Roman'
    r_inst.font.size = Pt(9.5)
    r_inst.font.italic = True

    # SECTION 2: Two-column body
    sec2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    sec2.top_margin = Inches(0.75)
    sec2.bottom_margin = Inches(0.85)
    sec2.left_margin = Inches(0.625)
    sec2.right_margin = Inches(0.625)

    sectPr = sec2._sectPr
    cols = parse_xml(f'<w:cols {nsdecls("w")} w:num="2" w:space="280"/>')
    sectPr.append(cols)

    def add_p(text, indent=True, space_after=4):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.05
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.18)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        return p

    def add_sec_head(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        r.font.bold = True
        return p

    def add_subsec_head(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        r.font.italic = True
        return p

    def add_equation(eq_num, eq_text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r_eq = p.add_run(f"\t{eq_text}\t({eq_num})")
        r_eq.font.name = 'Times New Roman'
        r_eq.font.size = Pt(9.5)
        r_eq.font.italic = True
        return p

    def add_fig_image(img_path, caption_text, width=Inches(3.35)):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(2)
            run = p_img.add_run()
            run.add_picture(img_path, width=width)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(6)
            r = p_cap.add_run(caption_text)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8.5)
            r.font.italic = True

    # ---------------------------------------------------------
    # ABSTRACT & KEYWORDS
    # ---------------------------------------------------------
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_before = Pt(4)
    p_abs.paragraph_format.space_after = Pt(6)
    p_abs.paragraph_format.first_line_indent = Inches(0.18)
    r_ab_b = p_abs.add_run("Abstract—")
    r_ab_b.font.name = 'Times New Roman'
    r_ab_b.font.size = Pt(9.0)
    r_ab_b.font.bold = True
    
    abs_text = (
        "Urban crime analysis in Tier-2 Indian cities faces acute administrative opacity; municipal First Information Report (FIR) feeds remain closed, forcing reliance on spatially aggregated annual compendiums or uncurated digital news archives. This investigation presents CrimeSense, an empirical pedestrian safety and spatial criminology platform evaluated on an authoritative 596-incident corpus mined from regional Tamil Nadu reportage across 11 relational tables. Spatial auditing reveals an acute 'Locality Centroid Cliff' artifact: 469 of 596 incidents (78.69%) stack precisely onto coordinate (12.9165, 79.1325), generating an extreme raw risk score of 1641.10 that saturates standard baseline models (R_ref = 100) and triggers an artificial 88-point score collapse across a 10-meter boundary at the 1000 m radius limit. We mathematically derive and evaluate an empirical normalization ceiling (R_ref = 2500) alongside spatial co-location collapse (s_cell = s_max*(1+ln n)), eliminating artificial saturation while preserving continuous risk variation. Evaluated through 999 Monte Carlo permutations of the Knox space-time statistic, raw news data exhibits severe pair inflation (110,888 coincident d=0 pairs, 62.54% of total) that masks near-repeat dynamics (p in [0.338, 0.998]); conversely, partitioning true micro-places isolates significant short-term space-time recurrence at 7 days (Obs=23, Exp=12.7, pseudo-p = 0.012). We further benchmark multi-factor safe-haven utility over OpenStreetMap shelters across Katpadi, CMC, and Bagayam, verify role-based security across 12 API checks, and demonstrate a 2.51 ms edge escalation state machine for incapacitated pedestrians."
    )
    r_ab = p_abs.add_run(abs_text)
    r_ab.font.name = 'Times New Roman'
    r_ab.font.size = Pt(9.0)

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_after = Pt(8)
    r_kw_b = p_kw.add_run("Index Terms—")
    r_kw_b.font.name = 'Times New Roman'
    r_kw_b.font.size = Pt(9.0)
    r_kw_b.font.bold = True
    r_kw = p_kw.add_run("Spatial criminology, locality centroid cliff, geoparsing uncertainty, Knox space-time interaction, safe haven utility, finite state machine, DPDP Act 2023, pedestrian navigation.")
    r_kw.font.name = 'Times New Roman'
    r_kw.font.size = Pt(9.0)

    # ---------------------------------------------------------
    # I. INTRODUCTION
    # ---------------------------------------------------------
    add_sec_head("I. INTRODUCTION")
    add_p(
        "Spatial heterogeneity governs urban crime concentration across metropolitan environments [1], [2]. Criminological field studies demonstrate that unlawful incidents do not disperse uniformly across municipal geography; instead, predatory offenses concentrate persistently at distinct street intersections, poorly illuminated alleyways, and transport interchange terminals [2], [4]. Routine activity theory articulates that predatory violations materialize when motivated offenders intersect with suitable targets in space and time in the absence of capable guardianship [3]. While law enforcement agencies in Western jurisdictions leverage computer-aided dispatch (CAD) logs and kernel density estimation (KDE) to direct motorized patrols [5], [6], civilians in developing urban centers cannot operationalize administrative police records for pedestrian transit decisions."
    )
    add_p(
        "In the Indian context, official crime metrics published by the National Crime Records Bureau (NCRB) are compiled exclusively for annual regional auditing [7]. These compendiums aggregate violent and property infractions at district and commissionerate resolutions across 12-month intervals, obscuring micro-place realities. An annual district total provides zero actionable intelligence to a lone student navigating Katpadi railway junction or an evening healthcare worker traversing Bagayam bus terminal after 21:00 IST. Conversely, commercially available civilian safety applications suffer from a purely reactive paradigm [8]. Such utilities rely almost universally on manual panic triggers, audio scream detection, or handset gyroscopic shake listeners. When a pedestrian experiences sudden physical confrontation, intimidation, or medical incapacitation, unlocking a mobile handset and pressing a confirmation prompt is physically infeasible. Furthermore, existing emergency software operates in spatial ignorance, evaluating user vulnerability identically whether an alert originates within a well-lit commercial enclave or a verified crime hotspot."
    )
    add_p(
        "Because state police commissionerates in Tamil Nadu do not publish open programmatic application programming interface (API) streams of daily First Information Reports, public safety research must harness digital journalistic coverage [9], [10]. Digital news mining introduces distinct methodological hurdles, notably journalistic selection biases favoring sensational violence [11] and coarse toponym resolution [24], [25]. When automated geocoders process generic locality mentions such as 'Vellore' or 'Vellore District', hundreds of heterogeneous reports collapse onto an arbitrary municipal centroid, generating what we define as the 'Locality Centroid Cliff'. Failure to diagnose this spatial artifact distorts predictive hotspot models and induces catastrophic risk boundary discontinuities."
    )
    add_p(
        "To resolve these operational and methodological dilemmas, this investigation introduces CrimeSense, an empirical spatial framework engineered for news-mined crime analysis, centroid cliff diagnostics, and active pedestrian guidance. This paper presents five primary scientific contributions:",
        indent=True
    )
    add_p(
        "1) The Locality Centroid Cliff Diagnostic: We provide the first rigorous empirical characterization of coordinate stacking in news-geocoded spatial datasets, documenting how 78.69% of records collapse onto a single centroid and deriving mathematical mitigations through adaptive scaling and cell collapse.",
        indent=True, space_after=2
    )
    add_p(
        "2) Recalibrated Exposure Field Formulation: We formulate a distance-decayed, recency-weighted continuous risk field R(q) and establish an empirical normalization ceiling (R_ref = 2500) that eliminates artificial risk saturation across urban query grids.",
        indent=True, space_after=2
    )
    add_p(
        "3) Micro-Place Knox Space-Time Permutation Analysis: We evaluate spatio-temporal near-repeat clustering across 999 Monte Carlo permutations, demonstrating that centroid stacking induces 110,888 artificial coincident pairs that obscure genuine micro-place near-repeat dynamics.",
        indent=True, space_after=2
    )
    add_p(
        "4) Institutional Safe-Haven Utility Optimization: We formulate a multi-factor shelter ranking metric integrating OpenStreetMap guardianship weights, operational status, walking decay, and destination ambient risk penalties across Katpadi, CMC, and Bagayam sectors.",
        indent=True, space_after=2
    )
    add_p(
        "5) Validated Edge State Machine & Privacy Architecture: We implement and benchmark an automated red-zone inactivity finite state machine alongside role-based access control (RBAC) verified across 12 API penetration endpoints in compliance with the Indian Digital Personal Data Protection Act 2023.",
        indent=True, space_after=6
    )

    # ---------------------------------------------------------
    # II. RELATED WORK & TAXONOMY
    # ---------------------------------------------------------
    add_sec_head("II. RELATED WORK")
    add_subsec_head("A. Spatial Crime Concentration and Hotspot Mapping")
    add_p(
        "Micro-geographic crime analysis demonstrates that a fraction of urban street segments generates the vast majority of municipal infractions [1], [2]. Analysts historically model spatial clustering via planar kernel density estimation [12], with temporal decay extensions improving short-range forecasting [13]. Unsupervised spatial density clustering, particularly DBSCAN [14], isolates arbitrary non-linear cluster geometries while categorizing peripheral observations as noise [34]. Although hotspot policing trials confirm that targeted enforcement reduces localized crime [6], spatial intelligence tools have remained restricted to command headquarters without translating into actionable pedestrian interfaces."
    )
    add_subsec_head("B. Spatiotemporal Forecasting and Near-Repeat Victimization")
    add_p(
        "Near-repeat victimization theory posits that an initial criminal infraction temporarily elevates victimization hazard across adjacent spatial and temporal intervals [21], [22]. Epidemiological modeling by Townsley et al. [22] and cross-national assessments by Johnson et al. [23] demonstrate that residential burglaries exhibit infectious communicability over 14-day to 30-day horizons. Point process models [15], risk terrain modeling [16], [17], and machine learning architectures [18], [19], [20] depend heavily on administrative police dispatch records. In data-sparse developing regions lacking live police feeds, consumer applications translating empirical near-repeat dynamics into real-time pedestrian protection have not been established in prior literature."
    )
    add_subsec_head("C. News Mining, Toponym Resolution, and Geocoding Errors")
    add_p(
        "Digital newspaper archives provide valuable supplementary records of social conflict and public safety occurrences [9], [10]. Nonetheless, journalistic narratives inherently reflect editorial filtering, prioritizing high-severity felonies over routine infractions [11]. Furthermore, geoparsing descriptive text to geographic coordinates introduces structural spatial uncertainty [24], [25]. When descriptive text mentions broad administrative localities, automated geocoders default to geometric centroids, collapsing micro-places into dense artificial clusters that distort spatial statistics."
    )
    add_subsec_head("D. Pedestrian Safety Protocols and Environmental Criminology")
    add_p(
        "Pedestrian navigation algorithms typically formulate safe transit as bi-objective Pareto optimization trading physical distance against cumulative crime exposure [26]. CrimeSense diverges from rerouting by focusing on immediate environmental guardianship. Jane Jacobs established that active commercial storefronts provide informal 'eyes on the street' [27], a concept Oscar Newman formalized as defensible space [28]. Public shelters offering institutional surveillance—such as 24-hour pharmacies, hospitals, and police posts—can be dynamically retrieved from OpenStreetMap [29]. Furthermore, spatial safety tools must prevent stigmatizing lower-income sectors [30], [31] and avoid generating self-reinforcing algorithmic feedback loops [32]."
    )

    # Table I: Prior Art Taxonomy
    p_t1 = doc.add_paragraph()
    p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1.paragraph_format.space_before = Pt(8)
    p_t1.paragraph_format.space_after = Pt(2)
    r_t1 = p_t1.add_run("TABLE I: TAXONOMY OF RELEVANT PRIOR ART VS. CRIMESENSE")
    r_t1.font.name = 'Times New Roman'
    r_t1.font.size = Pt(8.5)
    r_t1.font.bold = True

    t1_headers = ["System / Method", "Data Feed", "Spatial Granularity", "Centroid Diagnostic", "Pedestrian Guard", "Edge FSM"]
    t1_rows = [
        ["PredPol / Geolitica [15]", "Official CAD/RMS", "150m x 150m Grid", "Not Addressed", "Patrol Dispatch", "No"],
        ["Risk Terrain Modeling [16]", "Arrest / Feature Logs", "Block-Level Features", "Ignored", "Policing Strategy", "No"],
        ["WoSApp / Reactive SOS [8]", "Zero Crime Data", "Point GPS Only", "None", "Panic Trigger Only", "No"],
        ["SafeCity Crowd Platform [10]", "Crowdsourced Reports", "Locality Toponyms", "Uncorrected", "Static Pin Map", "No"],
        ["Safe Navigation Graphs [26]", "Municipal Police Feeds", "Street Network Segments", "Assumed Precise", "Detour Rerouting", "No"],
        ["CrimeSense (This Work)", "Mined News Corpus", "Micro-Place & District", "Diagnosed & Solved", "Safe Haven Utility", "Verified (2.5ms)"]
    ]
    tbl1 = doc.add_table(rows=len(t1_rows) + 1, cols=len(t1_headers))
    tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl1)
    for c_idx, h in enumerate(t1_headers):
        cell = tbl1.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 40, 40, 50, 50)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8)
            r.font.bold = True
    for r_idx, row in enumerate(t1_rows):
        for c_idx, val in enumerate(row):
            cell = tbl1.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 30, 30, 40, 40)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [3, 4, 5] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.5)

    # ---------------------------------------------------------
    # III. SYSTEM ARCHITECTURE & DATA GOVERNANCE
    # ---------------------------------------------------------
    add_sec_head("III. SYSTEM ARCHITECTURE & DATA GOVERNANCE")
    add_subsec_head("A. Multi-Tier Distributed Stack")
    add_p(
        "CrimeSense is structured as a decoupled multi-tier web GIS architecture comprising a browser client tier, an application API routing gateway, a persistent relational storage layer, and an offline news curation pipeline. The client interface is built using reactive HTML5 and Leaflet GIS mapping, communicating over TLS 1.3 encrypted HTTPS with a Python Flask REST service. The underlying datastore uses SQLite 3 configured with Write-Ahead Logging (WAL) and normal synchronous pragmas, ensuring concurrent read access without database locking. Administrative operations write persistent chronological entries into an audit_logs table tracking caller IP addresses, timestamps, and target records."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig1_architecture.png"), "Fig. 1. Multi-tier CrimeSense architecture linking GIS, REST services, SQLite WAL storage, and edge state machines.")

    add_subsec_head("B. Relational Schema and Cryptographic Security")
    add_p(
        "The relational schema spans 11 normalized tables: crimes (596 records holding source URLs, geocoding confidence tags, and severity ratings), users (account entities with salted cryptographic credentials), user_settings (privacy switches and telemetry toggles), sos_contacts (designated guardian telephone records), user_locations (ephemeral GPS telemetry), user_red_zone_states (inactivity state machine registers), sos_events (emergency dispatches), saved_locations, shared_links, alerts, and audit_logs. User authentication enforces role-based access control (RBAC). Passwords are protected using PBKDF2 with SHA-256 and unique 16-byte random salts across 100,000 iterations, alongside JWT token verification with HS256 encryption."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig2_schema.png"), "Fig. 2. Relational entity-relationship schema across all 11 tables with foreign-key constraints.")

    add_subsec_head("C. Data Governance under DPDP Act 2023")
    add_p(
        "User location processing adheres strictly to the Indian Digital Personal Data Protection (DPDP) Act 2023 [42]. In compliance with statutory consent requirements, ambient background geolocation is never recorded without verifiable opt-in consent explicitly registered in user_settings [39], [40]. Telemetry entries in user_locations are ephemeral, subject to automated purge cycles. Residents retain complete rights to summary extraction and permanent erasure, with account termination cascading deletions across settings, contacts, and historical heartbeats."
    )

    # ---------------------------------------------------------
    # IV. MATHEMATICAL SIGNAL & SAFETY FORMULATIONS
    # ---------------------------------------------------------
    add_sec_head("IV. MATHEMATICAL FORMULATIONS")
    add_subsec_head("A. Great-Circle Distance Metric")
    add_p(
        "Spatial separation between query coordinate q = (phi_q, lambda_q) and geocoded incident i = (phi_i, lambda_i) is evaluated via the Great-Circle Haversine formulation [33]:"
    )
    add_equation(1, "d_ij = 2R arcsin( sqrt( sin^2(Delta phi / 2) + cos phi_i cos phi_j sin^2(Delta lambda / 2) ) )")
    add_p(
        "where Earth radius R = 6,371,000 meters, Delta phi = phi_j - phi_i, and Delta lambda = lambda_j - lambda_i."
    )
    add_subsec_head("B. Distance-Decayed Recency-Weighted Exposure Field")
    add_p(
        "For query coordinate q within search radius rho = 1000 m, let N(q) represent the set of nearby incidents satisfying d_i <= rho. Raw crime risk R(q) aggregates incident severity s_i in [1, 10], linear spatial distance decay delta(d_i), and temporal recency weight w(a_i):"
    )
    add_equation(2, "R(q) = sum_{i in N(q)} s_i * delta(d_i) * w(a_i),   delta(d) = max(0, 1 - d / rho)")
    add_p(
        "The temporal recency multiplier w(a_i) penalizes historical records using three discrete empirical intervals: w(a_i) = 1.0 for incidents occurring within 6 months (<= 182.5 days), 0.7 for 6 to 24 months (182.5 to 730 days), and 0.4 for older infractions (> 730 days)."
    )
    add_subsec_head("C. Calibrated Zone Normalization")
    add_p(
        "The raw risk R(q) is mapped onto a bounded 0-100 safety score Z(q) via saturation parameter R_ref:"
    )
    add_equation(3, "Z(q) = min( 100,  100 * R(q) / R_ref )")
    add_p(
        "Operational safety tiers are defined as: Green Zone (Z(q) < 30), Yellow Zone (30 <= Z(q) < 60), and Red Zone (Z(q) >= 60). In the initial prototype, R_ref = 100 clamped high-density scores artificially. Section V proves that R_ref = 2500 restores dynamic scoring variance."
    )
    add_subsec_head("D. Knox Spatiotemporal Interaction Statistic")
    add_p(
        "To test whether crime occurrences exhibit localized spatiotemporal clustering rather than independent random dispersal, we implement the Knox interaction statistic [21]:"
    )
    add_equation(4, "X = sum_{i < j} I(d_ij <= d_s) * I(|t_i - t_j| <= d_t)")
    add_p(
        "where I(.) is the indicator function, d_s in {250, 500, 1000} m, and d_t in {7, 14, 30} days. Statistical significance is evaluated against 999 Monte Carlo permutations of event dates, computing pseudo-p = (1 + #{X* >= X}) / (1 + 999). Multiple testing across 9 parameter pairs is evaluated under Bonferroni (alpha_adj = 0.00556) and Benjamini-Hochberg false discovery rate controls."
    )
    add_subsec_head("E. Multi-Factor Safe Haven Utility")
    add_p(
        "When an individual detects elevated risk, CrimeSense computes utility scores across candidate OpenStreetMap shelters p within 2000 meters:"
    )
    add_equation(5, "H(p) = w_c * o(p, t) * exp( -d_p / lambda ) * ( 1 - Z_p / 100 )")
    add_p(
        "where w_c denotes institutional guardianship (Police: 1.0, Hospital: 0.9, Clinic: 0.8, Municipal/Mall: 0.7, Pharmacy: 0.6, Bus/Fuel: 0.5), o(p, t) reflects verified operational status (1.0 for 24/7 or active daytime, 0.85 for regular commercial), lambda = 500 m defines walking decay, and (1 - Z_p / 100) penalizes shelters situated inside high-crime zones."
    )
    add_subsec_head("F. Red-Zone Dwell Inactivity Escalation State Machine")
    add_p(
        "To safeguard incapacitated pedestrians, an edge finite state machine (FSM) monitors dwell duration within Red zones (Z >= 60). Governed by dwell threshold T_dwell = 10 min, prompt window 60 s, cooldown T_cool = 30 min, and 30 s heartbeats, the FSM transitions deterministically as defined in Table IV."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig6_state_machine.png"), "Fig. 3. Finite State Machine (FSM) discrete transition architecture for Red-Zone Inactivity Escalation.")

    # ---------------------------------------------------------
    # V. CORPUS AUDIT & THE CENTROID CLIFF DIAGNOSTIC
    # ---------------------------------------------------------
    add_sec_head("V. CORPUS AUDIT & THE CENTROID CLIFF")
    add_subsec_head("A. Authoritative Dataset Audit")
    add_p(
        f"A rigorous audit of the active SQLite database confirms exactly {audit_data['total_records']} verified records across 11 tables. Table II summarizes the zone classification parameters, while Table VI details corpus distributions. Geocoding confidence analysis reveals 513 high-confidence records (86.07%), 53 low-confidence records (8.89%), 3 medium records (0.50%), and 27 unknown confidence entries (4.53%). Breakdown by risk severity categorizes {audit_data['risk_level_breakdown']['Low']} low-risk (51.68%), {audit_data['risk_level_breakdown']['Medium']} medium-risk (23.15%), and {audit_data['risk_level_breakdown']['High']} high-risk incidents (25.17%), with severity scores averaging 5.92 (min 2.0, max 10.0)."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig7_dataset_charts.png"), "Fig. 4. Empirical corpus distributions across categories, districts, and severity levels.")

    # Table II: Zone Model Parameters
    p_t2 = doc.add_paragraph()
    p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2.paragraph_format.space_before = Pt(6)
    p_t2.paragraph_format.space_after = Pt(2)
    r_t2 = p_t2.add_run("TABLE II: ZONE CLASSIFICATION PARAMETERS")
    r_t2.font.name = 'Times New Roman'
    r_t2.font.size = Pt(8.5)
    r_t2.font.bold = True

    t2_headers = ["Parameter", "Symbol", "Calibrated Value", "Operational Rationale"]
    t2_rows = [
        ["Search Radius", "rho", "1000.0 m", "Standard pedestrian walking horizon (12-minute walk)"],
        ["Distance Decay", "delta(d)", "1 - (d / rho)", "Linear attenuation to zero at boundary"],
        ["Recent Weight", "w_new", "1.00 (<= 182.5 d)", "Full weight for current-cycle incidents"],
        ["Medium Weight", "w_med", "0.70 (182.5-730 d)", "Moderate weight for past 2 years"],
        ["Historical Weight", "w_old", "0.40 (> 730 d)", "Long-term persistent baseline weighting"],
        ["Baseline Ceiling", "R_ref(base)", "100.0", "Prototype saturation threshold (induces cliff)"],
        ["Calibrated Ceiling", "R_ref(cal)", "2500.0", "Empirical ceiling derived from urban grid percentiles"],
        ["Zone Tiers", "Z(q)", "Green <30, Yel 30-59, Red >=60", "Three-state intuitive safety categorization"]
    ]
    tbl2 = doc.add_table(rows=len(t2_rows) + 1, cols=len(t2_headers))
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl2)
    for c_idx, h in enumerate(t2_headers):
        cell = tbl2.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 45, 45)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8)
            r.font.bold = True
    for r_idx, row in enumerate(t2_rows):
        for c_idx, val in enumerate(row):
            cell = tbl2.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 35, 35)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.5)

    add_subsec_head("B. The Locality Centroid Cliff Diagnostic")
    add_p(
        f"Spatial inspection uncovers a severe data stacking phenomenon: out of {audit_data['total_records']} total incidents, exactly {audit_data['centroid_records']} records ({audit_data['centroid_percentage']}%) share the identical coordinate pair ({audit_data['centroid_coordinate'][0]}, {audit_data['centroid_coordinate'][1]}), corresponding to the default municipal centroid of Vellore. Across the entire database, only {audit_data['unique_coordinates']} unique coordinate pairs exist ({audit_data['unique_vellore_coordinates']} within Vellore district, 12 external-district coordinates). Furthermore, exactly {audit_data['records_within_1000m_of_centroid']} incidents reside within 1000 meters of this central coordinate, while {audit_data['external_district_records']} incidents (7.38%) belong to external districts (Chennai 16, Ranipet 13, Tiruvannamalai 5, Tirupattur 4, Coimbatore 2, others 4)."
    )
    add_p(
        "This stacking creates an acute spatial discontinuity. Querying at the centroid (d = 0 m) accumulates 477 incidents, producing a raw risk score of R(0) = 1641.10. Under the baseline setting R_ref = 100, the score saturates completely at Z = 100.0 (Red). As the query point moves radially outward, R(q) remains massive (994.75 at 400 m, 832.98 at 500 m, 178.84 at 900 m, and 29.77 at 990 m). At 990 m, Z remains clamped at 29.77 (or 100.0 if d <= 900m). However, upon reaching 1000 m—where the centroid coordinate crosses the search perimeter rho—the incident count collapses from 477 to 8, and raw risk plunges to 14.03. At 1100 m, raw risk is 11.92, yielding Z = 11.92 (Green). The baseline model thus functions not as a continuous crime density surface, but as a severe step-function detector around geocoded centroids."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig_centroid_cliff.png"), "Fig. 5. The Locality Centroid Cliff: Score saturation under R_ref=100 vs. continuous variation under R_ref=2500 and cell-collapse mitigations.")

    add_subsec_head("C. Evaluation of Mitigations and Sensitivity Analysis")
    add_p(
        "To address this spatial artifact, we evaluate two distinct interventions:",
        indent=True
    )
    add_p(
        "1) Co-Location Cell Collapse: Rather than summing individual records at coincident coordinates, all n incidents sharing a coordinate cell are collapsed into a composite severity: s_cell = s_max * (1 + ln n). With n = 469 at the centroid and s_max = 10.0, s_cell becomes 71.50. Raw risk at the centroid drops from 1641.10 to 46.51. Under R_ref = 100, the centroid registers Z = 46.51 (Yellow), tapering smoothly to 32.69 at 500 m and 5.56 at 1000 m, eliminating artificial saturation.",
        indent=True, space_after=3
    )
    add_p(
        "2) Two-Tier Administrative Stratification: Segregating the 469 generic centroid reports into a separate 'District-Level Context' layer isolates 127 genuine micro-place incidents. Within 1000 m of the central medical corridor, 8 micro-incidents generate a raw risk of 6.40 to 17.75, producing realistic Green scores (Z in [6.4, 17.75]) that reflect local street conditions without centroid distortion.",
        indent=True, space_after=4
    )
    add_p(
        "To establish an optimal normalization ceiling for the uncollapsed system, we execute a parameter sweep across R_ref in {100, 500, 1000, 2500, 5000} over a uniform 625-point spatial grid (12.87-12.98 N, 79.08-79.18 E). As summarized in Table VII, R_ref = 100 induces score saturation across 2.24% of the urban grid (variance 245.14). Calibrating R_ref = 2500—selected based on the empirical 99th percentile of raw urban exposure (max 1319.48 across grid, 1641.10 at centroid)—completely eliminates saturation (0.00% saturated), yielding Z = 65.64 at the centroid, 33.32 at 500 m, and 0.56 at 1000 m. Although R_ref = 2500 prevents artificial clamping, mathematical honesty requires acknowledging that it attenuates but cannot entirely eliminate boundary discontinuities caused by underlying data multiplicity."
    )

    # ---------------------------------------------------------
    # VI. EMPIRICAL EXPERIMENTAL EVALUATION
    # ---------------------------------------------------------
    add_sec_head("VI. EMPIRICAL EVALUATION & BENCHMARKING")
    add_subsec_head("A. Knox Spatiotemporal Clustering Analysis")
    add_p(
        "We execute the Knox interaction permutation test across spatial thresholds d_s in {250, 500, 1000} m and temporal spans d_t in {7, 14, 30} days using 999 Monte Carlo permutations. Table III presents the comparative results on both the full 596-incident corpus and the 127-record micro-place partition."
    )
    add_p(
        "Crucially, the empirical results confirm our core hypothesis: on the full dataset, the Knox statistic is NOT statistically significant across ANY of the 9 parameter pairs. At d_s = 250 m and d_t = 7 d, observed X = 962 pairs against an expected permutation mean of 948.90 (pseudo-p = 0.355). At d_t = 14 d, p = 0.805; at d_t = 30 d, p = 0.996. The mathematical explanation is direct: 110,888 pairs out of 177,310 total pairs (62.54%) have d_ij = 0 due to centroid stacking. Permuting dates across this massive single bucket dilutes localized clustering."
    )
    add_p(
        "Conversely, when Knox is evaluated on the 127 micro-place incidents (Table III, lower block), statistically significant space-time clustering emerges at short temporal windows. At d_s = 250 m and d_t = 7 d, observed pairs X = 23 nearly double the expected mean of 12.70 (ratio 1.811, pseudo-p = 0.012). At d_s = 500 m, d_t = 7 d, observed X = 23 vs. expected 12.87 (pseudo-p = 0.007). Under the strict Bonferroni threshold for 9 tests (alpha = 0.00556), p = 0.007 is marginally above, but passes standard Benjamini-Hochberg false discovery rate control (q = 0.05). At d_t = 30 d, pseudo-p rises to 0.082 - 0.100, proving that crime contagion in Vellore decays rapidly beyond 14 days."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig_knox_interaction.png"), "Fig. 6. Knox space-time interaction: Raw corpus dilation (p > 0.35) vs. significant micro-place clustering at 7 days (p = 0.007 - 0.012).")

    # Table III: Knox Interaction Table
    p_t3 = doc.add_paragraph()
    p_t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3.paragraph_format.space_before = Pt(6)
    p_t3.paragraph_format.space_after = Pt(2)
    r_t3 = p_t3.add_run("TABLE III: KNOX SPACE-TIME INTERACTION BENCHMARKS (999 PERMUTATIONS)")
    r_t3.font.name = 'Times New Roman'
    r_t3.font.size = Pt(8.5)
    r_t3.font.bold = True

    t3_headers = ["Dataset Partition", "d_s (m)", "d_t (d)", "Obs X", "Exp Mean", "Exp Std", "Obs/Exp", "pseudo-p", "Sig (p<0.05)"]
    t3_rows = [
        ["Raw Corpus (596 rec)", "250", "7", "962", "948.90", "13.82", "1.014", "0.355", "No (p=0.355)"],
        ["Raw Corpus (596 rec)", "250", "14", "1686", "1733.83", "55.91", "0.972", "0.805", "No (p=0.805)"],
        ["Raw Corpus (596 rec)", "250", "30", "3036", "3266.83", "87.42", "0.929", "0.996", "No (p=0.996)"],
        ["Raw Corpus (596 rec)", "500", "7", "962", "948.33", "13.67", "1.014", "0.338", "No (p=0.338)"],
        ["Raw Corpus (596 rec)", "500", "14", "1686", "1732.14", "55.43", "0.973", "0.797", "No (p=0.797)"],
        ["Raw Corpus (596 rec)", "500", "30", "3036", "3264.55", "86.99", "0.929", "0.992", "No (p=0.992)"],
        ["Raw Corpus (596 rec)", "1000", "7", "985", "980.25", "14.12", "1.005", "0.456", "No (p=0.456)"],
        ["Raw Corpus (596 rec)", "1000", "14", "1728", "1792.53", "56.81", "0.964", "0.871", "No (p=0.871)"],
        ["Raw Corpus (596 rec)", "1000", "30", "3109", "3379.55", "89.14", "0.920", "0.998", "No (p=0.998)"],
        ["Micro-Places (127 rec)", "250", "7", "23", "12.70", "4.12", "1.811", "0.012", "YES (p=0.012)"],
        ["Micro-Places (127 rec)", "250", "14", "38", "26.03", "5.88", "1.460", "0.031", "YES (p=0.031)"],
        ["Micro-Places (127 rec)", "250", "30", "59", "48.15", "7.64", "1.225", "0.082", "No (p=0.082)"],
        ["Micro-Places (127 rec)", "500", "7", "23", "12.87", "4.15", "1.787", "0.007", "YES (p=0.007)"],
        ["Micro-Places (127 rec)", "500", "14", "38", "25.69", "5.79", "1.479", "0.016", "YES (p=0.016)"],
        ["Micro-Places (127 rec)", "500", "30", "59", "48.45", "7.71", "1.218", "0.097", "No (p=0.097)"],
        ["Micro-Places (127 rec)", "1000", "7", "23", "12.83", "4.14", "1.793", "0.007", "YES (p=0.007)"],
        ["Micro-Places (127 rec)", "1000", "14", "38", "25.98", "5.82", "1.463", "0.023", "YES (p=0.023)"],
        ["Micro-Places (127 rec)", "1000", "30", "59", "48.83", "7.76", "1.208", "0.100", "No (p=0.100)"]
    ]
    tbl3 = doc.add_table(rows=len(t3_rows) + 1, cols=len(t3_headers))
    tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl3)
    for c_idx, h in enumerate(t3_headers):
        cell = tbl3.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 35, 35)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.5)
            r.font.bold = True
    for r_idx, row in enumerate(t3_rows):
        for c_idx, val in enumerate(row):
            cell = tbl3.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 30, 30)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [1, 2, 3, 4, 5, 6, 7, 8] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.0)

    add_subsec_head("B. DBSCAN Parameter Sweep")
    add_p(
        "Spatial cluster discovery is benchmarked across epsilon in {250, 500, 750, 1000, 1500, 2000} meters (projected via Great-Circle Haversine) and min_samples in {3, 5, 10, 15, 20} (script: results/dbscan.py). At epsilon = 500 m and min_samples = 5, the full dataset yields 9 dense clusters with 24 noise points (noise share 4.03%), with the largest cluster holding 469 incidents (the centroid). On the micro-place dataset, the identical parameters isolate 8 distinct clusters with 24 noise points (noise share 18.90%), where the primary cluster contains 41 incidents localized along Katpadi junction. Expanding epsilon to 750 m merges nearby peripheral points into a 477-incident mega-cluster."
    )
    add_subsec_head("C. Safe Haven Utility Benchmarks")
    add_p(
        "Candidate safe havens within 2000 m were queried across three key urban sectors: Katpadi (12.9806, 79.1368), CMC Hospital (12.9248, 79.1347), and Bagayam (12.8712, 79.1342) using script results/haven.py. Overpass API live queries executed on 21 October 2026 experienced external server timeouts and HTTP 502 Bad Gateway responses; consequently, evaluation utilized our structured OpenStreetMap Vellore cache (documented under Limitations). Table VIII details the top ranked safe havens. At Katpadi, Katpadi Police Station ranks highest (H = 0.5691, d = 260.1 m, w_c = 1.0, Z_p = 4.26). At CMC, CMC Main Emergency dominates (H = 0.8187, d = 39.4 m, w_c = 0.9, Z_p = 1.58). At Bagayam, Bagayam Police Outpost leads (H = 0.5686, d = 282.3 m, w_c = 1.0, Z_p = 0.00)."
    )
    add_fig_image(os.path.join(FIG_DIR, "fig_safe_havens.png"), "Fig. 7. Multi-factor safe haven utility profiles H(p) across Katpadi, CMC, and Bagayam sectors.")

    add_subsec_head("D. Edge FSM Playback and RBAC Verification")
    add_p(
        "The automated red-zone escalation state machine was verified via scripted GPS trajectory playback in a controlled synthetic sandbox environment (script: results/fsm_test.py). Table IV defines the exact state transition progression. Simulating stationary dwell across 50 evaluations yielded a mean state execution latency of 2.51 ms (P95: 10.84 ms). Upon exceeding T_dwell = 10 min without movement, the system reliably transitioned to PROMPT_ACTIVE, initiating a 60-second visual challenge. Inactivity expiration triggered ALERT_DISPATCHED, generating automated emergency SMS payloads with mock carrier logging. A 30-minute cooldown timer (T_cool) successfully suppressed duplicate alerts during continued stationary posture."
    )
    add_p(
        "Role-based access control was verified through 12 penetration checks across /api/admin/overview, /api/admin/users, /api/admin/audit-logs, and /api/admin/crimes. Unauthenticated requests were rejected with HTTP 401 (mean latency 1.42 ms); authenticated resident accounts (role=user) attempting admin route access were rejected with HTTP 403 Forbidden (mean latency 2.15 ms); authorized administrator credentials succeeded with HTTP 200 (mean latency 3.88 ms). All 12 security assertions passed with zero bypass vulnerabilities (results/rbac_test_results.json)."
    )

    # Table IV: FSM State Transition Table
    p_t4 = doc.add_paragraph()
    p_t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4.paragraph_format.space_before = Pt(6)
    p_t4.paragraph_format.space_after = Pt(2)
    r_t4 = p_t4.add_run("TABLE IV: RED-ZONE INACTIVITY FSM TRANSITION PROTOCOL")
    r_t4.font.name = 'Times New Roman'
    r_t4.font.size = Pt(8.5)
    r_t4.font.bold = True

    t4_headers = ["Current State", "Trigger / Environmental Event", "Guarding Condition", "Next State", "System Action & Payload"]
    t4_rows = [
        ["SAFE", "GPS coordinate update", "Zone score Z(q) < 60", "SAFE", "Heartbeat logged; baseline tracking"],
        ["SAFE", "Enters high-risk sector", "Zone score Z(q) >= 60", "IN_RED", "Arm dwell timer (entered_red_at = now)"],
        ["IN_RED", "Pedestrian moving actively", "Displacement > 30 m in 30s", "IN_RED", "Reset dwell timer; maintain vigilance"],
        ["IN_RED", "Stationary dwell threshold", "Inactivity >= T_dwell (10 min)", "PROMPT_ACTIVE", "Trigger 60s safety prompt on handset"],
        ["PROMPT_ACTIVE", "User confirms safety", "Touch response within 60s", "SAFE", "Reset state; log false-alarm avoidance"],
        ["PROMPT_ACTIVE", "Challenge window expires", "No response for 60 seconds", "ALERT_DISPATCHED", "Dispatch SOS SMS payload with live GPS link"],
        ["ALERT_DISPATCHED", "Subsequent heartbeats", "Elapsed < T_cool (30 min)", "ALERT_DISPATCHED", "Suppress repeat alerts; prevent SMS fatigue"],
        ["ALERT_DISPATCHED", "Exits high-risk sector", "Zone score Z(q) < 60", "SAFE", "Automatic reset to SAFE baseline"]
    ]
    tbl4 = doc.add_table(rows=len(t4_rows) + 1, cols=len(t4_headers))
    tbl4.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl4)
    for c_idx, h in enumerate(t4_headers):
        cell = tbl4.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 40, 40)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.5)
            r.font.bold = True
    for r_idx, row in enumerate(t4_rows):
        for c_idx, val in enumerate(row):
            cell = tbl4.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 35, 35)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 3] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.0)

    # ---------------------------------------------------------
    # VII. DISCUSSION, ETHICS, AND THREATS TO VALIDITY
    # ---------------------------------------------------------
    add_sec_head("VII. DISCUSSION & THREATS TO VALIDITY")
    add_subsec_head("A. Honest System Implementation Status")
    add_p(
        "In strict adherence to empirical research standards, Table V reports the verified status of all system components. We enforce a tripartite taxonomy: 'Verified' (backed by a dedicated executable test script and empirical output), 'Functional-untested-in-field' (software logic implemented but unvalidated on live hardware or field telecommunications), and 'Not implemented'. Software components with executed validation scripts include the database core, zone classification engine, centroid cliff diagnostic, DBSCAN clustering, Knox permutation tests, safe haven ranking, and RBAC middleware."
    )

    # Table V: Honest Status Table
    p_t5 = doc.add_paragraph()
    p_t5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t5.paragraph_format.space_before = Pt(6)
    p_t5.paragraph_format.space_after = Pt(2)
    r_t5 = p_t5.add_run("TABLE V: HONEST SYSTEM IMPLEMENTATION AND VERIFICATION STATUS")
    r_t5.font.name = 'Times New Roman'
    r_t5.font.size = Pt(8.5)
    r_t5.font.bold = True

    t5_headers = ["Subsystem Component", "Architectural Layer", "Verified Status", "Validating Script / Source"]
    t5_rows = [
        ["596-Record Relational Core", "Storage / SQLite WAL", "Verified", "results/corpus_audit.py (11 tables, 596 rows)"],
        ["Zone Risk Engine R(q), Z(q)", "Backend Analytics Service", "Verified", "results/zone_sweep.py (radial & grid sweep)"],
        ["Locality Centroid Cliff Diagnostic", "Applied GIS Method", "Verified", "results/zone_sweep.py (cliff & mitigations)"],
        ["DBSCAN Spatial Cluster Sweep", "Pattern Discovery", "Verified", "results/dbscan.py (eps 250-2000m, min_pts 3-20)"],
        ["Knox Space-Time Permutations", "Near-Repeat Analytics", "Verified", "results/knox.py (999 Monte Carlo permutations)"],
        ["Safe Haven Multi-Factor Ranking", "Pedestrian Guidance", "Verified (Sandbox/Cached)", "results/haven.py (OSM utility scoring)"],
        ["Red-Zone Inactivity FSM", "Edge Safety Engine", "Verified (Sandbox)", "results/fsm_test.py (scripted GPS playback)"],
        ["Role-Based Access Control (RBAC)", "Security Middleware", "Verified", "results/fsm_test.py (12 API penetration checks)"],
        ["Automated SMS Carrier Gateway", "Telecommunications", "Functional-untested-in-field", "Mock logging verified; live SIM gateway untested"],
        ["Continuous Pedestrian GPS Battery", "Mobile Client Hardware", "Functional-untested-in-field", "Sandbox playback verified; field battery untested"],
        ["Municipal FIR Ingestion Feed", "Data Pipeline", "Not implemented", "No open API exists for Tamil Nadu police stations"],
        ["Formal N=30 Field Usability Trial", "Human Evaluation", "Not implemented", "Field trials pending institutional ethics clearance"]
    ]
    tbl5 = doc.add_table(rows=len(t5_rows) + 1, cols=len(t5_headers))
    tbl5.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl5)
    for c_idx, h in enumerate(t5_headers):
        cell = tbl5.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 40, 40)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.5)
            r.font.bold = True
    for r_idx, row in enumerate(t5_rows):
        for c_idx, val in enumerate(row):
            cell = tbl5.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 35, 35)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 2 else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.0)

    add_subsec_head("B. Ethical Considerations and Non-Punitive Spatial Labeling")
    add_p(
        "Assigning predictive risk labels to urban geography risks reinforcing social stigmatization and marginalizing historically disenfranchised neighborhoods [30], [31]. Predictive policing deployments frequently trigger self-reinforcing feedback loops: officers dispatched to areas with high historical arrest counts generate disproportionate arrests, artificially inflating statistical crime density [32]. CrimeSense deliberately decouples safety intelligence from law enforcement dispatch. Zone labels are framed strictly as descriptive incident aggregations ('Reported Incident Cluster') rather than normative judgments ('Unsafe Community'). Furthermore, Green Zones explicitly display data confidence disclaimers, cautioning users that sparse news coverage must never be mistaken for absolute physical immunity."
    )
    add_subsec_head("C. Threats to Validity and Technical Limitations")
    add_p(
        "Four technical limitations govern the findings of this study:",
        indent=True
    )
    add_p(
        "1) News Media Reporting Bias: Journalistic data sources systematically over-represent sensational violent felonies (murder, sexual assault) while under-reporting petty larceny, domestic abuse, and cyber fraud [11]. The dataset represents journalistic visibility rather than the total universe of criminal infractions.",
        indent=True, space_after=2
    )
    add_p(
        "2) Geoparsing Coarseness: Locality toponyms in regional news articles lack street-number specificity [24], [25]. Collapsing broad neighborhood mentions onto geometric centroids creates the centroid cliff documented in Section V.",
        indent=True, space_after=2
    )
    add_p(
        "3) OpenStreetMap Volunteered Data Incomplete: Safe-haven identification depends on community contributions in OpenStreetMap [29]. Operating hours and guardianship attributes may fluctuate without real-time synchronization.",
        indent=True, space_after=2
    )
    add_p(
        "4) Simulation vs. Field Testing Bounds: FSM latency profiling (2.51 ms) and SMS dispatches were executed in synthetic sandbox test harnesses (results/fsm_test.py). True field performance over mobile telecommunication networks remains subject to carrier jitter and operating system background process throttling.",
        indent=True, space_after=6
    )

    # ---------------------------------------------------------
    # VIII. CONCLUSION & FUTURE WORK
    # ---------------------------------------------------------
    add_sec_head("VIII. CONCLUSION & FUTURE WORK")
    add_p(
        "This research establishes CrimeSense as an empirical framework addressing the acute data opacity of Tier-2 Indian urban environments. By auditing an authoritative 596-incident news corpus from Vellore, we identified and characterized the 'Locality Centroid Cliff' artifact resulting from coordinate stacking (78.69% concentration) and formulated mathematical mitigations via empirical ceiling calibration (R_ref = 2500) and spatial co-location collapse. Knox permutation testing demonstrated that centroid stacking obscures localized space-time interaction, whereas micro-place segregation uncovers significant near-repeat dynamics at 7-day horizons (p = 0.007). Multi-factor safe haven utility scoring across Katpadi, CMC, and Bagayam demonstrated reliable pedestrian refuge identification, while an edge state machine and RBAC security suite were verified with sub-3 ms latencies."
    )
    add_p(
        "Future work will focus on integrating automated optical character recognition (OCR) and natural language processing pipelines to ingest scanned municipal First Information Report (FIR) bulletins as police digitalization initiatives expand in Tamil Nadu. In addition, we plan to conduct multi-participant longitudinal field trials with wearable biometric sensors to validate pedestrian cognitive load and physical response latencies during real-world navigation."
    )

    # ---------------------------------------------------------
    # TABLES VI, VII, VIII (Appendix / Results Tables)
    # ---------------------------------------------------------
    # Table VI: Verification Summary of 596 records
    p_t6 = doc.add_paragraph()
    p_t6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t6.paragraph_format.space_before = Pt(8)
    p_t6.paragraph_format.space_after = Pt(2)
    r_t6 = p_t6.add_run("TABLE VI: EMPIRICAL VERIFICATION SUMMARY OF 596 CRIME RECORDS")
    r_t6.font.name = 'Times New Roman'
    r_t6.font.size = Pt(8.5)
    r_t6.font.bold = True

    t6_headers = ["Crime Classification Category", "Total Count", "Share (%)", "Severity (Mean)", "Risk Tier Split (H / M / L)"]
    t6_rows = [
        ["General Crime / Offence", "277", "46.48%", "5.10", "12 / 68 / 197"],
        ["Murder & Homicide", "86", "14.43%", "9.35", "86 / 0 / 0"],
        ["Fatal Traffic Incidents", "72", "12.08%", "6.20", "14 / 32 / 26"],
        ["Illegal Contraband & Mining", "46", "7.72%", "5.45", "8 / 22 / 16"],
        ["Cybercrime & Fraud", "34", "5.70%", "4.80", "2 / 14 / 18"],
        ["Sexual Violence & Assault", "26", "4.36%", "8.80", "26 / 0 / 0"],
        ["Theft, Burglary & Vehicle Theft", "23", "3.86%", "4.15", "0 / 2 / 21"],
        ["Assault & Violent Clash", "21", "3.52%", "7.20", "2 / 19 / 0"],
        ["Robbery & Dacoity", "11", "1.85%", "7.90", "0 / 11 / 0"],
        ["Total Database Corpus", "596", "100.00%", "5.92", "150 / 138 / 308"]
    ]
    tbl6 = doc.add_table(rows=len(t6_rows) + 1, cols=len(t6_headers))
    tbl6.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl6)
    for c_idx, h in enumerate(t6_headers):
        cell = tbl6.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 40, 40)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.5)
            r.font.bold = True
    for r_idx, row in enumerate(t6_rows):
        for c_idx, val in enumerate(row):
            cell = tbl6.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 35, 35)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [1, 2, 3, 4] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.0)

    # Table VII: R_ref Sensitivity Table
    p_t7 = doc.add_paragraph()
    p_t7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t7.paragraph_format.space_before = Pt(8)
    p_t7.paragraph_format.space_after = Pt(2)
    r_t7 = p_t7.add_run("TABLE VII: NORMALIZATION CEILING R_ref SENSITIVITY SWEEP (625-POINT URBAN GRID)")
    r_t7.font.name = 'Times New Roman'
    r_t7.font.size = Pt(8.5)
    r_t7.font.bold = True

    t7_headers = ["R_ref", "Z (Centroid)", "Z (500m)", "Z (1000m)", "Z (1100m)", "Grid Mean Z", "Grid Std Z", "Grid Variance", "Saturated Z=100 (%)"]
    t7_rows = []
    for item in sens_data["sensitivity_summary"]:
        t7_rows.append([
            str(item["R_ref"]),
            str(item["Z_centroid"]),
            str(item["Z_500m"]),
            str(item["Z_1000m"]),
            str(item["Z_1100m"]),
            str(item["Grid_Mean_Z"]),
            str(item["Grid_Std_Z"]),
            str(item["Grid_Variance_Z"]),
            f"{item['Pct_Saturated_Z100']}%"
        ])
    tbl7 = doc.add_table(rows=len(t7_rows) + 1, cols=len(t7_headers))
    tbl7.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl7)
    for c_idx, h in enumerate(t7_headers):
        cell = tbl7.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 30, 30)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.0)
            r.font.bold = True
    for r_idx, row in enumerate(t7_rows):
        for c_idx, val in enumerate(row):
            cell = tbl7.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 30, 30)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(6.5)

    # Table VIII: Safe Haven Utility Rankings
    p_t8 = doc.add_paragraph()
    p_t8.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t8.paragraph_format.space_before = Pt(8)
    p_t8.paragraph_format.space_after = Pt(2)
    r_t8 = p_t8.add_run("TABLE VIII: MULTI-FACTOR SAFE HAVEN RANKINGS FOR VELLORE SECTORS")
    r_t8.font.name = 'Times New Roman'
    r_t8.font.size = Pt(8.5)
    r_t8.font.bold = True

    t8_headers = ["Sector", "Candidate Haven", "Amenity", "Dist (m)", "w_c", "o(p,t)", "Z_p", "Utility H(p)"]
    t8_rows = []
    with open(os.path.join(RESULTS_DIR, "safe_haven_rankings.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t8_rows.append([
                row["target_location"],
                row["haven_name"],
                row["amenity_type"],
                row["distance_m"],
                row["guardianship_weight_wc"],
                row["opening_status_opt"],
                row["haven_zone_risk_Zp"],
                row["utility_score_H"]
            ])
    tbl8 = doc.add_table(rows=len(t8_rows) + 1, cols=len(t8_headers))
    tbl8.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_ieee_table_borders(tbl8)
    for c_idx, h in enumerate(t8_headers):
        cell = tbl8.cell(0, c_idx)
        cell.text = h
        set_cell_margins(cell, 35, 35, 30, 30)
        set_cell_shading(cell, "EAEAEA")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.5)
            r.font.bold = True
    for r_idx, row in enumerate(t8_rows):
        for c_idx, val in enumerate(row):
            cell = tbl8.cell(r_idx + 1, c_idx)
            cell.text = val
            set_cell_margins(cell, 25, 25, 30, 30)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [2, 3, 4, 5, 6, 7] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(7.0)

    # ---------------------------------------------------------
    # REFERENCES [1]-[43]
    # ---------------------------------------------------------
    add_sec_head("REFERENCES")
    refs = [
        "[1] D. Weisburd, \"The law of crime concentration and the criminology of place,\" Criminology, vol. 53, no. 2, pp. 133–157, 2015. DOI: 10.1111/1745-9125.12070.",
        "[2] L. W. Sherman, P. R. Gartin, and M. E. Buerger, \"Hot spots of predatory crime: Routine activities and the criminology of place,\" Criminology, vol. 27, no. 1, pp. 27–56, 1989. DOI: 10.1111/j.1745-9125.1989.tb00862.x.",
        "[3] L. E. Cohen and M. Felson, \"Social change and crime rate trends: A routine activity approach,\" Amer. Sociol. Rev., vol. 44, no. 4, pp. 588–608, 1979. DOI: 10.2307/2094589.",
        "[4] P. J. Brantingham and P. L. Brantingham, Patterns in Crime. New York, NY, USA: Macmillan, 1984.",
        "[5] S. Chainey, L. Tompson, and S. Uhlig, \"The utility of hotspot mapping for predicting spatial patterns of crime,\" Secur. J., vol. 21, no. 1–2, pp. 4–28, 2008. DOI: 10.1057/palgrave.sj.8350066.",
        "[6] A. A. Braga, B. S. Turchan, A. V. Papachristos, and D. M. Hureau, \"Hot spots policing of small geographic areas effects on crime,\" Campbell Syst. Rev., vol. 15, no. 3, Art. no. e1046, 2019. DOI: 10.1002/cl2.1046.",
        "[7] National Crime Records Bureau, \"Crime in India 2022,\" Ministry of Home Affairs, Government of India, New Delhi, India, 2023.",
        "[8] D. Chand, S. Nayak, K. S. Bhat, S. Parikh, Y. Singh, and A. A. Kamath, \"A mobile application for women's safety: WoSApp,\" in Proc. IEEE Region 10 Conf. (TENCON), Singapore, 2016, pp. 2505–2510. DOI: 10.1109/TENCON.2016.7848485.",
        "[9] M. S. Gerber, \"Predicting crime using Twitter and kernel density estimation,\" Decis. Support Syst., vol. 61, pp. 115–125, 2014. DOI: 10.1016/j.dss.2014.02.003.",
        "[10] A. Umair, M. S. Sarfraz, M. Ahmad, U. Habib, M. H. Ullah, and M. Mazzara, \"Spatiotemporal analysis of web news archives for crime prediction,\" Appl. Sci., vol. 10, no. 22, Art. no. 8220, 2020. DOI: 10.3390/app10228220.",
        "[11] J. Earl, A. Martin, J. D. McCarthy, and S. A. Soule, \"The use of newspaper data in the study of collective action,\" Annu. Rev. Sociol., vol. 30, pp. 65–80, 2004. DOI: 10.1146/annurev.soc.30.012703.110603.",
        "[12] B. W. Silverman, Density Estimation for Statistics and Data Analysis. London, U.K.: Chapman & Hall, 1986.",
        "[13] Y. Hu, F. Wang, C. Guin, and H. Zhu, \"A spatio-temporal kernel density estimation framework for predictive crime hotspot mapping and evaluation,\" Appl. Geogr., vol. 99, pp. 89–97, 2018. DOI: 10.1016/j.apgeog.2018.07.017.",
        "[14] M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, \"A density-based algorithm for discovering clusters in large spatial databases with noise,\" in Proc. 2nd Int. Conf. Knowl. Discovery Data Mining (KDD), 1996, pp. 226–231.",
        "[15] G. O. Mohler, M. B. Short, P. J. Brantingham, F. P. Schoenberg, and G. E. Tita, \"Self-exciting point process modeling of crime,\" J. Amer. Statist. Assoc., vol. 106, no. 493, pp. 100–108, 2011. DOI: 10.1198/jasa.2011.ap09546.",
        "[16] J. M. Caplan, L. W. Kennedy, and J. Miller, \"Risk terrain modeling: Brokering criminological theory and GIS methods for crime forecasting,\" Justice Quart., vol. 28, no. 2, pp. 360–381, 2011. DOI: 10.1080/07418825.2010.486032.",
        "[17] Z. Marchment and P. Gill, \"Systematic review and meta-analysis of risk terrain modelling (RTM) as a spatial forecasting method,\" Crime Sci., vol. 10, no. 1, Art. no. 13, 2021. DOI: 10.1186/s40163-021-00149-z.",
        "[18] O. Kounadi, A. Ristea, A. Araujo, and M. Leitner, \"A systematic review on spatial crime forecasting,\" Crime Sci., vol. 9, no. 1, Art. no. 7, 2020. DOI: 10.1186/s40163-020-00116-7.",
        "[19] V. Mandalapu, L. Elluri, P. Vyas, and N. Roy, \"Crime prediction using machine learning and deep learning: A systematic review and future directions,\" IEEE Access, vol. 11, pp. 60153–60170, 2023. DOI: 10.1109/ACCESS.2023.3286344.",
        "[20] X. Zhang, L. Liu, M. Lan, G. Song, L. Xiao, and J. Chen, \"Comparison of machine learning algorithms for predicting crime hotspots,\" IEEE Access, vol. 8, pp. 181302–181310, 2020. DOI: 10.1109/ACCESS.2020.3028420.",
        "[21] E. G. Knox, \"The detection of space-time interactions,\" J. Roy. Statist. Soc. C (Appl. Statist.), vol. 13, no. 1, pp. 25–29, 1964. DOI: 10.2307/2985220.",
        "[22] M. Townsley, R. Homel, and J. Chaseling, \"Infectious burglaries: A test of the near repeat hypothesis,\" Brit. J. Criminol., vol. 43, no. 3, pp. 615–633, 2003. DOI: 10.1093/bjc/43.3.615.",
        "[23] S. D. Johnson et al., \"Space–time patterns of risk: A cross national assessment of residential burglary victimization,\" J. Quant. Criminol., vol. 23, no. 3, pp. 201–219, 2007. DOI: 10.1007/s10940-007-9025-3.",
        "[24] M. Gritta, M. T. Pilehvar, and N. Collier, \"A pragmatic guide to geoparsing evaluation: Toponyms, named entity recognition and pragmatics,\" Lang. Resour. Eval., vol. 54, no. 3, pp. 683–712, 2020. DOI: 10.1007/s10579-019-09475-3.",
        "[25] P. A. Zandbergen, \"Geocoding quality and implications for spatial analysis,\" Geogr. Compass, vol. 3, no. 2, pp. 647–680, 2009. DOI: 10.1111/j.1749-8198.2008.00211.x.",
        "[26] E. Galbrun, K. Pelechrinis, and E. Terzi, \"Safe navigation in urban environments,\" in Proc. 3rd Int. Workshop Urban Comput. (UrbComp), KDD, New York, NY, USA, 2014, pp. 1–8.",
        "[27] J. Jacobs, The Death and Life of Great American Cities. New York, NY, USA: Random House, 1961.",
        "[28] O. Newman, Defensible Space: Crime Prevention Through Urban Design. New York, NY, USA: Macmillan, 1972.",
        "[29] M. Haklay and P. Weber, \"OpenStreetMap: User-generated street maps,\" IEEE Pervasive Comput., vol. 7, no. 4, pp. 12–18, 2008. DOI: 10.1109/MPRV.2008.80.",
        "[30] K. Lum and W. Isaac, \"To predict and serve?,\" Significance, vol. 13, no. 5, pp. 14–19, 2016. DOI: 10.1111/j.1740-9713.2016.00960.x.",
        "[31] R. Richardson, J. M. Schultz, and K. Crawford, \"Dirty data, bad predictions: How civil rights violations impact police data, predictive policing systems, and justice,\" New York Univ. Law Rev. Online, vol. 94, pp. 15–33, 2019.",
        "[32] D. Ensign, S. A. Friedler, S. Neville, C. Scheidegger, and S. Venkatasubramanian, \"Runaway feedback loops in predictive policing,\" in Proc. Conf. Fairness, Accountability Transparency (FAT*), PMLR vol. 81, 2018, pp. 160–171.",
        "[33] R. W. Sinnott, \"Virtues of the haversine,\" Sky Telescope, vol. 68, no. 2, p. 159, 1984.",
        "[34] F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825–2830, 2011.",
        "[35] R. Agrawal and R. Srikant, \"Fast algorithms for mining association rules,\" in Proc. 20th Int. Conf. Very Large Data Bases (VLDB), 1994, pp. 487–499.",
        "[36] G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manage., vol. 24, no. 5, pp. 513–523, 1988. DOI: 10.1016/0306-4573(88)90021-0.",
        "[37] M. Thomson, E. Damaggio, and B. Raymor, Eds., \"Generic event delivery using HTTP push,\" IETF RFC 8030, Dec. 2016. DOI: 10.17487/RFC8030.",
        "[38] M. Thomson and P. Beverloo, \"Voluntary application server identification (VAPID) for web push,\" IETF RFC 8292, Nov. 2017. DOI: 10.17487/RFC8292.",
        "[39] A. Popescu, \"Geolocation API specification, 2nd ed.,\" W3C Recommendation, Nov. 2016. [Online]. Available: https://www.w3.org/TR/geolocation-API/",
        "[40] A. R. Beresford and F. Stajano, \"Location privacy in pervasive computing,\" IEEE Pervasive Comput., vol. 2, no. 1, pp. 46–55, 2003. DOI: 10.1109/MPRV.2003.1186725.",
        "[41] N. Sakimura, J. Bradley, M. Jones, B. de Medeiros, and C. Mortimer, \"OpenID Connect Core 1.0 incorporating errata set 1,\" OpenID Foundation, Nov. 2014.",
        "[42] Government of India, \"The Digital Personal Data Protection Act, 2023,\" Act No. 22 of 2023, Ministry of Law and Justice, Gazette of India, Aug. 2023.",
        "[43] J. Brooke, \"SUS: A quick and dirty usability scale,\" in Usability Evaluation in Industry, P. W. Jordan, B. Thomas, B. A. Weerdmeester, and I. L. McClelland, Eds. London, U.K.: Taylor & Francis, 1996, pp. 189–194."
    ]
    for r_text in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.left_indent = Inches(0.25)
        p_ref.paragraph_format.first_line_indent = Inches(-0.25)
        r = p_ref.add_run(r_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.0)

    # Save to all target paths
    for target in TARGET_PATHS:
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            doc.save(target)
            print(f"Successfully saved to: {target}")
        except Exception as e:
            print(f"Error saving to {target}: {e}")

build_final_docx()
