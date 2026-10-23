"""
generate_fig2_pipeline.py
=========================
Generates Fig. 2: CrimeSense publication-quality system pipeline diagram
for an IEEE two-column research paper (fits 3.4 in single column).

100% Orthogonal Precision Routing:
- Tier 1: [1. Crime News Sources] -> [2. Text Extraction] -> [3. Validation & Filtering]
- Stepped connector from Stage 3 down & left into Stage 4
- Tier 2: [4. Locality Resolution (Left)] --(dashed)--> [Unresolved Locality (Right)]
- Pure vertical arrow from Stage 4 down to Stage 5
- Tier 3: [5. Severity Classification (Left)] --------> [6. SQLite Database (Right)]
- Pure vertical arrow from Stage 6 down to Stage 7
- Clean outer dashed routing from Unresolved Locality down to Stage 7
- Tier 4: [8. Flask Backend API (Left)] <-------------- [7. Hotspot Analysis (Right)]
- Pure vertical arrow from Stage 8 down to Stage 9
- Tier 5: [9. React Frontend (Left)] -----------------> [10. Proximity Alert (Right)]

Zero diagonal lines. Zero overlapping words. Zero margin overflow.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "figures", "fig2_pipeline.png")

# Clean IEEE palette
ACCENT_EDGE = "#1D4ED8"   # Steel / Royal Blue
ACCENT_FILL = "#EFF6FF"   # Clean light blue tint
BG_BOX      = "#FAFAFA"   # Neutral crisp off-white
BORDER_BOX  = "#262626"   # Sharp dark border
ARROW_C     = "#262626"   # Dark arrow charcoal
DASH_EDGE   = "#2563EB"   # Blue for uncertainty
DASH_FILL   = "#F0F7FF"
TEXT_MAIN   = "#111827"   # High contrast dark charcoal
TEXT_SUB    = "#4B5563"   # Slate gray subtitle

def draw_box(ax, cx, cy, w, h, title_lines, sub=None, accent=False, dashed=False):
    """Draw a rounded stage box with multiline text centered at (cx, cy)."""
    fc = DASH_FILL if dashed else (ACCENT_FILL if accent else BG_BOX)
    ec = DASH_EDGE if dashed else (ACCENT_EDGE if accent else BORDER_BOX)
    ls = '--' if dashed else '-'
    lw = 1.3 if (accent or dashed) else 1.1

    rect = FancyBboxPatch(
        (cx - w / 2.0, cy - h / 2.0), w, h,
        boxstyle="round,pad=0,rounding_size=0.016",
        facecolor=fc, edgecolor=ec,
        linewidth=lw, linestyle=ls, zorder=3
    )
    ax.add_patch(rect)

    if sub:
        ax.text(cx, cy + 0.16 * h, title_lines, ha="center", va="center",
                fontsize=6.5, fontweight="bold", fontfamily="Arial", color=TEXT_MAIN,
                linespacing=1.15, zorder=4)
        ax.text(cx, cy - 0.25 * h, sub, ha="center", va="center",
                fontsize=5.2, fontfamily="Arial", color=TEXT_SUB, zorder=4)
    else:
        ax.text(cx, cy, title_lines, ha="center", va="center",
                fontsize=6.5, fontweight="bold", fontfamily="Arial", color=TEXT_MAIN,
                linespacing=1.2, zorder=4)

def draw_cylinder(ax, cx, cy, w, h, title_lines, sub=None):
    """Draw a crisp database cylinder centered at (cx, cy)."""
    ew = h * 0.22
    fc = BG_BOX
    ec = BORDER_BOX

    # Body
    body = plt.Rectangle((cx - w / 2.0, cy - h / 2.0 + ew / 2.0), w, h - ew,
                         facecolor=fc, edgecolor=ec, linewidth=1.1, zorder=3)
    ax.add_patch(body)

    # Bottom cap
    theta = np.linspace(np.pi, 2 * np.pi, 80)
    bx = cx + (w / 2.0) * np.cos(theta)
    by = (cy - h / 2.0 + ew / 2.0) + (ew / 2.0) * np.sin(theta)
    ax.fill(bx, by, color=fc, zorder=2)
    ax.plot(bx, by, color=ec, linewidth=1.1, zorder=3)

    # Top cap
    top_y = cy + h / 2.0 - ew / 2.0
    theta_full = np.linspace(0, 2 * np.pi, 80)
    tx = cx + (w / 2.0) * np.cos(theta_full)
    ty = top_y + (ew / 2.0) * np.sin(theta_full)
    ax.fill(tx, ty, color=fc, zorder=4)
    ax.plot(tx, ty, color=ec, linewidth=1.1, zorder=5)

    if sub:
        ax.text(cx, cy + 0.09 * h, title_lines, ha="center", va="center",
                fontsize=6.5, fontweight="bold", fontfamily="Arial", color=TEXT_MAIN,
                linespacing=1.15, zorder=6)
        ax.text(cx, cy - 0.25 * h, sub, ha="center", va="center",
                fontsize=5.2, fontfamily="Arial", color=TEXT_SUB, zorder=6)
    else:
        ax.text(cx, cy - 0.005, title_lines, ha="center", va="center",
                fontsize=6.5, fontweight="bold", fontfamily="Arial", color=TEXT_MAIN,
                linespacing=1.2, zorder=6)

def draw_arrow(ax, x1, y1, x2, y2, dashed=False, color=ARROW_C):
    """Draw a clean directional arrow."""
    ls = '--' if dashed else '-'
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=1.1,
            linestyle=ls,
            mutation_scale=9,
            shrinkA=1, shrinkB=1
        ),
        zorder=2
    )

def build_figure():
    fig_w = 3.4   # IEEE column width (inches)
    fig_h = 5.6   # Vertical height
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # ── Legend at top ──────────────────────────────────────────────
    leg_y = 0.97
    leg_x = 0.50
    ax.add_patch(FancyBboxPatch((leg_x - 0.22, leg_y - 0.010), 0.035, 0.020,
                                boxstyle="round,pad=0,rounding_size=0.005",
                                facecolor=ACCENT_FILL, edgecolor=ACCENT_EDGE, lw=1.1, zorder=3))
    ax.text(leg_x - 0.17, leg_y, "Uncertainty-aware processing / alert stage",
            fontsize=5.8, fontfamily="Arial", color=TEXT_MAIN, va="center", zorder=4)

    # ── TIER 1: Ingestion (Stages 1, 2, 3) ─────────────────────────
    t1_y = 0.885
    t1_w = 0.285
    t1_h = 0.076
    t1_cxs = [0.17, 0.50, 0.83]

    draw_box(ax, t1_cxs[0], t1_y, t1_w, t1_h, "1. Public Crime\nNews Sources", "Web portals & bulletins")
    draw_box(ax, t1_cxs[1], t1_y, t1_w, t1_h, "2. Text Extraction\nof Crime Details", "NLP detail parsing")
    draw_box(ax, t1_cxs[2], t1_y, t1_w, t1_h, "3. Validation &\nFiltering", "Relevance & duplicate check")

    # Arrows in Tier 1
    draw_arrow(ax, t1_cxs[0] + t1_w/2, t1_y, t1_cxs[1] - t1_w/2, t1_y)
    draw_arrow(ax, t1_cxs[1] + t1_w/2, t1_y, t1_cxs[2] - t1_w/2, t1_y)

    # Standard 2-column dimensions for Tiers 2 to 5
    cx_left  = 0.25
    cx_right = 0.73
    bw = 0.39
    bh = 0.078

    # ── Connector from Tier 1 (Stage 3) down to Tier 2 (Stage 4) ───
    # Orthogonal stepped connector in the clear space between Tier 1 and Tier 2
    t2_y = 0.715
    channel_y = (t1_y - t1_h/2 + t2_y + bh/2) / 2.0  # 0.800
    ax.plot([t1_cxs[2], t1_cxs[2], cx_left, cx_left],
            [t1_y - t1_h/2, channel_y, channel_y, t2_y + bh/2 + 0.015],
            color=ARROW_C, lw=1.1, zorder=2)
    ax.annotate(
        "", xy=(cx_left, t2_y + bh/2), xytext=(cx_left, t2_y + bh/2 + 0.015),
        arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=1.1, mutation_scale=9),
        zorder=2
    )

    # ── TIER 2: Geocoding & Branch (Stage 4 & Unresolved) ──────────
    draw_box(ax, cx_left, t2_y, bw, bh, "4. Locality Resolution\n& Geocoding", "Nominatim & coordinates", accent=True)
    draw_box(ax, cx_right, t2_y, bw, bh, "Unresolved Locality\nBranch", "Flagged as spatial uncertainty", accent=True, dashed=True)

    # Dashed arrow from Stage 4 (Left) across to Unresolved Locality (Right)
    draw_arrow(ax, cx_left + bw/2, t2_y, cx_right - bw/2, t2_y, dashed=True, color=DASH_EDGE)
    ax.text((cx_left + bw/2 + cx_right - bw/2)/2, t2_y + 0.014, "unresolved",
            fontsize=4.6, fontfamily="Arial", color=DASH_EDGE, ha="center", va="bottom")

    # ── TIER 3: Classification & Storage (Stages 5 & 6) ────────────
    t3_y = 0.540
    # Downward arrow from Stage 4 (Left) straight down to Stage 5 (Left)
    draw_arrow(ax, cx_left, t2_y - bh/2, cx_left, t3_y + bh/2)
    ax.text(cx_left + 0.020, (t2_y - bh/2 + t3_y + bh/2)/2, "resolved",
            fontsize=4.8, fontfamily="Arial", color=ARROW_C, ha="left", va="center")

    draw_box(ax, cx_left, t3_y, bw, bh, "5. Severity\nClassification", "Critical, High, Med, Low, Unk")
    draw_cylinder(ax, cx_right, t3_y, bw, bh + 0.016, "6. SQLite\nDatabase", "596 verified crime records")

    # Arrow from Stage 5 across to Stage 6
    draw_arrow(ax, cx_left + bw/2, t3_y, cx_right - bw/2, t3_y)

    # ── TIER 4: Analytics & Services (Stages 7 & 8) ────────────────
    t4_y = 0.365
    # Pure vertical solid arrow from SQLite Database (Tier 3 Right) straight down to Hotspot Analysis (Tier 4 Right)
    draw_arrow(ax, cx_right, t3_y - bh/2 - 0.008, cx_right, t4_y + bh/2)
    ax.text(cx_right - 0.022, (t3_y - bh/2 + t4_y + bh/2)/2, "query records",
            fontsize=4.8, fontfamily="Arial", color=ARROW_C, ha="right", va="center")

    # Dashed vertical arrow from Unresolved Locality (Tier 2 Right) down to Hotspot Analysis (Tier 4 Right)
    # Routes cleanly with dedicated margin
    x_dash_route = cx_right + bw/2 + 0.018
    ax.plot([cx_right + bw/2, x_dash_route, x_dash_route, cx_right + bw/2],
            [t2_y, t2_y, t4_y, t4_y],
            color=DASH_EDGE, lw=1.1, linestyle="--", zorder=2)
    ax.annotate(
        "", xy=(cx_right + bw/2, t4_y), xytext=(x_dash_route, t4_y),
        arrowprops=dict(arrowstyle="-|>", color=DASH_EDGE, lw=1.1, linestyle="--", mutation_scale=8),
        zorder=2
    )
    ax.text(x_dash_route + 0.008, (t2_y + t4_y)/2, "uncertainty\npropagation",
            fontsize=4.4, fontfamily="Arial", color=DASH_EDGE, ha="left", va="center")

    draw_box(ax, cx_right, t4_y, bw, bh, "7. Hotspot Analysis\n(Uncertainty-Aware)", "Spatial decay modeling", accent=True)
    draw_box(ax, cx_left, t4_y, bw, bh, "8. Flask Backend\nAPI Services", "REST microservices & JWT auth")

    # Arrow from Stage 7 (Right) across to Stage 8 (Left)
    draw_arrow(ax, cx_right - bw/2, t4_y, cx_left + bw/2, t4_y)

    # ── TIER 5: Presentation & Delivery (Stages 9 & 10) ────────────
    t5_y = 0.190
    # Downward vertical arrow from Flask Backend (Tier 4 Left) straight down to React Dashboard (Tier 5 Left)
    draw_arrow(ax, cx_left, t4_y - bh/2, cx_left, t5_y + bh/2)
    ax.text(cx_left + 0.020, (t4_y - bh/2 + t5_y + bh/2)/2, "JSON payload",
            fontsize=4.8, fontfamily="Arial", color=ARROW_C, ha="left", va="center")

    draw_box(ax, cx_left, t5_y, bw, bh, "9. React Frontend\nDashboard", "Interactive Leaflet maps & havens")
    draw_box(ax, cx_right, t5_y, bw, bh, "10. Proximity Alert\nto User (Final Output)", "Audible/push alert notification", accent=True)

    # Arrow from Stage 9 across to Stage 10
    draw_arrow(ax, cx_left + bw/2, t5_y, cx_right - bw/2, t5_y)

    # ── Figure Caption ────────────────────────────────────────────
    cap = (
        "Fig. 2. CrimeSense end-to-end processing pipeline across data ingestion,\n"
        "geocoding, uncertainty propagation, hotspot modeling, and alert delivery."
    )
    ax.text(0.5, 0.05, cap, ha="center", va="center",
            fontsize=6.6, fontfamily="Times New Roman", color=TEXT_MAIN, linespacing=1.35)

    plt.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.01)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH, dpi=300, facecolor='white', bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print(f"Fig 2 pipeline successfully generated at: {OUT_PATH}")

if __name__ == "__main__":
    build_figure()
