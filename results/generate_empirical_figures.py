import json
import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("results", exist_ok=True)
os.makedirs("research_paper/figures", exist_ok=True)

# -------------------------------------------------------------
# Figure 1: Centroid Cliff & R_ref Sensitivity & Mitigations
# -------------------------------------------------------------
distances = []
z_r100 = []
z_r500 = []
z_r1000 = []
z_r2500 = []
incident_counts = []

with open("results/radial_zone_sweep.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        distances.append(float(row["distance_m"]))
        z_r100.append(float(row["Z_R100"]))
        z_r500.append(float(row["Z_R500"]))
        z_r1000.append(float(row["Z_R1000"]))
        z_r2500.append(float(row["Z_R2500"]))
        incident_counts.append(int(row["incident_count"]))

with open("results/mitigation_comparison.json", "r") as f:
    mit_data = json.load(f)

collapsed_radial = mit_data["collapsed_radial"]
z_collapsed = [float(r["Z_collapsed_R100"]) for r in collapsed_radial]
micro_radial = mit_data["micro_radial"]
z_micro = [float(r["Z_micro_R100"]) for r in micro_radial]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# Top plot: Z vs Distance
ax1.plot(distances, z_r100, "r--o", label=r"Baseline $R_{ref}=100$ (Saturated Cliff)", linewidth=1.8, markersize=4)
ax1.plot(distances, z_r500, "m-.s", label=r"$R_{ref}=500$", linewidth=1.4, markersize=3)
ax1.plot(distances, z_r1000, "g-^", label=r"$R_{ref}=1000$", linewidth=1.4, markersize=3)
ax1.plot(distances, z_r2500, "b-d", label=r"Calibrated $R_{ref}=2500$ (Unsaturated)", linewidth=2.0, markersize=4)
ax1.plot(distances, z_collapsed, "orange", linestyle=":", marker="x", label=r"Mitigation A: Cell Collapse ($s_{cell}$)", linewidth=1.8)
ax1.plot(distances, z_micro, "purple", linestyle="-.", marker="v", label=r"Mitigation B: Pure Micro Tier", linewidth=1.6)

ax1.axhline(60, color="gray", linestyle="--", alpha=0.5, label="Red Threshold (60)")
ax1.axhline(30, color="gray", linestyle=":", alpha=0.5, label="Yellow Threshold (30)")
ax1.axvline(1000, color="black", linestyle="--", alpha=0.7, label=r"Search Radius Boundary ($\rho=1000$ m)")

ax1.set_ylabel("Zone Score Z(q) [0 - 100]", fontsize=10, fontweight="bold")
ax1.set_title("The Locality Centroid Cliff: Risk Field Discontinuity & Normalization", fontsize=11, fontweight="bold")
ax1.grid(True, linestyle=":", alpha=0.6)
ax1.legend(loc="upper right", fontsize=7.5, framealpha=0.9)
ax1.set_ylim(-2, 105)

# Bottom plot: Active Incident Count
ax2.plot(distances, incident_counts, "k-s", linewidth=1.5, markersize=4, label="Active Incidents in Radius")
ax2.axvline(1000, color="black", linestyle="--", alpha=0.7)
ax2.set_xlabel("Radial Distance from Locality Centroid (12.9165, 79.1325) [meters]", fontsize=10, fontweight="bold")
ax2.set_ylabel("Incident Count N", fontsize=10, fontweight="bold")
ax2.grid(True, linestyle=":", alpha=0.6)
ax2.set_yscale("log")
ax2.legend(loc="upper right", fontsize=8)

plt.tight_layout()
fig.savefig("results/fig_centroid_cliff.png", dpi=300)
fig.savefig("research_paper/figures/fig_centroid_cliff.png", dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# Figure 2: Knox Space-Time Interaction (Raw vs Micro-Place)
# -------------------------------------------------------------
with open("results/knox_results.json", "r") as f:
    knox_data = json.load(f)

raw_tests = knox_data["raw_knox_tests"]
micro_tests = knox_data["micro_place_knox_tests"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=False)

# Raw Knox: Ratio Obs / Exp
labels = [f"s{t['ds_meters']}\nt{t['dt_days']}d" for t in raw_tests]
x_pos = np.arange(len(labels))
ratios_raw = [t["ratio_obs_exp"] for t in raw_tests]
p_raw = [t["pseudo_p"] for t in raw_tests]

ax1.bar(x_pos, ratios_raw, color=["salmon" if p > 0.05 else "darkred" for p in p_raw], edgecolor="black", width=0.6)
ax1.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(labels, fontsize=7)
ax1.set_ylabel("Observed / Expected Ratio (Obs/Exp)", fontsize=9, fontweight="bold")
ax1.set_title("Raw Corpus Knox Test\n(110,888 Coincident Pairs d=0)", fontsize=9.5, fontweight="bold")
ax1.set_ylim(0.8, 1.2)
ax1.grid(True, linestyle=":", alpha=0.6)

# Micro Knox: Ratio Obs / Exp
ratios_micro = [t["ratio_obs_exp"] for t in micro_tests]
p_micro = [t["pseudo_p"] for t in micro_tests]
colors_micro = ["forestgreen" if p < 0.05 else "lightgray" for p in p_micro]

ax2.bar(x_pos, ratios_micro, color=colors_micro, edgecolor="black", width=0.6)
ax2.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(labels, fontsize=7)
ax2.set_ylabel("Observed / Expected Ratio (Obs/Exp)", fontsize=9, fontweight="bold")
ax2.set_title("Micro-Place Knox Test\n(Statistically Significant at dt=7d, 14d)", fontsize=9.5, fontweight="bold")
ax2.set_ylim(0.5, 2.2)
ax2.grid(True, linestyle=":", alpha=0.6)

plt.tight_layout()
fig.savefig("results/fig_knox_interaction.png", dpi=300)
fig.savefig("research_paper/figures/fig_knox_interaction.png", dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# Figure 3: Safe Haven Multi-Factor Utility Profiles
# -------------------------------------------------------------
haven_rows = []
with open("results/safe_haven_rankings.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        haven_rows.append(row)

# Filter top 3 for Katpadi, CMC, Bagayam
loc_groups = {"Katpadi": [], "CMC": [], "Bagayam": []}
for r in haven_rows:
    if len(loc_groups[r["target_location"]]) < 3:
        loc_groups[r["target_location"]].append(r)

fig, ax = plt.subplots(figsize=(7.2, 3.2))
names = []
scores = []
colors = []
for loc, items in loc_groups.items():
    for it in items:
        short_name = it["haven_name"][:18] + (".." if len(it["haven_name"]) > 18 else "")
        names.append(f"{loc}:\n{short_name}")
        scores.append(float(it["utility_score_H"]))
        if loc == "Katpadi":
            colors.append("#2b5c8f")
        elif loc == "CMC":
            colors.append("#d95f02")
        else:
            colors.append("#2ca02c")

bars = ax.bar(range(len(names)), scores, color=colors, edgecolor="black", width=0.6)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, fontsize=7.5, rotation=25, ha="right")
ax.set_ylabel("Utility Metric H(p) [0 - 1]", fontsize=9, fontweight="bold")
ax.set_title("Safe Haven Multi-Factor Utility Ranking (Top 3 per Sector)", fontsize=10, fontweight="bold")
ax.set_ylim(0, 1.0)
ax.grid(True, axis="y", linestyle=":", alpha=0.6)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f"{yval:.3f}", ha='center', va='bottom', fontsize=7, fontweight="bold")

plt.tight_layout()
fig.savefig("results/fig_safe_havens.png", dpi=300)
fig.savefig("research_paper/figures/fig_safe_havens.png", dpi=300)
plt.close(fig)

print("Empirical figures successfully generated and saved to results/ and research_paper/figures/.")
