@echo off
echo === killing anything listening on port 5000 ===
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 " ^| findstr /i LISTENING') do (
    echo killing pid %%a
    taskkill /f /pid %%a /t >nul 2>&1
)

echo === starting fresh backend ===
cd /d "c:\Users\sruth\crime analysis"
start "crimesense-backend" /b cmd /c "call runapp.bat"

echo === waiting for server to come up ===
set OK=0
for /l %%i in (1,1,20) do (
    curl -s -o nul -w "" "http://127.0.0.1:5000/api/health" >nul 2>&1 && set OK=1 && goto :started
    timeout /t 1 >nul
)
:started
echo health check reachable: %OK%

echo === GET /api/health ===
curl -s -i "http://127.0.0.1:5000/api/health"
echo.
echo === GET /api/crimes (count + first record) ===
curl -s "http://127.0.0.1:5000/api/crimes" > C:\Users\sruth\crimecli\crimes_resp.json
python -c "import json;d=json.load(open(r'C:\Users\sruth\crimecli\crimes_resp.json'));print('count:',d['count'],'success:',d['success'],'total_pages:',d.get('pagination',{}).get('total_pages'));print('keys:',sorted(d['data'][0].keys()));print('first:',json.dumps({k:d['data'][0][k] for k in['id','article_id','crime_type','locality','location_confidence','latitude','longitude','risk_level','severity_score']},indent=2))"
echo.
echo === GET /api/hotspots ===
curl -s "http://127.0.0.1:5000/api/hotspots" > C:\Users\sruth\crimecli\hotspots_resp.json
python -c "import json;d=json.load(open(r'C:\Users\sruth\crimecli\hotspots_resp.json'));print('success:',d['success'],'count:',d['count'],'source:',d['source']);print(json.dumps(d['data'][:2],indent=2))"
echo.
echo === GET /api/risk/Bengaluru ===
curl -s "http://127.0.0.1:5000/api/risk/Bengaluru"
echo.
echo === server.log ===
type backend\server.log
