import csv
from collections import Counter

VELLORE_REGION_LOCALITIES = {
    "vellore", "katpadi", "gudiyatham", "gudiyattam", "pernambut",
    "ambur", "vaniyambadi", "tirupattur", "tirupathur", "jolarpet",
    "natrampalli", "ranipet", "walajapet", "arcot", "melvisharam",
    "sholingur", "alangayam", "thuthipattu", "avaniyapuram",
    "kaniyambadi",
}

VELLORE_REGION_DISTRICTS = {
    "vellore", "ranipet", "tirupattur", "tirupathur",
}

def normalize(text):
    if not text: return ""
    return text.strip().lower()

# Check original 89 records
with open(r"C:\Users\sruth\crime analysis\data\final\crimesense_database_import.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"Original 89 records audit:")
print(f"Total: {len(rows)}")

locality_counter = Counter()
district_counter = Counter()
valid = 0
invalid = 0

for r in rows:
    loc = normalize(r.get("locality"))
    dist = normalize(r.get("district"))
    
    if loc: locality_counter[loc] += 1
    if dist: district_counter[dist] += 1
    
    is_valid = False
    if dist in VELLORE_REGION_DISTRICTS:
        is_valid = True
    if loc in VELLORE_REGION_LOCALITIES:
        is_valid = True
    
    if is_valid:
        valid += 1
    else:
        invalid += 1

print(f"\nValid Vellore-region: {valid}")
print(f"Invalid/out-of-scope: {invalid}")

print(f"\n--- Districts ---")
for d, c in district_counter.most_common():
    print(f"  {d}: {c}")

print(f"\n--- Localities ---")
for l, c in locality_counter.most_common():
    print(f"  {l}: {c}")
