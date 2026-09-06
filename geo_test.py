import urllib.parse, urllib.request, json, time, os, sys

NOM_URL = 'https://nominatim.openstreetmap.org/search'
HEADERS = {'User-Agent': 'CrimeAnalysisProject/1.0 (crime-analysis@example.com)'}

def lookup(query):
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(NOM_URL+'?'+params, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if data:
                d = data[0]
                return {'lat': float(d['lat']), 'lon': float(d['lon']), 'display_name': d.get('display_name','')}
            return None
    except Exception as e:
        return {'error': str(e)}

# Test if Nominatim is available at all
for q in ['Arani, Tiruvallur, Tamil Nadu, India', 'Vellore Government Hospital, Tamil Nadu']:
    print('Trying:', q)
    res = lookup(q)
    time.sleep(5)
    if res and 'error' not in res:
        print('  OK: lat={}, lon={} | {}'.format(round(res['lat'],6), round(res['lon'],6), res['display_name'][:90]))
    else:
        print('  FAIL:', res)
    print()
