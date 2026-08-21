import pandas as pd, os, json
base = r'c:\Users\sruth\crime analysis'
fin = pd.read_csv(os.path.join(base,'data','processed','news_scored_final.csv'), low_memory=False)
val = pd.read_csv(os.path.join(base,'data','processed','news_validated.csv'), low_memory=False)
gcv = pd.read_csv(os.path.join(base,'data','processed','geocoded_v2.csv'), low_memory=False)

print('=== news_scored_final.csv ===')
print('shape:', fin.shape)
print('columns:', list(fin.columns))
print('dtypes:')
print(fin.dtypes)
print()

print('=== news_validated.csv ===')
print('shape:', val.shape)
print('columns:', list(val.columns))
print('locality values:', val['locality'].value_counts().to_dict())
print('has lat/lon cols?', 'lat' in val.columns, 'lon' in val.columns)
print()

print('=== geocoded_v2.csv ===')
print('shape:', gcv.shape)
print('columns:', list(gcv.columns))
print('lat/lon coverage:')
print('  lat non-null:', gcv['lat'].notna().sum())
print('  lon non-null:', gcv['lon'].notna().sum())
print()

# Which article_ids are in geocoded_v2 but NOT in scored_final (or vice versa)
sids = set(fin['article_id'])
gids = set(gcv['article_id'])
print('article_id in scored_final:', len(sids))
print('article_id in geocoded_v2:', len(gids))
print('in scored_final but NOT geocoded_v2:', len(sids - gids))
print('in geocoded_v2 but NOT scored_final:', len(gids - sids))
print()

# Show the geocoded_v2 records with coords
print('=== geocoded_v2 records WITH lat/lon ===')
for _, r in gcv[gcv['lat'].notna() | gcv['lon'].notna()].iterrows():
    print('  {} | title={} | loc={} | lat={} | lon={}'.format(
        str(r['article_id'])[:10], str(r.get('title',''))[:45], 
        r.get('locality',''), r.get('lat',''), r.get('lon','')))
print()
print('=== geocoded_v2 records WITHOUT lat/lon ===')
gcv_no = gcv[gcv['lat'].isna() & gcv['lon'].isna()]
print('count:', len(gcv_no))
