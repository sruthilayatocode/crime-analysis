import urllib.parse, urllib.request, json, time
NOM_URL = 'https://nominatim.openstreetmap.org/search'
def lookup(query):
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(NOM_URL+'?'+params, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CrimeAnalysisProject/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if data:
                d=data[0]; return float(d['lat']), float(d['lon']), d.get('display_name','')[:80]
            return None
    except Exception as e:
        return 'ERR:'+str(e)

queries = [
    'Arani, Tiruvallur, Tamil Nadu, India',
    "Government Hospital, Vellore, Tamil Nadu",
    'Katpadi railway station, Tamil Nadu',
    'Vellore Government Medical College, Tamil Nadu',
    'Vellore Central Prison, Tamil Nadu',
    'Vellore Cantonment, Tamil Nadu',
    'Ambur, Tamil Nadu, India',
]
for q in queries:
    r = lookup(q)
    print('{} -> {}'.format(q, r))
    time.sleep(10)  # respect Nominatim rate limit
