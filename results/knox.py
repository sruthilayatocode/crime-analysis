import sqlite3
import math
import json
import csv
import sys
import numpy as np
from datetime import datetime

DB_PATH = "backend/instance/crimesense.db"
EARTH_RADIUS = 6371000.0

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
rows = cur.execute("SELECT id, latitude, longitude, published_date, crime_date FROM crimes;").fetchall()
conn.close()

def parse_date(d_str):
    if not d_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(d_str).strip()[:19], fmt)
        except Exception:
            pass
    return None

def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(min(1.0, max(0.0, a))))

records = []
for r in rows:
    if r["latitude"] is not None and r["longitude"] is not None:
        dt = parse_date(r["published_date"]) or parse_date(r["crime_date"])
        if dt is not None:
            records.append({
                "id": r["id"],
                "lat": float(r["latitude"]),
                "lon": float(r["longitude"]),
                "date": dt,
                "days": (dt - datetime(1970, 1, 1)).total_seconds() / 86400.0
            })

N = len(records)
print(f"Total valid space-time records: {N}")

lats = np.array([r["lat"] for r in records], dtype=np.float64)
lons = np.array([r["lon"] for r in records], dtype=np.float64)
times = np.array([r["days"] for r in records], dtype=np.float64)

# Precompute pair indices as numpy arrays
p0_list = []
p1_list = []
for i in range(N):
    for j in range(i + 1, N):
        p0_list.append(i)
        p1_list.append(j)

p0 = np.array(p0_list, dtype=np.int32)
p1 = np.array(p1_list, dtype=np.int32)
n_pairs = len(p0)
print(f"Total pairs: {n_pairs}")

# Calculate pairwise spatial distances
spatial_dists = np.zeros(n_pairs, dtype=np.float32)
zero_count = 0
for idx in range(n_pairs):
    d = haversine(lats[p0[idx]], lons[p0[idx]], lats[p1[idx]], lons[p1[idx]])
    spatial_dists[idx] = d
    if d == 0.0:
        zero_count += 1

print(f"Pairs with d_ij == 0 (coincident): {zero_count} ({round(zero_count/n_pairs*100, 2)}%)")

# Precompute time diffs
time_diffs_orig = np.abs(times[p0] - times[p1])

ds_list = [250.0, 500.0, 1000.0]
dt_list = [7.0, 14.0, 30.0]
n_perms = 999

def run_fast_knox(p0_arr, p1_arr, s_dists, t_orig, t_arr, ds_vals, dt_vals, perms, seed=42):
    np.random.seed(seed)
    results = []
    for ds in ds_vals:
        s_mask = (s_dists <= ds)
        n_space = int(np.count_nonzero(s_mask))
        sub_p0 = p0_arr[s_mask]
        sub_p1 = p1_arr[s_mask]
        sub_t_orig = t_orig[s_mask]
        
        for dt in dt_vals:
            x_obs = int(np.count_nonzero(sub_t_orig <= dt))
            
            # Vectorized permutations: generate permuted array
            perm_counts = np.zeros(perms, dtype=np.int32)
            for k in range(perms):
                perm_t = np.random.permutation(t_arr)
                perm_counts[k] = np.count_nonzero(np.abs(perm_t[sub_p0] - perm_t[sub_p1]) <= dt)
                
            exp_mean = float(np.mean(perm_counts))
            exp_std = float(np.std(perm_counts))
            ge_count = int(np.count_nonzero(perm_counts >= x_obs))
            pseudo_p = (1.0 + ge_count) / (1.0 + perms)
            
            results.append({
                "ds_meters": int(ds),
                "dt_days": int(dt),
                "pairs_space_close": n_space,
                "observed_X": x_obs,
                "expected_mean": round(exp_mean, 2),
                "expected_std": round(exp_std, 2),
                "ratio_obs_exp": round(x_obs / exp_mean, 3) if exp_mean > 0 else 0.0,
                "pseudo_p": round(pseudo_p, 4),
                "significant_005": bool(pseudo_p < 0.05),
                "significant_bonferroni": bool(pseudo_p < (0.05 / 9.0))
            })
            print(f"ds={int(ds)}m, dt={int(dt)}d -> Obs={x_obs}, Exp={round(exp_mean, 2)}, p={round(pseudo_p, 4)}")
            sys.stdout.flush()
    return results

print("\n--- Running Knox on RAW dataset (596 records) ---")
raw_knox = run_fast_knox(p0, p1, spatial_dists, time_diffs_orig, times, ds_list, dt_list, n_perms)

# Now on micro-place (non-centroid) records
micro_records = [r for r in records if not (round(r["lat"], 4) == 12.9165 and round(r["lon"], 4) == 79.1325)]
N_micro = len(micro_records)
print(f"\n--- Running Knox on Micro-Place (non-centroid) records ({N_micro} records) ---")

p0_m = []
p1_m = []
for i in range(N_micro):
    for j in range(i + 1, N_micro):
        p0_m.append(i)
        p1_m.append(j)

p0_m = np.array(p0_m, dtype=np.int32)
p1_m = np.array(p1_m, dtype=np.int32)
n_micro_pairs = len(p0_m)

lats_m = np.array([r["lat"] for r in micro_records], dtype=np.float64)
lons_m = np.array([r["lon"] for r in micro_records], dtype=np.float64)
times_m = np.array([r["days"] for r in micro_records], dtype=np.float64)

s_dists_m = np.zeros(n_micro_pairs, dtype=np.float32)
for idx in range(n_micro_pairs):
    s_dists_m[idx] = haversine(lats_m[p0_m[idx]], lons_m[p0_m[idx]], lats_m[p1_m[idx]], lons_m[p1_m[idx]])

t_orig_m = np.abs(times_m[p0_m] - times_m[p1_m])

micro_knox = run_fast_knox(p0_m, p1_m, s_dists_m, t_orig_m, times_m, ds_list, dt_list, n_perms)

with open("results/knox_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(raw_knox[0].keys()))
    writer.writeheader()
    writer.writerows(raw_knox)

with open("results/knox_results.json", "w") as f:
    json.dump({
        "total_records": N,
        "total_pairs": n_pairs,
        "coincident_pairs_d0": zero_count,
        "coincident_pair_pct": round(zero_count / n_pairs * 100, 2),
        "bonferroni_threshold_alpha": round(0.05 / 9.0, 5),
        "raw_knox_tests": raw_knox,
        "micro_place_knox_tests": micro_knox
    }, f, indent=2)

print("\nKnox space-time analysis completed and saved to results/knox_results.csv and results/knox_results.json.")
