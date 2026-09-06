import urllib.parse, urllib.request, json, time
NOM_URL = 'https://nominatim.openstreetmap.org/search'
def lookup(query):
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(NOM_URL+'?'+params, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CrimeAnalysisProject/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if data:
                d=data[0]; return float(d['lat']), float(d['lon']), d.get('display_name','')[:90]
            return None
    except Exception as e:
        return 'ERR:'+str(e)

# Try Arani differently + landmarks
time.sleep(8)
queries = [
    'Arani, Tamil Nadu, India',                  # what cache has (suspicious 13.331, 80.084)
    'Vellore Government Hospital',               # try without ", Vellore"
    'Katpadi Railway Station',                   # try without ", Tamil Nadu"
    'Government Medical College, Vellore',        # alt for Medical College
]
for q in queries:
    r = lookup(q)
    print('{} -> {}'.format(q, r))
    time.sleep(10)
