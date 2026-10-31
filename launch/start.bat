@echo off
rem Crossweave offline launcher (Windows). Needs Python 3 from https://www.python.org/downloads/
cd /d "%~dp0app"
set PORT=8017
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo Crossweave running at http://localhost:%PORT%/  (close this window to stop)
start "" http://localhost:%PORT%/
%PY% -m http.server %PORT% --bind 127.0.0.1
if errorlevel 1 (
  echo.
  echo Python 3 is required. Install it from https://www.python.org/downloads/ and try again.
  pause
)
