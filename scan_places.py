import pandas as pd, os, re
from collections import Counter
base = r'c:\Users\\sruth\\crime analysis'

# The path has an escape issue; rebuild properly
base = r'c:\Users\sruth\crime analysis'
fin = pd.read_csv(os.path.join(base,'data','processed','news_scored_final.csv'), low_memory=False)

print('=== All 89 records: article_id, locality, crime_type, title ===')
for _, r in fin.iterrows():
    loc = r.get('locality','')
    loc_s = '' if pd.isna(loc) else str(loc).strip()
    print('{} | loc={!r:20s} | {} | {}'.format(
        r['article_id'][:12], loc_s, r['crime_type'], str(r['title'])[:80]))
