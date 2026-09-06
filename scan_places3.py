import pandas as pd, os, re
from collections import Counter
base = r'c:\Users\sruth\crime analysis'
fin = pd.read_csv(os.path.join(base,'data','processed','news_scored_final.csv'), low_memory=False)
val = pd.read_csv(os.path.join(base,'data','processed','news_validated.csv'), low_memory=False)

# All candidate places (broad + specific), lower = higher priority to match (longer first)
places = ['katpadi railway station','katpadi railway','vellore medical college',
          'government hospital','gh','vellore fort','sriperumbudur','pallikonda',
          'ranipet','tiruppattur','tirupattur','katpadi','villain','arani','ambur',
          'vellore']

# Scan title + description for ANY place mention
print('=== Detailed place scan (title + description) for all 89 records ===')
for _, r in fin.iterrows():
    txt = (str(r.get('title','')) + ' ' + str(r.get('description',''))).lower()
    found_specific = []
    for p in places:
        if p in txt and p != 'vellore':
            found_specific.append(p)
    print('{} | {} | specific={}'.format(
        r['article_id'][:10], str(r['title'])[:50], found_specific if found_specific else 'none'))
print()

# Validated locality for the NaN-local rows
print('=== Validated locality for records that are NaN in enriched ===')
enr_locs = set(fin['locality'].dropna().astype(str).str.strip())
val_locality_map = dict(zip(val['article_id'], val['locality']))
for _, r in fin.iterrows():
    enr_loc = r.get('locality','')
    if pd.isna(enr_loc) or str(enr_loc).strip()=='':
        vid = r['article_id']
        vloc = val_locality_map.get(vid, '')
        if vloc and str(vloc).strip() and str(vloc).strip().lower() != 'nan':
            print('  {} | enriched=NaN | validated_locality={!r} | {}'.format(
                vid[:10], str(vloc).strip(), str(r['title'])[:55]))
