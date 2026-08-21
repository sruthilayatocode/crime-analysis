import csv
from collections import Counter

with open('data/processed/news_geocoded_v2.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print('Rows:', len(rows))
lat_none = sum(1 for r in rows if not r['latitude'].strip())
print('With latitude:', len(rows) - lat_none)
print('Without latitude:', lat_none)
print('With longitude:', sum(1 for r in rows if r['longitude'].strip()))
print()
conf = Counter(r['location_confidence'] for r in rows)
print('location_confidence:', dict(conf))
print()
loc = Counter(r['locality'] for r in rows)
print('locality counts:')
for k, v in sorted(loc.items(), key=lambda x: (-x[1], str(x[0]))):
    print('  {}: {}'.format(repr(k), v))
print()
ct = Counter(r['crime_type'] for r in rows)
print('crime_type counts:')
for k, v in sorted(ct.items(), key=lambda x: (-x[1], x[0])):
    print('  {}: {}'.format(k, v))
print()
print('=== Records WITH lat/lon ===')
for i, r in enumerate(rows):
    if r['latitude'].strip() and r['longitude'].strip():
        print('  row{} aid={} loc={} conf={} src={} lat={} lon={}'.format(
            i+2, r['article_id'][:8], repr(r['locality']),
            r['location_confidence'], r['location_source'],
            r['latitude'], r['longitude']))