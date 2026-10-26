@echo off
cd /d "%~dp0"

set PYEXE=python
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYEXE=%~dp0.venv\Scripts\python.exe"
) else if exist "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYEXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
)

echo === killing any process on port 5000 ===
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 " ^| findstr /i LISTENING') do (
    echo killing pid %%a
    taskkill /f /pid %%a /t >nul 2>&1
)

echo === starting fresh backend ===
start "crimesense-backend" /b cmd /c "\"%PYEXE%\" backend\app.py > backend\server.log 2>&1"

timeout /t 3 >nul
echo === server.log ===
if exist backend\server.log (
    type backend\server.log
)
