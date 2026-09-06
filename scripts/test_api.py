"""
test_api.py
===========
Exercise every CrimeSense API endpoint via FastAPI's TestClient and print
a summary of the results.  Run:

    python scripts/test_api.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def show(label, resp):
    ok = resp.status_code == 200
    body = resp.json()
    print("  [%s] %s -> %d" % ("OK" if ok else "FAIL", label, resp.status_code))
    return body


print("=" * 70)
print("API ENDPOINT TESTS")
print("=" * 70)

# /health
b = show("GET /health", client.get("/health"))
print("      status=%s total_crimes=%s" % (b.get("status"), b.get("total_crimes")))

# / -> root
show("GET /", client.get("/"))

# all crimes
b = show("GET /crimes", client.get("/crimes?limit=500"))
print("      total=%s n_returned=%d" % (b.get("total"), len(b["crimes"])))

# by locality
b = show("GET /crimes/locality/Katpadi", client.get("/crimes/locality/Katpadi"))
print("      Katpadi crimes=%d" % len(b["crimes"]))

# by crime type
b = show("GET /crimes/crime-type/Murder", client.get("/crimes/crime-type/Murder"))
print("      Murder crimes=%d" % len(b["crimes"]))

# by risk level
b = show("GET /crimes/risk-level/Critical", client.get("/crimes/risk-level/Critical"))
print("      Critical crimes=%d" % len(b["crimes"]))

# filtered /crimes
b = show("GET /crimes?risk_level=High&has_coordinates=true",
         client.get("/crimes?risk_level=High&has_coordinates=true"))
print("      High+coords=%d" % b.get("total"))

# single crime
b = show("GET /crimes/{article_id}", client.get("/crimes/70d2d39686e4ee8b"))
print("      crime locality=%s severity=%s" % (b["crime"]["locality"], b["crime"]["severity_score"]))

# single crime not found
show("GET /crimes/{bad_id}", client.get("/crimes/nonexistentid123"))

# metadata
b = show("GET /localities", client.get("/localities"))
print("      localities=%d" % len(b))
b = show("GET /crime-types", client.get("/crime-types"))
print("      crime-types=%d" % len(b))
b = show("GET /risk-levels", client.get("/risk-levels"))
print("      risk-levels=%d" % len(b))

# hotspots
b = show("GET /hotspots", client.get("/hotspots"))
print("      hotspots=%d" % b.get("count"))

# proximity at Katpadi (radius 2)
b = show("GET /proximity (Katpadi r=2)", client.get("/proximity?lat=13.043505&lon=79.240410&radius=2"))
print("      nearby=%d overall=%s" % (b.get("nearby_count"), b.get("overall_alert_level")))
for e in b["nearby"]:
    print("        %s %.3f km %s" % (e["location_name"], e["distance_km"], e["highest_risk_level"]))

# proximity far away (no nearby)
b = show("GET /proximity (remote r=2)", client.get("/proximity?lat=13.20&lon=78.90&radius=2"))
print("      nearby=%d overall=%s" % (b.get("nearby_count"), b.get("overall_alert_level")))

# proximity validation error (missing lat)
show("GET /proximity (missing args)", client.get("/proximity"))

print("=" * 70)
print("TESTS COMPLETE")
print("=" * 70)