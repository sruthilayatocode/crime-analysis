@echo off
cd /d "c:\Users\sruth\crime analysis"
call "c:\Users\sruth\crime analysis\.venv\Scripts\activate.bat"
python backend\app.py > backend\server.log 2>&1
