import urllib.parse, urllib.request, json, time

NOM_URL = 'https://nominatim.openstreetmap.org/search'
HEADERS = {'User-Agent': 'CrimeAnalysisProject/1.0 (crime-analysis@example.com)'}

def lookup(query):
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(NOM_URL+'?'+params, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
            if data:
                d = data[0]
                return {'lat': float(d['lat']), 'lon': float(d['lon']), 'display_name': d.get('display_name',''), 'class': d.get('class',''), 'type': d.get('type',''), 'osm_id': d.get('osm_id','')}
            return None
    except Exception as e:
        return {'error': str(e)}

# Places to verify — cross-check cache entries + new places mentioned in articles
queries = [
    'Arani, Tiruvallur, Tamil Nadu, India',      # cache suspicious: 13.331, 80.084
    'Arani, Vellore, Tamil Nadu, India',          # alternate: Arani in Vellore district
    'Sriperumbudur, Tamil Nadu, India',           # mentioned in 1 article
    'Vellore Government Hospital, Vellore, Tamil Nadu',  # Vellore GH
    'Katpadi Railway Station, Vellore, Tamil Nadu',     # landmark
    'Vellore Central Prison, Tamil Nadu',         # mentioned
    'Vellore, Tamil Nadu, India',                 # cross-check cache
    'Katpadi, Tamil Nadu, India',                 # cross-check cache
    'Pallikonda, Tamil Nadu, India',              # cross-check cache
    'Ranipet, Tamil Nadu, India',                 # cross-check cache
    'Tirupattur, Tamil Nadu, India',              # cross-check cache
    'Vellore Fort, Vellore, Tamil Nadu',          # cross-check
    'Vellore Cantonment, Tamil Nadu',             # config locality
    'Ambur, Tamil Nadu, India',                  # config locality
]
for q in queries:
    res = lookup(q)
    time.sleep(1.1)
    print('QUERY: {!r}'.format(q))
    if res and 'error' not in res:
        print('  -> lat={}, lon={} | dn={}'.format(round(res['lat'],6), round(res['lon'],6), res['display_name'][:80]))
    elif res and 'error' in res:
        print('  -> ERROR:', res['error'])
    else:
        print('  -> NO RESULT')
    print()
