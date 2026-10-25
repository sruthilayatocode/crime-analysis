@echo off
set PYEXE=c:\Users\sruth\crime analysis\.venv\Scripts\python.exe
cd /d "c:\Users\sruth\crime analysis"

echo === killing any process on port 5000 ===
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 " ^| findstr /i LISTENING') do (
    echo killing pid %%a
    taskkill /f /pid %%a /t >nul 2>&1
)

echo === starting fresh backend ===
start "crimesense-backend" /b cmd /c "\"%PYEXE%\" backend\app.py > backend\server.log 2>&1"

timeout /t 4 >nul
echo === server.log ===
type backend\server.log
