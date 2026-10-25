import sqlite3
from collections import Counter

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"

# Vellore-region geographic scope (including 2019 reorganization)
VELLORE_REGION_LOCALITIES = {
    "vellore", "katpadi", "gudiyatham", "gudiyattam", "pernambut",
    "ambur", "vaniyambadi", "tirupattur", "tirupathur", "jolarpet",
    "natrampalli", "ranipet", "walajapet", "arcot", "melvisharam",
    "sholingur", "alangayam", "anandapuram", "gudiyattam", "katpadi",
    "thuthipattu", "avaniyapuram", "kaniyambadi", "ambur",
}

VELLORE_REGION_DISTRICTS = {
    "vellore", "ranipet", "tirupattur", "tirupathur",
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM crimes").fetchall()
print(f"Total records: {len(rows)}")

# Counters
states_counter = Counter()
districts_counter = Counter()
localities_counter = Counter()
crime_types_counter = Counter()
sources_counter = Counter()
location_confidence_counter = Counter()

# Classification
valid_vellore = []
out_of_scope = []
ambiguous = []
missing_location = []

def normalize(text):
    if not text:
        return ""
    return text.strip().lower()

def is_vellore_region(locality, district, title, description):
    """Check if record belongs to Vellore region."""
    loc = normalize(locality)
    dist = normalize(district)
    title_lower = normalize(title)
    desc_lower = normalize(description)
    
    # Check district first (strongest signal)
    if dist in VELLORE_REGION_DISTRICTS:
        return True, f"district={dist}"
    
    # Check locality
    if loc in VELLORE_REGION_LOCALITIES:
        return True, f"locality={loc}"
    
    # Check if any Vellore-region locality appears in title or description
    for vloc in VELLORE_REGION_LOCALITIES:
        if vloc in title_lower or vloc in desc_lower:
            return True, f"mentioned={vloc}"
    
    return False, ""

def extract_state_from_text(text):
    """Try to extract state from text."""
    if not text:
        return None
    text_lower = text.lower()
    state_keywords = {
        "tamil nadu": "Tamil Nadu",
        "karnataka": "Karnataka",
        "kerala": "Kerala",
        "andhra pradesh": "Andhra Pradesh",
        "telangana": "Telangana",
        "maharashtra": "Maharashtra",
        "delhi": "Delhi",
        "west bengal": "West Bengal",
        "uttar pradesh": "Uttar Pradesh",
        "gujarat": "Gujarat",
        "rajasthan": "Rajasthan",
        "punjab": "Punjab",
        "haryana": "Haryana",
        "bihar": "Bihar",
        "odisha": "Odisha",
        "assam": "Assam",
        "jharkhand": "Jharkhand",
        "chhattisgarh": "Chhattisgarh",
        "madhya pradesh": "Madhya Pradesh",
        "goa": "Goa",
        "puducherry": "Puducherry",
    }
    for keyword, state in state_keywords.items():
        if keyword in text_lower:
            return state
    return None

for row in rows:
    d = dict(row)
    crime_types_counter[d["crime_type"]] += 1
    sources_counter[d["source"]] += 1
    location_confidence_counter[d["location_confidence"] or "NULL"] += 1
    
    locality = d.get("locality") or ""
    district = d.get("district") or ""
    title = d.get("title") or ""
    description = d.get("description") or ""
    
    if locality:
        localities_counter[locality] += 1
    if district:
        districts_counter[district] += 1
    
    # Try to extract state from description
    state = extract_state_from_text(description)
    if state:
        states_counter[state] += 1
    else:
        states_counter["Unknown"] += 1
    
    # Classify
    is_vellore, reason = is_vellore_region(locality, district, title, description)
    
    if is_vellore:
        valid_vellore.append(d)
    elif not locality and not district:
        missing_location.append(d)
    elif locality or district:
        # Has some location info but not Vellore
        out_of_scope.append(d)
    else:
        ambiguous.append(d)

print("\n" + "="*60)
print("GEOGRAPHIC AUDIT REPORT")
print("="*60)

print(f"\nTotal records: {len(rows)}")
print(f"Valid Vellore-region: {len(valid_vellore)}")
print(f"Out-of-scope: {len(out_of_scope)}")
print(f"Missing location: {len(missing_location)}")
print(f"Ambiguous: {len(ambiguous)}")

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

print(f"\n--- Location Confidence ---")
for lc, count in location_confidence_counter.most_common():
    print(f"  {lc}: {count}")

# Show some out-of-scope examples
print(f"\n--- Out-of-scope examples (first 10) ---")
for d in out_of_scope[:10]:
    print(f"  [{d['crime_type']}] {d.get('locality','')} | {d.get('district','')} | {d['title'][:60]}")

# Show valid Vellore examples
print(f"\n--- Valid Vellore examples (first 10) ---")
for d in valid_vellore[:10]:
    print(f"  [{d['crime_type']}] {d.get('locality','')} | {d.get('district','')} | {d['title'][:60]}")

conn.close()
