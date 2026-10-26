@echo off
cd /d "%~dp0"

echo === killing anything listening on port 5000 ===
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 " ^| findstr /i LISTENING') do (
    echo killing pid %%a
    taskkill /f /pid %%a /t >nul 2>&1
)

echo === starting fresh backend ===
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
echo === GET /api/crimes (count) ===
curl -s "http://127.0.0.1:5000/api/crimes?limit=1"
echo.
echo === GET /api/hotspots ===
curl -s "http://127.0.0.1:5000/api/hotspots"
echo.
echo === GET /api/risk/Bengaluru ===
curl -s "http://127.0.0.1:5000/api/risk/Bengaluru"
echo.
echo === server.log ===
if exist backend\server.log (
    type backend\server.log
)
