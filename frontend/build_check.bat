@echo off
cd /d "c:\Users\sruth\crime analysis\frontend"
if not exist node_modules (
  echo MISSING node_modules
  exit /b 1
)
echo node_modules present
npx vite build --minify false 2>&1
echo EXITCODE=%errorlevel%
