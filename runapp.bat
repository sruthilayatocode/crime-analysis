@echo off
cd /d "%~dp0"

REM Find python executable
set PYEXE=python
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYEXE=%~dp0.venv\Scripts\python.exe"
) else if exist "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYEXE=C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
)

"%PYEXE%" backend\app.py > backend\server.log 2>&1
