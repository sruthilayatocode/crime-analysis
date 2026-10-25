import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = r"c:\Users\sruth\crime analysis\research_paper\figures"
os.makedirs(OUT_DIR, exist_ok=True)

# Set global publication styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif']
plt.rcParams['font.size'] = 9

def generate_fig1():
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    ax.axis('off')

    # Background canvas
    box_kw = dict(boxstyle="square,pad=0.3", fc="#f8f9fa", ec="#333333", lw=1)
    dashed_kw = dict(boxstyle="square,pad=0.3", fc="#ffffff", ec="#333333", lw=1, ls="--")
    solid_kw = dict(boxstyle="square,pad=0.3", fc="#ffffff", ec="#333333", lw=1)

    # 1. Client Layer
    ax.text(0.28, 0.92, "User Web Application (Mobile-first)\nsearch · zone · SOS · saved · settings", ha="center", va="center", bbox=solid_kw, fontsize=7.5)
    ax.text(0.72, 0.92, "Admin Dashboard (Desktop)\nanalytics · users · live map · alerts", ha="center", va="center", bbox=solid_kw, fontsize=7.5)
    ax.annotate("", xy=(0.5, 0.83), xytext=(0.5, 0.87), arrowprops=dict(arrowstyle="<|-|>", lw=1.3, color="#222", mutation_scale=10))

    # 2. REST API Gateway
    ax.text(0.5, 0.79, "Flask REST API Gateway\nsession auth · role guard (user / admin) · Google ID-token check · audit log", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.3", fc="#fff9db", ec="#cca000", lw=1), fontsize=8, weight="bold")
    ax.annotate("", xy=(0.5, 0.71), xytext=(0.5, 0.75), arrowprops=dict(arrowstyle="<|-|>", lw=1.3, color="#222", mutation_scale=10))

    # 3. Service Layer Outer Box
    service_box = patches.Rectangle((0.05, 0.38), 0.9, 0.31, fill=True, fc="#f1f3f5", ec="#adb5bd", lw=0.8)
    ax.add_patch(service_box)
    ax.text(0.5, 0.66, "Service Layer (Dashed boxes = proposed modules)", ha="center", va="center", fontsize=7.5, style="italic")

    # Service Submodules
    ax.text(0.18, 0.58, "Zone Classifier\nred / yellow / green", ha="center", va="center", bbox=solid_kw, fontsize=7)
    ax.text(0.50, 0.58, "Hotspot & Heatmap\nDBSCAN · density", ha="center", va="center", bbox=solid_kw, fontsize=7)
    ax.text(0.82, 0.58, "Pattern Recurrence\nnear-repeat · rules", ha="center", va="center", bbox=dashed_kw, fontsize=7)

    ax.text(0.18, 0.45, "Pre-visit Advisory\nrule-based text", ha="center", va="center", bbox=dashed_kw, fontsize=7)
    ax.text(0.50, 0.45, "Safe-haven Finder\nOSM places", ha="center", va="center", bbox=dashed_kw, fontsize=7)
    ax.text(0.82, 0.45, "SOS & Dwell Monitor\nSMS / Provider", ha="center", va="center", bbox=solid_kw, fontsize=7)

    ax.annotate("", xy=(0.5, 0.32), xytext=(0.5, 0.38), arrowprops=dict(arrowstyle="<|-|>", lw=1.3, color="#222", mutation_scale=10))

    # 4. Database Layer
    ax.text(0.5, 0.26, "SQLite Database (Single Source of Truth)\ncrimes · users · user_settings · sos_contacts · saved_locations · user_locations\nuser_red_zone_states · sos_events · shared_links · alerts · audit_logs", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.4", fc="#e7f5ff", ec="#1c7ed6", lw=1), fontsize=7.5)

    ax.annotate("", xy=(0.5, 0.17), xytext=(0.5, 0.20), arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#222", mutation_scale=10))

    # 5. Ingestion Pipeline
    ax.text(0.5, 0.08, "Ingestion Pipeline (Offline)\nNews collection → Crime-type tagging → De-duplication → Locality & coordinate assignment\n→ Severity mapping → Validation → Import into crimes table", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.3", fc="#f8f0fc", ec="#ae3ec9", lw=0.8), fontsize=7.5)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig1_architecture.png")
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print("Fig 1 saved:", path)

def generate_fig2():
    fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=300)
    ax.axis('off')

    tbl_kw = dict(boxstyle="square,pad=0.3", fc="#ffffff", ec="#212529", lw=1)
    child_kw = dict(boxstyle="square,pad=0.3", fc="#f8f9fa", ec="#495057", lw=0.8)

    # Central users table
    ax.text(0.25, 0.85, "users\nid (PK) · name · email (unique)\npassword_hash · google_id · role\nis_active · created_at · last_login_at", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.4", fc="#d3f9d8", ec="#2b8a3e", lw=1.2), fontsize=7.5, weight="bold")

    # Children
    ax.text(0.08, 0.55, "user_settings\nuser_id (FK)\nlocation_sharing\nred_zone_alert", ha="center", va="center", bbox=child_kw, fontsize=6.8)
    ax.text(0.24, 0.55, "user_locations\nuser_id (FK)\nheartbeat pos\ntimestamp", ha="center", va="center", bbox=child_kw, fontsize=6.8)
    ax.text(0.40, 0.55, "user_red_zone_states\nuser_id (FK)\nzone · dwell state\nlast_heartbeat", ha="center", va="center", bbox=child_kw, fontsize=6.8)

    ax.text(0.08, 0.25, "sos_contacts\nuser_id (FK)\nname · phone\nis_primary", ha="center", va="center", bbox=child_kw, fontsize=6.8)
    ax.text(0.24, 0.25, "saved_locations\nuser_id (FK)\nlat, lng · label\naddress · is_pinned", ha="center", va="center", bbox=child_kw, fontsize=6.8)
    ax.text(0.40, 0.25, "sos_events\nuser_id (FK)\nstatus · pos · zone\ncontacts_notified", ha="center", va="center", bbox=child_kw, fontsize=6.8)

    # Lines from users to children
    for x_pos in [0.08, 0.24, 0.40]:
        ax.plot([0.25, x_pos], [0.73, 0.63], color="#495057", lw=0.8)

    # Independent crimes table
    ax.text(0.75, 0.70, "crimes (596 records, independent)\nid (PK) · article_id (unique)\ntitle · url · source · crime_type\ndescription · district · locality\nlatitude · longitude · severity_score\nrisk_level · published_date", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.4", fc="#ffe3e3", ec="#c92a2a", lw=1.2), fontsize=7.5)

    # audit_logs and shared_links
    ax.text(0.75, 0.30, "audit_logs\nid (PK) · admin_id (FK)\naction · target_entity\ndetails · ip · timestamp", ha="center", va="center", bbox=child_kw, fontsize=7)
    ax.text(0.75, 0.10, "shared_links\ntoken (unique) · user_id (FK)\nlat, lng · expires_at · is_live", ha="center", va="center", bbox=child_kw, fontsize=7)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig2_schema.png")
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print("Fig 2 saved:", path)

def generate_fig3():
    fig, ax = plt.subplots(figsize=(6.2, 3.8), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    step_kw = dict(boxstyle="square,pad=0.28", fc="#f8f9fa", ec="#333333", lw=1.1)

    steps = [
        ("Query point q (GPS fix, search address, or typed coordinates)", 0.94),
        ("Bounding-box spatial pre-filter on stored crimes table", 0.81),
        ("Haversine distance calculation: d(q, i) <= rho (search radius rho = 1000 m)", 0.68),
        ("Calculate contribution of each incident: s_i x delta(d_i) x w(a_i)", 0.55),
        ("Sum raw risk R(q), clamp to ceiling: Z(q) = min(100, 100 x R / R_ref)", 0.42),
    ]

    for i, (s, y_pos) in enumerate(steps):
        ax.text(0.5, y_pos, s, ha="center", va="center", bbox=step_kw, fontsize=7.2)
        if i < len(steps) - 1:
            next_y = steps[i+1][1]
            ax.annotate("", xy=(0.5, next_y + 0.04), xytext=(0.5, y_pos - 0.04),
                        arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    # Horizontal distributor bar from step 5 to 3 zones
    y_bus_top = 0.35
    ax.annotate("", xy=(0.5, y_bus_top), xytext=(0.5, 0.38),
                arrowprops=dict(arrowstyle="-", lw=1.2, color="#495057"))
    ax.plot([0.18, 0.82], [y_bus_top, y_bus_top], color="#495057", lw=1.2)

    # 3 vertical drop arrows into zone boxes
    zone_x = [0.18, 0.50, 0.82]
    zone_colors = ["#c92a2a", "#f59f00", "#2b8a3e"]
    for zx, zc in zip(zone_x, zone_colors):
        ax.annotate("", xy=(zx, 0.28), xytext=(zx, y_bus_top),
                    arrowprops=dict(arrowstyle="-|>", lw=1.3, color=zc, mutation_scale=11))

    ax.text(0.18, 0.24, "RED ZONE\nscore Z >= 60", ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.25", fc="#ffe3e3", ec="#c92a2a", lw=1.2), fontsize=7.2, weight="bold")
    ax.text(0.50, 0.24, "YELLOW ZONE\n30 <= score < 60", ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.25", fc="#fff9db", ec="#f59f00", lw=1.2), fontsize=7.2, weight="bold")
    ax.text(0.82, 0.24, "GREEN ZONE\nscore Z < 30", ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.25", fc="#d3f9d8", ec="#2b8a3e", lw=1.2), fontsize=7.2, weight="bold")

    # Collector from 3 zones down to Advisory Card Assembly
    y_bus_bot = 0.16
    for zx, zc in zip(zone_x, zone_colors):
        ax.plot([zx, zx], [0.19, y_bus_bot], color="#495057", lw=1.1)
    ax.plot([0.18, 0.82], [y_bus_bot, y_bus_bot], color="#495057", lw=1.1)
    ax.annotate("", xy=(0.5, 0.10), xytext=(0.5, y_bus_bot),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    ax.text(0.5, 0.05, "Advisory Card Assembly: Zone badge, incident count, top crime types, nearest report, source article link",
            ha="center", va="center", bbox=dict(boxstyle="square,pad=0.28", fc="#e7f5ff", ec="#1c7ed6", lw=1.1), fontsize=7.0)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig3_zone_pipeline.png")
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.04)
    plt.close()
    print("Fig 3 saved:", path)

def generate_fig4():
    fig, ax = plt.subplots(figsize=(6.2, 3.4), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    b_kw = dict(boxstyle="square,pad=0.32", fc="#ffffff", ec="#333333", lw=1.1, ls="--")

    # Top box: Stored Incidents
    ax.text(0.5, 0.92, "Stored Incidents (Type, Locality, Coordinates, Date)", ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.32", fc="#f8f9fa", ec="#333333", lw=1.2), fontsize=7.8, weight="bold")

    # Distributor bus
    y_dist = 0.82
    ax.plot([0.5, 0.5], [0.86, y_dist], color="#333333", lw=1.2)
    ax.plot([0.18, 0.82], [y_dist, y_dist], color="#333333", lw=1.2)

    # 3 Downward arrows into analysis blocks
    xs = [0.18, 0.50, 0.82]
    for x_pos in xs:
        ax.annotate("", xy=(x_pos, 0.74), xytext=(x_pos, y_dist),
                    arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    ax.text(0.18, 0.62, "Near-Repeat\nKnox permutation test\npairs within (Delta s, Delta t)\nvs 999 Monte Carlo runs",
            ha="center", va="center", bbox=b_kw, fontsize=6.8)
    ax.text(0.50, 0.62, "Association Rules\nItemset: crime type, locality,\nweek bin; evaluate\nsupport, confidence, lift",
            ha="center", va="center", bbox=b_kw, fontsize=6.8)
    ax.text(0.82, 0.62, "Recurrence Index\nPer locality and type\nShare of repeat incidents\nwithin time window Delta t",
            ha="center", va="center", bbox=b_kw, fontsize=6.8)

    # Collector bus below analysis blocks
    y_coll = 0.48
    for x_pos in xs:
        ax.plot([x_pos, x_pos], [0.50, y_coll], color="#333333", lw=1.2)
    ax.plot([0.18, 0.82], [y_coll, y_coll], color="#333333", lw=1.2)

    # Drop arrow into Pattern Cards box
    ax.annotate("", xy=(0.5, 0.40), xytext=(0.5, y_coll),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    # Center Yellow Box
    ax.text(0.5, 0.32, "Pattern Cards Generated:\n'Same crime type recurs within 500 m and 14 days'\nStatistical lift, confidence level, and source incident links",
            ha="center", va="center", bbox=dict(boxstyle="square,pad=0.35", fc="#fff9db", ec="#cca000", lw=1.2, ls="--"), fontsize=7.2)

    # Distributor bus below Pattern Cards
    y_out = 0.20
    ax.plot([0.5, 0.5], [0.24, y_out], color="#333333", lw=1.2)
    ax.plot([0.28, 0.72], [y_out, y_out], color="#333333", lw=1.2)

    ax.annotate("", xy=(0.28, 0.13), xytext=(0.28, y_out),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))
    ax.annotate("", xy=(0.72, 0.13), xytext=(0.72, y_out),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    ax.text(0.28, 0.06, "Admin Console Review\n(Analyst inspection of patterns)", ha="center", va="center", bbox=b_kw, fontsize=6.8)
    ax.text(0.72, 0.06, "Optional Recurrence Weight\n(In zone scoring, post-validation)", ha="center", va="center", bbox=b_kw, fontsize=6.8)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig4_recurrence.png")
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.04)
    plt.close()
    print("Fig 4 saved:", path)

def generate_fig5():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.2, 3.8), dpi=300)
    for ax in (ax1, ax2):
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    b_kw = dict(boxstyle="square,pad=0.3", fc="#ffffff", ec="#333333", lw=1.1)

    # Subplot A: Pre-visit
    ax1.set_title("(a) Pre-Visit Destination Check", fontsize=8.5, weight="bold", pad=8)
    a_steps = [
        "Search place name / street /\nlandmark or tap on map",
        "Geocoding resolution to\nquery coordinates (lat, lng)",
        "Query Zone Service\n(evaluate radius rho = 1000 m)",
        "Rule-based Advisory Generator\n(transparent template mapping)",
        "Advisory Card Display:\nZone badge, reasons, top types,\nrecommendation, source links",
        "Optional: Save location or share\ncard via messaging"
    ]
    y_positions = [0.91, 0.75, 0.59, 0.43, 0.27, 0.09]
    for i, s in enumerate(a_steps):
        ax1.text(0.5, y_positions[i], s, ha="center", va="center", bbox=b_kw, fontsize=6.6)
        if i < len(a_steps) - 1:
            ax1.annotate("", xy=(0.5, y_positions[i+1] + 0.055), xytext=(0.5, y_positions[i] - 0.055),
                         arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    # Subplot B: Nearest Haven
    ax2.set_title("(b) 'I Feel Unsafe' Haven Search", fontsize=8.5, weight="bold", pad=8)
    b_steps = [
        "User taps 'I Feel Unsafe'\n(immediate low-friction trigger)",
        "Acquire precise current GPS fix\nfrom browser/device",
        "Query OpenStreetMap nodes:\npolice, hospital, market, pharmacy",
        "Compute Haven Score H(p):\nw_c x open(t) x exp(-d/lambda) x (1-Z/100)",
        "Ranked Safe-Haven List:\nTop 5 places, distance, ETA,\ncall button, turn-by-turn navigation",
        "One-tap live share link or\nSOS escalation trigger"
    ]
    for i, s in enumerate(b_steps):
        ax2.text(0.5, y_positions[i], s, ha="center", va="center", bbox=b_kw, fontsize=6.6)
        if i < len(b_steps) - 1:
            ax2.annotate("", xy=(0.5, y_positions[i+1] + 0.055), xytext=(0.5, y_positions[i] - 0.055),
                         arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#212529", mutation_scale=11))

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig5_resident_flows.png")
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.04)
    plt.close()
    print("Fig 5 saved:", path)

def generate_fig6():
    fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    st_kw = dict(boxstyle="round,pad=0.25,rounding_size=0.03", fc="#ffffff", ec="#333333", lw=1.2)
    red_kw = dict(boxstyle="round,pad=0.25,rounding_size=0.03", fc="#ffe3e3", ec="#c92a2a", lw=1.4)
    warn_kw = dict(boxstyle="round,pad=0.25,rounding_size=0.03", fc="#fff9db", ec="#d97706", lw=1.4)
    sos_kw = dict(boxstyle="round,pad=0.25,rounding_size=0.03", fc="#fee2e2", ec="#991b1b", lw=1.4)

    # State positions
    sx, sy = 0.22, 0.78   # SAFE
    rx, ry = 0.78, 0.78   # IN_RED
    wx, wy = 0.78, 0.22   # WARNING
    ax_pos, ay = 0.22, 0.22  # AUTO_ALERT_SENT

    # Draw state boxes
    ax.text(sx, sy, "SAFE\n(Normal state)", ha="center", va="center",
            bbox=st_kw, fontsize=6.8, weight="bold", fontfamily="Arial", linespacing=1.2)
    ax.text(rx, ry, "IN_RED\n(Inside Red Zone)", ha="center", va="center",
            bbox=red_kw, fontsize=6.8, weight="bold", fontfamily="Arial", linespacing=1.2)
    ax.text(wx, wy, "WARNING\n'Are you safe?' prompt\n(60 s countdown)", ha="center", va="center",
            bbox=warn_kw, fontsize=6.2, fontfamily="Arial", linespacing=1.15)
    ax.text(ax_pos, ay, "AUTO_ALERT_SENT\n(SOS event created,\ncontacts messaged)", ha="center", va="center",
            bbox=sos_kw, fontsize=6.2, weight="bold", fontfamily="Arial", linespacing=1.15)

    # --- Transition arrows ---

    # SAFE -> IN_RED (top, above center)
    ax.annotate("", xy=(0.60, 0.83), xytext=(0.38, 0.83),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#c92a2a", mutation_scale=10))
    ax.text(0.49, 0.90, "zone == RED", ha="center", va="center",
            fontsize=6.0, color="#c92a2a", weight="bold", fontfamily="Arial")

    # IN_RED -> SAFE (top, below center)
    ax.annotate("", xy=(0.38, 0.73), xytext=(0.60, 0.73),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#2b8a3e", mutation_scale=10))
    ax.text(0.49, 0.67, "leaves red / user ok", ha="center", va="center",
            fontsize=5.6, color="#2b8a3e", weight="medium", fontfamily="Arial")

    # IN_RED -> WARNING (right side vertical)
    ax.annotate("", xy=(0.78, 0.35), xytext=(0.78, 0.65),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#d97706", mutation_scale=10))
    ax.text(0.81, 0.50, "dwell >= 10 min\nmoved < 30 m\nno interaction",
            ha="left", va="center", fontsize=5.3, color="#d97706",
            weight="medium", fontfamily="Arial", linespacing=1.2)

    # WARNING -> AUTO_ALERT_SENT (bottom horizontal)
    ax.annotate("", xy=(0.40, 0.22), xytext=(0.60, 0.22),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#991b1b", mutation_scale=10))
    ax.text(0.50, 0.13, "timeout (60 s)", ha="center", va="center",
            fontsize=5.6, color="#991b1b", weight="bold", fontfamily="Arial")

    # AUTO_ALERT_SENT -> SAFE (left side vertical)
    ax.annotate("", xy=(0.22, 0.65), xytext=(0.22, 0.35),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#2b8a3e", mutation_scale=10))
    ax.text(0.19, 0.50, "'I am safe'\ntapped\n(cooldown)",
            ha="right", va="center", fontsize=5.3, color="#2b8a3e",
            weight="medium", fontfamily="Arial", linespacing=1.2)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig6_state_machine.png")
    plt.savefig(path, dpi=300, facecolor='white', bbox_inches='tight', pad_inches=0.04)
    plt.close()
    print("Fig 6 saved:", path)
    plt.close()
    print("Fig 6 saved:", path)

def generate_fig7():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.5, 3.2), dpi=300)

    # Subplot A: Crime-type breakdown
    types = [
        "General Crime / Offence", "Murder & Homicide", "Contraband & Mining",
        "Murder (Separate Label)", "Cybercrime & Fraud", "Sexual Violence & Assault",
        "Theft & Burglary", "Assault & Violent Clash", "All Other Types"
    ]
    counts = [277, 49, 46, 37, 28, 26, 22, 21, 90]
    types.reverse()
    counts.reverse()

    ax1.barh(types, counts, color="#495057", height=0.65)
    ax1.set_xlabel("Number of Records (N = 596)", fontsize=8)
    ax1.set_title("(a) Crime-Type Labels in Database", fontsize=8.5, weight="bold")
    ax1.tick_params(axis='both', labelsize=7)
    for i, v in enumerate(counts):
        ax1.text(v + 3, i, str(v), va='center', fontsize=6.8)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Subplot B: Risk-level split
    risk_labels = ["Low Risk", "Medium Risk", "High Risk"]
    risk_counts = [308, 138, 150]
    risk_colors = ["#8ce99a", "#ffd43b", "#ff8787"]

    wedges, texts, autotexts = ax2.pie(
        risk_counts, labels=risk_labels, autopct="%1.1f%%",
        startangle=90, colors=risk_colors,
        textprops=dict(fontsize=7.5),
        wedgeprops=dict(edgecolor="#495057", linewidth=0.8)
    )
    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_weight("bold")
    ax2.set_title("(b) Risk-Level Split (N = 596)", fontsize=8.5, weight="bold")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig7_dataset_charts.png")
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print("Fig 7 saved:", path)

if __name__ == "__main__":
    generate_fig1()
    generate_fig2()
    generate_fig3()
    generate_fig4()
    generate_fig5()
    generate_fig6()
    generate_fig7()
    print("All 7 IEEE publication figures generated successfully in high resolution!")
