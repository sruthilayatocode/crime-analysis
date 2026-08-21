import urllib.parse, urllib.request, json, time
NOM_URL = 'https://nominatim.openstreetmap.org/search'
def lookup(query):
    params = urllib.parse.urlencode({'format':'json','q':query,'email':'crime-analysis@example.com','limit':'1'})
    req = urllib.request.Request(NOM_URL+'?'+params, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CrimeAnalysisProject/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if data:
                d=data[0]; return float(d['lat']), float(d['lon']), d.get('display_name','')
            return None
    except Exception as e:
        return 'ERR:'+str(e)
time.sleep(8)
for q in ['Vellore Government Hospital, Vellore', 'Sriperumbudur, Tamil Nadu']:
    r = lookup(q)
    print(q, '->', r)
    time.sleep(5)
