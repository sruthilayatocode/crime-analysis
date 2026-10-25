import json
from pathlib import Path

ACCEPTED_JSON = Path(r"C:\Users\sruth\crime analysis\data\processed\accepted_incidents.json")

accepted = json.loads(ACCEPTED_JSON.read_text(encoding="utf-8"))
print(f"Accepted incidents: {len(accepted)}")

for i, inc in enumerate(accepted, 1):
    print(f"\n--- Incident {i} ---")
    print(f"  Headline: {inc.get('headline', inc.get('title', ''))[:100]}")
    print(f"  Source: {inc.get('source', '')}")
    print(f"  URL: {inc.get('source_url', inc.get('url', ''))[:100]}")
    print(f"  Crime type: {inc.get('crime_type', '')}")
    print(f"  Locality: {inc.get('locality', '')}")
    print(f"  District: {inc.get('district', '')}")
    print(f"  Date: {inc.get('published_date', inc.get('incident_date', ''))}")
