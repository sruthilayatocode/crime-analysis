import pandas as pd, os, re
base = r'c:\Users\sruth\crime analysis'
fin = pd.read_csv(os.path.join(base,'data','processed','news_scored_final.csv'), low_memory=False)

# Known places to search for (longest/most-specific first)
known_places = [
    'Katpadi Railway Station', 'Katpadi railway station',
    'Vellore Fort', 'Vellore GH', 'Vellore Government Hospital',
    'Vellore Central Prison', 'Vellore Cantonment', 'Vellore Cantt',
    'Sriperumbudur', 'Pallikonda', 'Ranipet', 'Tirupattur',
    'Tiruppattur', 'Katpadi', 'Arani', 'Ambur', 'Vellore',
]

text_cols = ['title','description','collection_query']
print('=== Records and the KNOWN places found in their text ===')
for _, r in fin.iterrows():
    txt = ' '.join(str(r.get(c,'')) for c in text_cols).lower()
    found = [p for p in known_places if p.lower() in txt]
    loc = r.get('locality','')
    loc_s = '' if pd.isna(loc) else str(loc).strip()
    if found:
        print('{} | loc={} | places_found={} | title={}'.format(
            r['article_id'][:12], loc_s, found, str(r['title'])[:65]))
    else:
        # show which records have NO known place in text
        if loc_s:
            pass
print()

# Specifically: records with NO known place mention in text at all
print('=== Records with NO known place in title/description/query ===')
none_list = []
for _, r in fin.iterrows():
    txt = ' '.join(str(r.get(c,'')) for c in text_cols).lower()
    found = [p for p in known_places if p.lower() in txt]
    if not found:
        none_list.append(r['article_id'][:12])
        print('  {} | title={}'.format(r['article_id'][:12], str(r['title'])[:75]))
print()
print('Total with no known place in text:', len(none_list))

# District column values
print()
print('=== district column values ===')
print(fin['district'].fillna('').astype(str).value_counts().to_dict())

# collection_query values
print()
print('=== collection_query values ===')
print(fin['collection_query'].fillna('').astype(str).value_counts().to_dict())
