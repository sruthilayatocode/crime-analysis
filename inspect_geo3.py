import pandas as pd, os, json, re, urllib.parse, urllib.request
from collections import Counter
base = r'c:\Users\sruth\crime analysis'

# --- Load data ---
fin = pd.read_csv(os.path.join(base,'data','processed','news_scored_final.csv'), low_memory=False)
val = pd.read_csv(os.path.join(base,'data','processed','news_validated.csv'), low_memory=False)
gc_v1 = pd.read_csv(os.path.join(base,'data','processed','news_geocoded.csv'), low_memory=False)
gc_v2 = pd.read_csv(os.path.join(base,'data','processed','news_geocoded_v2.csv'), low_memory=False)

with open(os.path.join(base,'data','cache','geocode_cache.json')) as f:
    cache = json.load(f)

with open(os.path.join(base,'data','reference','vellore_localities_config.json')) as f:
    config = json.load(f)

print('=== vellore_localities_config.json localities ===')
for item in config['localities']:
    print('  name={!r} aliases={}'.format(item['name'], item.get('aliases',[])))
print()

# --- Check article_id alignment between validated (has locality) and scored final ---
print('=== article_id alignment: validated vs scored_final ===')
v_ids = set(val['article_id'])
f_ids = set(fin['article_id'])
print('  validated IDs:', len(v_ids), '| scored IDs:', len(f_ids), '| match:', v_ids==f_ids)
print()

# --- What places are mentioned in titles+descriptions? ---
places_of_interest = ['Katpadi','Pallikonda','Arani','Ranipet','Tirupattur','Sriperumbudur',
    'Vellore Fort','Vellore GH','Vellore Central Prison','Chennai','Tiruppattur','Ambur',
    'Sathyamangalam','Kaveripattinam','Perambur','Nathavasi','Tirumala','Vellore Cantonment']
text_cols = ['title','description','collection_query']
print('=== Place mentions across all 89 records (title+description+query) ===')
all_text = ' '.join(str(fin[c].fillna('')) for c in text_cols for _, fin_row in [ (None, fin) ]).join([''])  # build combined text
# simpler: scan each record
mention_counter = Counter()
for _, r in fin.iterrows():
    txt = ' '.join(str(r.get(c,'')) for c in text_cols).lower()
    for pl in places_of_interest:
        if pl.lower() in txt:
            mention_counter[pl] += 1
for k,v in sorted(mention_counter.items(), key=lambda x:-x[1]):
    print('  {!r}: {} records'.format(k, v))
print()

# --- Test Nominatim access (single, cached-style request) ---
print('=== Testing Nominatim network access ===')
def nominatim_lookup(query):
    url = 'https://nominatim.openstreetmap.org/search'
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(url+'?'+params, headers={'User-Agent':'CrimeAnalysisProject/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            import json as J
            data = J.loads(resp.read())
            return data[0] if data else None
    except Exception as e:
        return 'ERROR: '+str(e)
for q in ['Arani, Tamil Nadu, India','Vellore Fort, Vellore, Tamil Nadu']:
    res = nominatim_lookup(q)
    print('  Nominatim {!r}: {}'.format(q, res))
print()

# --- Check geocoded_v2 rows with coordinates ---
print('=== geocoded_v2 records WITH coordinates ===')
g7 = gc_v2[gc_v2['latitude'].notna()]
for _, r in g7.iterrows():
    print('  art={} | loc={!r} | lat={} lon={} | conf={} | {}'.format(
        r['article_id'][:12], r['locality'], r['latitude'], r['longitude'],
        r.get('location_confidence',''), str(r.get('title',''))[:55]))
print()

# --- Check geocoded.csv (v1, 80 records) ---
print('=== geocoded.csv (v1) summary ===')
print('  Shape:', gc_v1.shape)
print('  locality counts:', dict(Counter(gc_v1['locality'])))
print('  coords present:', gc_v1['latitude'].notna().sum(), 'of', len(gc_v1))
# Does it overlap with validated?
print('  v1 IDs in validated:', len(set(gc_v1['article_id']) & v_ids), 'of', len(gc_v1))
