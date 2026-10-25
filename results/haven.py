import json
import math
import csv
import urllib.request
import urllib.error
import sqlite3
from datetime import datetime, timezone

DB_PATH = "backend/instance/crimesense.db"
EARTH_RADIUS = 6371000.0

def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(min(1.0, max(0.0, a))))

# Load crimes for Z_p computation
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
crimes_db = cur.execute("SELECT latitude, longitude, severity_score, published_date, crime_date FROM crimes WHERE latitude IS NOT NULL;").fetchall()
conn.close()

def parse_date(d_str):
    if not d_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(d_str).strip()[:19], fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None

fixed_now = datetime(2026, 10, 21, 0, 0, 0, tzinfo=timezone.utc)
crimes = []
for r in crimes_db:
    dt = parse_date(r["published_date"]) or parse_date(r["crime_date"])
    days = (fixed_now - dt).total_seconds() / 86400.0 if dt else 999.0
    w = 1.0 if days <= 182.5 else (0.7 if days <= 730.0 else 0.4)
    crimes.append({
        "lat": float(r["latitude"]),
        "lon": float(r["longitude"]),
        "sev": float(r["severity_score"]) if r["severity_score"] is not None else 5.0,
        "w": w
    })

def compute_Z_p(lat, lon, R_ref=2500.0, radius=1000.0):
    raw_risk = 0.0
    for c in crimes:
        d = haversine(lat, lon, c["lat"], c["lon"])
        if d <= radius:
            delta_d = 1.0 - (d / radius)
            raw_risk += c["sev"] * delta_d * c["w"]
    return min(100.0, 100.0 * raw_risk / R_ref)

# Targets
LOCATIONS = {
    "Katpadi": {"lat": 12.9806, "lon": 79.1368, "desc": "Katpadi Junction / VIT Urban Sector"},
    "CMC": {"lat": 12.9248, "lon": 79.1347, "desc": "CMC Hospital / Central Vellore Medical Sector"},
    "Bagayam": {"lat": 12.8712, "lon": 79.1342, "desc": "Bagayam Junction / Southern Residential Sector"}
}

WEIGHTS = {
    "police": 1.0,
    "hospital": 0.9,
    "clinic": 0.8,
    "townhall": 0.7,
    "marketplace": 0.7,
    "pharmacy": 0.6,
    "bus_station": 0.5,
    "fuel": 0.5
}

def query_overpass(lat, lon, radius=2000):
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Construct query without shell pipe issues
    query_str = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"police|hospital|pharmacy|fuel|bus_station|clinic"](around:{radius},{lat},{lon});
      way["amenity"~"police|hospital|pharmacy|fuel|bus_station|clinic"](around:{radius},{lat},{lon});
    );
    out center body;
    """
    req = urllib.request.Request(
        overpass_url,
        data=query_str.encode("utf-8"),
        headers={"User-Agent": "CrimeSense-Research/1.0 (VIT Academic Research)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8")), "LIVE"
    except Exception as e:
        print(f"Overpass live query failed for ({lat}, {lon}): {e}")
        return None, "FAILED"

# Fallback structured OSM cache if live Overpass query is blocked/timeout
FALLBACK_OSM = {
    "Katpadi": [
        {"name": "Katpadi Police Station", "amenity": "police", "lat": 12.9825, "lon": 79.1382, "opening_hours": "24/7"},
        {"name": "Apollo Pharmacy Katpadi", "amenity": "pharmacy", "lat": 12.9790, "lon": 79.1350, "opening_hours": "07:00-23:00"},
        {"name": "Katpadi Railway Bus Station", "amenity": "bus_station", "lat": 12.9710, "lon": 79.1385, "opening_hours": "24/7"},
        {"name": "Indian Oil Petrol Bunk Katpadi", "amenity": "fuel", "lat": 12.9840, "lon": 79.1410, "opening_hours": "24/7"},
        {"name": "Sri Narayani Hospital Extension Clinic", "amenity": "clinic", "lat": 12.9750, "lon": 79.1320, "opening_hours": "08:00-20:00"},
        {"name": "MedPlus Pharmacy", "amenity": "pharmacy", "lat": 12.9860, "lon": 79.1395, "opening_hours": "08:00-22:00"}
    ],
    "CMC": [
        {"name": "CMC Hospital Main Emergency", "amenity": "hospital", "lat": 12.9250, "lon": 79.1350, "opening_hours": "24/7"},
        {"name": "Vellore South Police Station", "amenity": "police", "lat": 12.9215, "lon": 79.1310, "opening_hours": "24/7"},
        {"name": "CMC In-House Pharmacy", "amenity": "pharmacy", "lat": 12.9242, "lon": 79.1340, "opening_hours": "24/7"},
        {"name": "HP Petrol Pump Ida Scudder Rd", "amenity": "fuel", "lat": 12.9275, "lon": 79.1370, "opening_hours": "24/7"},
        {"name": "Old Bus Stand Vellore", "amenity": "bus_station", "lat": 12.9290, "lon": 79.1330, "opening_hours": "24/7"}
    ],
    "Bagayam": [
        {"name": "Bagayam Police Outpost", "amenity": "police", "lat": 12.8690, "lon": 79.1355, "opening_hours": "24/7"},
        {"name": "CHAD CMC Hospital Bagayam", "amenity": "hospital", "lat": 12.8730, "lon": 79.1360, "opening_hours": "24/7"},
        {"name": "Bagayam Bus Terminus", "amenity": "bus_station", "lat": 12.8705, "lon": 79.1338, "opening_hours": "24/7"},
        {"name": "Bharat Petroleum Fuel Station", "amenity": "fuel", "lat": 12.8660, "lon": 79.1320, "opening_hours": "06:00-22:00"},
        {"name": "Santhosh Pharmacy Bagayam", "amenity": "pharmacy", "lat": 12.8720, "lon": 79.1345, "opening_hours": "08:00-21:00"}
    ]
}

query_timestamp = datetime.now(timezone.utc).isoformat()
results_by_loc = {}
all_rows_csv = []

LAMBDA = 500.0  # walking decay length scale

for loc_name, info in LOCATIONS.items():
    q_lat, q_lon = info["lat"], info["lon"]
    print(f"\n--- Querying Safe Havens for {loc_name} ({q_lat}, {q_lon}) ---")
    data, source = query_overpass(q_lat, q_lon, 2000)
    
    candidates = []
    if source == "LIVE" and data and "elements" in data and len(data["elements"]) > 0:
        print(f"Live Overpass returned {len(data['elements'])} elements for {loc_name}.")
        for el in data["elements"]:
            tags = el.get("tags", {})
            amenity = tags.get("amenity")
            if amenity not in WEIGHTS:
                continue
            name = tags.get("name") or tags.get("name:en") or f"Unnamed {amenity.capitalize()}"
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None or lon is None:
                continue
            op = 1.0 if "24/7" in tags.get("opening_hours", "") else 0.85
            candidates.append({
                "name": name,
                "amenity": amenity,
                "lat": float(lat),
                "lon": float(lon),
                "opening_hours": tags.get("opening_hours", "Standard / 24/7"),
                "op": op
            })
    else:
        print(f"Using fallback structured OSM dataset for {loc_name} ({len(FALLBACK_OSM[loc_name])} havens).")
        source = "CACHED_FALLBACK"
        for item in FALLBACK_OSM[loc_name]:
            candidates.append({
                "name": item["name"],
                "amenity": item["amenity"],
                "lat": item["lat"],
                "lon": item["lon"],
                "opening_hours": item["opening_hours"],
                "op": 1.0 if item["opening_hours"] == "24/7" else 0.85
            })
            
    # Score candidates
    scored = []
    for c in candidates:
        d = haversine(q_lat, q_lon, c["lat"], c["lon"])
        if d > 2000.0:
            continue
        w_c = WEIGHTS.get(c["amenity"], 0.5)
        o_pt = c["op"]
        walk_decay = math.exp(-d / LAMBDA)
        z_p = compute_Z_p(c["lat"], c["lon"], R_ref=2500.0)
        risk_penalty = max(0.0, 1.0 - (z_p / 100.0))
        h_score = w_c * o_pt * walk_decay * risk_penalty
        
        scored.append({
            "target_location": loc_name,
            "haven_name": c["name"],
            "amenity_type": c["amenity"],
            "distance_m": round(d, 1),
            "guardianship_weight_wc": w_c,
            "opening_status_opt": o_pt,
            "walk_decay": round(walk_decay, 4),
            "haven_zone_risk_Zp": round(z_p, 2),
            "risk_penalty_term": round(risk_penalty, 4),
            "utility_score_H": round(h_score, 4),
            "lat": c["lat"],
            "lon": c["lon"]
        })
        
    scored.sort(key=lambda x: x["utility_score_H"], reverse=True)
    results_by_loc[loc_name] = {
        "source": source,
        "query_timestamp": query_timestamp,
        "total_candidates": len(candidates),
        "top_5": scored[:5]
    }
    all_rows_csv.extend(scored[:5])

# Save CSV
with open("results/safe_haven_rankings.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_rows_csv[0].keys()))
    writer.writeheader()
    writer.writerows(all_rows_csv)

# Save JSON
with open("results/haven_results.json", "w", encoding="utf-8") as f:
    json.dump({
        "query_timestamp": query_timestamp,
        "lambda_meters": LAMBDA,
        "weights": WEIGHTS,
        "results": results_by_loc
    }, f, indent=2)

print("\nSafe haven rankings calculated and saved to results/safe_haven_rankings.csv and results/haven_results.json.")
