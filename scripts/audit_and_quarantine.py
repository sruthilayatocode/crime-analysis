"""
scripts/audit_and_quarantine.py
===============================
Geographic audit of the CrimeSense dataset.
"""
import csv
import sqlite3
from collections import Counter
from pathlib import Path

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"
PROJECT_ROOT = Path(r"C:\Users\sruth\crime analysis")
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Vellore-region geographic scope (including 2019 reorganization)
VELLORE_REGION_LOCALITIES = {
    "vellore", "katpadi", "gudiyatham", "gudiyattam", "pernambut",
    "ambur", "vaniyambadi", "tirupattur", "tirupathur", "jolarpet",
    "natrampalli", "ranipet", "walajapet", "arcot", "melvisharam",
    "sholingur", "alangayam", "thuthipattu", "avaniyapuram",
    "kaniyambadi", "vaanpool", "kannamangalam", "kondapalayam",
    "usilampatti", "senur", "thiruvalam", "karungali", "alleri",
    "madhanur", "kajalpet", "timiri", "kalavai", "melpadi",
}

VELLORE_REGION_DISTRICTS = {
    "vellore", "ranipet", "tirupattur", "tirupathur",
}

VELLORE_REGION_LANDMARKS = {
    "vellore fort", "vellore institute", "vit university", "katpadi junction",
    "vellore jail", "vellore collectorate", "gudiyatham taluk",
    "ambur taluk", "ranipet district", "tirupattur district",
    "walajapet", "arcot town", "melvisharam", "sholingur",
    "jolarpettai", "natrampalli", "pernambut",
}

def normalize(text):
    if not text: return ""
    return text.strip().lower()

def classify_record(locality, district, title, description, source):
    loc = normalize(locality)
    dist = normalize(district)
    title_lower = normalize(title)
    desc_lower = normalize(description)
    all_text = f"{title_lower} {desc_lower}"
    
    # STRONG: District match
    if dist in VELLORE_REGION_DISTRICTS:
        return "VALID_VELLORE_REGION", f"district={dist}"
    
    # STRONG: Locality match
    if loc in VELLORE_REGION_LOCALITIES:
        return "VALID_VELLORE_REGION", f"locality={loc}"
    
    # MEDIUM: Locality mentioned in text
    for vloc in VELLORE_REGION_LOCALITIES:
        if vloc in all_text:
            return "VALID_VELLORE_REGION", f"mentioned={vloc}"
    
    for landmark in VELLORE_REGION_LANDMARKS:
        if landmark in all_text:
            return "VALID_VELLORE_REGION", f"landmark={landmark}"
    
    # OUT OF SCOPE: Has clear non-Vellore location
    if loc or dist:
        return "OUT_OF_SCOPE", f"locality={loc}, district={dist}"
    
    # MISSING LOCATION
    if not loc and not dist:
        return "MISSING_LOCATION", "no locality or district"
    
    return "AMBIGUOUS_NEEDS_REVIEW", "unclear"

def extract_state_from_text(text):
    if not text: return None
    text_lower = text.lower()
    state_keywords = {
        "tamil nadu": "Tamil Nadu", "karnataka": "Karnataka",
        "kerala": "Kerala", "andhra pradesh": "Andhra Pradesh",
        "telangana": "Telangana", "maharashtra": "Maharashtra",
        "delhi": "Delhi", "west bengal": "West Bengal",
        "jharkhand": "Jharkhand", "chhattisgarh": "Chhattisgarh",
        "madhya pradesh": "Madhya Pradesh", "goa": "Goa",
        "puducherry": "Puducherry", "jammu and kashmir": "Jammu and Kashmir",
        "jammu & kashmir": "Jammu and Kashmir",
    }
    for keyword, state in state_keywords.items():
        if keyword in text_lower:
            return state
    return None



# MAIN AUDIT
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM crimes").fetchall()
columns = [desc[0] for desc in conn.execute("SELECT * FROM crimes").description]

valid_vellore = []
out_of_scope = []
ambiguous = []
missing_location = []

states_counter = Counter()
districts_counter = Counter()
localities_counter = Counter()
crime_types_counter = Counter()
sources_counter = Counter()
classification_counter = Counter()

for row in rows:
    d = dict(row)
    crime_types_counter[d["crime_type"]] += 1
    sources_counter[d["source"]] += 1
    
    locality = d.get("locality") or ""
    district = d.get("district") or ""
    title = d.get("title") or ""
    description = d.get("description") or ""
    source = d.get("source") or ""
    
    if locality: localities_counter[locality] += 1
    if district: districts_counter[district] += 1
    
    state = extract_state_from_text(description)
    if state: states_counter[state] += 1
    else: states_counter["Unknown"] += 1
    
    classification, reason = classify_record(locality, district, title, description, source)
    d["_classification"] = classification
    d["_reason"] = reason
    classification_counter[classification] += 1
    
    if classification == "VALID_VELLORE_REGION": valid_vellore.append(d)
    elif classification == "OUT_OF_SCOPE": out_of_scope.append(d)
    elif classification == "MISSING_LOCATION": missing_location.append(d)
    else: ambiguous.append(d)

# WRITE QUARANTINE FILES
def write_csv(data, filename):
    if not data: return
    filepath = ANALYSIS_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns + ["_classification", "_reason"])
        writer.writeheader()
        writer.writerows(data)
    print(f"Written: {filepath} ({len(data)} records)")

write_csv(valid_vellore, "valid_vellore_region.csv")
write_csv(out_of_scope, "out_of_scope_records.csv")
write_csv(missing_location, "missing_location_records.csv")
write_csv(ambiguous, "ambiguous_records.csv")
all_classified = valid_vellore + out_of_scope + missing_location + ambiguous
write_csv(all_classified, "geographic_audit_full.csv")

# PRINT REPORT
print("\n" + "=" * 70)
print("CRIMESENSE GEOGRAPHIC AUDIT REPORT")
print("=" * 70)
print(f"\nTotal records: {len(rows)}")
print(f"VALID_VELLORE_REGION: {len(valid_vellore)}")
print(f"OUT_OF_SCOPE: {len(out_of_scope)}")
print(f"MISSING_LOCATION: {len(missing_location)}")
print(f"AMBIGUOUS_NEEDS_REVIEW: {len(ambiguous)}")

print(f"\n--- Classification Summary ---")
for cls, count in classification_counter.most_common():
    print(f"  {cls}: {count}")

print(f"\n--- States (extracted from description) ---")
for state, count in states_counter.most_common(20):
    print(f"  {state}: {count}")

print(f"\n--- Districts ---")
for dist, count in districts_counter.most_common(20):
    print(f"  {dist}: {count}")

print(f"\n--- Localities (top 30) ---")
for loc, count in localities_counter.most_common(30):
    print(f"  {loc}: {count}")

print(f"\n--- Crime Types ---")
for ct, count in crime_types_counter.most_common():
    print(f"  {ct}: {count}")

print(f"\n--- Sources ---")
for src, count in sources_counter.most_common():
    print(f"  {src}: {count}")

print(f"\n--- Out-of-scope examples (first 15) ---")
for d in out_of_scope[:15]:
    print(f"  [{d['crime_type']}] {d.get('locality','')} | {d['title'][:70]}")

print(f"\n--- Valid Vellore examples (all) ---")
for d in valid_vellore:
    print(f"  [{d['crime_type']}] {d.get('locality','')} | {d['title'][:70]}")

print(f"\n--- Missing location examples (first 10) ---")
for d in missing_location[:10]:
    print(f"  [{d['crime_type']}] {d['title'][:70]}")

conn.close()
print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)


