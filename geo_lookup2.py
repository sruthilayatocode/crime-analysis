import urllib.parse, urllib.request, json, time

def nom_lookup(query):
    url = 'https://nominatim.openstreetmap.org/search'
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(url+'?'+params, headers={'User-Agent':'CrimeAnalysisProject/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
            if data:
                d = data[0]
                return {'lat': float(d['lat']), 'lon': float(d['lon']), 'display_name': d.get('display_name','')}
            return None
    except Exception as e:
        return {'error': str(e)}

def photon_lookup(query):
    url = 'https://photon.komoot.io/api/'
    params = urllib.parse.urlencode({'q':query,'limit':'1'})
    req = urllib.request.Request(url+'?'+params, headers={'User-Agent':'CrimeAnalysisProject/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
            feats = data.get('features',[])
            if feats:
                g = feats[0]['geometry']['coordinates']  # [lon, lat]
                return {'lat': g[1], 'lon': g[0], 'display_name': feats[0]['properties'].get('name','')}
            return None
    except Exception as e:
        return {'error': str(e)}

queries = [
    'Vellore Government Hospital, Vellore, Tamil Nadu',
    'Katpadi Railway Station, Vellore, Tamil Nadu',
    'Vellore Central Prison, Tamil Nadu',
    'Sriperumbudur, Tamil Nadu, India',
]
for q in queries:
    res = nom_lookup(q)
    time.sleep(3.0)
    print('NOMINATIM {!r}'.format(q))
    if res and 'error' not in res:
        print('  -> lat={}, lon={} | {}'.format(round(res['lat'],6), round(res['lon'],6), res['display_name'][:80]))
    else:
        print('  -> Nominatim failed:', res)
        # try photon
        time.sleep(2.0)
        ph = photon_lookup(q)
        print('  PHOTON -> ', ph)
    print()
