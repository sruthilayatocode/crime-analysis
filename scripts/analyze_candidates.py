import json
from pathlib import Path
from collections import Counter

CANDIDATES_JSON = Path(r"C:\Users\sruth\crime analysis\data\raw\collected_sources\collected_candidates.json")

candidates = json.loads(CANDIDATES_JSON.read_text(encoding="utf-8"))
print(f"Total candidates: {len(candidates)}")

# Analyze candidates
source_counter = Counter()
has_vellore_terms = 0
has_crime_terms = 0
vellore_and_crime = 0
district_counter = Counter()
locality_counter = Counter()

for c in candidates:
    src = c.get("source", "unknown")
    source_counter[src] += 1
    
    vterms = c.get("vellore_terms", "")
    cterms = c.get("crime_terms", "")
    district = c.get("district", "")
    locality = c.get("locality", "")
    
    if vterms:
        has_vellore_terms += 1
    if cterms:
        has_crime_terms += 1
    if vterms and cterms:
        vellore_and_crime += 1
    if district:
        district_counter[district] += 1
    if locality:
        locality_counter[locality] += 1

print(f"\nWith Vellore terms: {has_vellore_terms}")
print(f"With crime terms: {has_crime_terms}")
print(f"With BOTH (Vellore + crime): {vellore_and_crime}")

print(f"\n--- Sources ---")
for src, count in source_counter.most_common():
    print(f"  {src}: {count}")

print(f"\n--- Districts ---")
for dist, count in district_counter.most_common():
    print(f"  {dist}: {count}")

print(f"\n--- Localities ---")
for loc, count in locality_counter.most_common(20):
    print(f"  {loc}: {count}")

# Show some examples of candidates with both Vellore and crime terms
print(f"\n--- Candidates with Vellore + crime terms (first 10) ---")
count = 0
for c in candidates:
    if c.get("vellore_terms") and c.get("crime_terms"):
        print(f"  [{c.get('source')}] {c.get('headline','')[:80]}")
        print(f"    Vellore terms: {c.get('vellore_terms')}")
        print(f"    Crime terms: {c.get('crime_terms')}")
        print(f"    Locality: {c.get('locality')}")
        count += 1
        if count >= 10:
            break
