import sqlite3
import math
import json
import csv
import numpy as np
from sklearn.cluster import DBSCAN

DB_PATH = "backend/instance/crimesense.db"
EARTH_RADIUS = 6371000.0  # meters

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
rows = cur.execute("SELECT id, latitude, longitude, locality, district FROM crimes WHERE latitude IS NOT NULL AND longitude IS NOT NULL;").fetchall()
conn.close()

coords_deg = np.array([[float(r["latitude"]), float(r["longitude"])] for r in rows])
coords_rad = np.radians(coords_deg)
N = len(coords_rad)
print(f"Total geocoded points for DBSCAN: {N}")

# Non-centroid micro records
micro_indices = [
    i for i, r in enumerate(rows)
    if not (round(float(r["latitude"]), 4) == 12.9165 and round(float(r["longitude"]), 4) == 79.1325)
]
coords_micro_rad = coords_rad[micro_indices]
N_micro = len(coords_micro_rad)
print(f"Total micro-place points for DBSCAN: {N_micro}")

eps_meters_list = [250, 500, 750, 1000, 1500, 2000]
min_pts_list = [3, 5, 10, 15, 20]

sweep_results = []

for eps_m in eps_meters_list:
    eps_rad = eps_m / EARTH_RADIUS
    for min_pts in min_pts_list:
        # 1. Full Dataset
        db = DBSCAN(eps=eps_rad, min_samples=min_pts, metric="haversine").fit(coords_rad)
        labels = db.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = int(np.sum(labels == -1))
        noise_share = round((n_noise / N) * 100.0, 2)
        
        # Cluster sizes
        unique, counts = np.unique(labels[labels != -1], return_counts=True)
        cluster_sizes = sorted(counts.tolist(), reverse=True) if len(counts) > 0 else []
        largest_cluster = cluster_sizes[0] if cluster_sizes else 0
        
        # 2. Micro Dataset
        db_m = DBSCAN(eps=eps_rad, min_samples=min_pts, metric="haversine").fit(coords_micro_rad)
        labels_m = db_m.labels_
        n_clusters_m = len(set(labels_m)) - (1 if -1 in labels_m else 0)
        n_noise_m = int(np.sum(labels_m == -1))
        noise_share_m = round((n_noise_m / N_micro) * 100.0, 2)
        unique_m, counts_m = np.unique(labels_m[labels_m != -1], return_counts=True)
        cluster_sizes_m = sorted(counts_m.tolist(), reverse=True) if len(counts_m) > 0 else []
        largest_cluster_m = cluster_sizes_m[0] if cluster_sizes_m else 0
        
        sweep_results.append({
            "eps_meters": eps_m,
            "min_pts": min_pts,
            "clusters_full": n_clusters,
            "noise_points_full": n_noise,
            "noise_share_pct_full": noise_share,
            "largest_cluster_full": largest_cluster,
            "clusters_micro": n_clusters_m,
            "noise_points_micro": n_noise_m,
            "noise_share_pct_micro": noise_share_m,
            "largest_cluster_micro": largest_cluster_m,
        })

with open("results/dbscan_sweep.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
    writer.writeheader()
    writer.writerows(sweep_results)

# Detailed analysis for representative parameters
# eps=500m, min_pts=5
db_rep = DBSCAN(eps=500.0/EARTH_RADIUS, min_samples=5, metric="haversine").fit(coords_rad)
labels_rep = db_rep.labels_
cluster_breakdown = {}
for cl_id in set(labels_rep):
    idx_list = np.where(labels_rep == cl_id)[0]
    localities = [rows[i]["locality"] or "Unknown" for i in idx_list]
    from collections import Counter
    loc_counts = Counter(localities).most_common(3)
    cluster_breakdown[int(cl_id)] = {
        "count": len(idx_list),
        "dominant_locations": loc_counts,
        "sample_coord": [float(rows[idx_list[0]]["latitude"]), float(rows[idx_list[0]]["longitude"])]
    }

with open("results/dbscan_results.json", "w") as f:
    json.dump({
        "total_records": N,
        "micro_records": N_micro,
        "sweep": sweep_results,
        "representative_clustering_500m_minpts5": cluster_breakdown
    }, f, indent=2)

print("DBSCAN parameter sweep finished successfully.")
