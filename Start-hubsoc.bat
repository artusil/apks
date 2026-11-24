@echo off
setlocal
cd /d "%~dp0" || goto extract
for %%F in (requirements.txt app.py host.py templates\index.html static\clips.js) do if not exist "%%F" goto extract
if exist ".venv\Scripts\python.exe" goto deps
where py >nul 2>nul
if errorlevel 1 goto pythonpath
py -3 -m venv .venv
if errorlevel 1 goto fail
goto deps
:pythonpath
python -m venv .venv
if errorlevel 1 goto fail
:deps
".venv\Scripts\python.exe" -c "import flask, waitress" >nul 2>nul
if not errorlevel 1 goto run
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
:run
echo Open http://127.0.0.1:8000 in your browser. Keep this window open.
".venv\Scripts\python.exe" host.py --host 127.0.0.1 --port 8000
if not errorlevel 1 exit /b 0
:fail
echo Setup or startup failed. Install Python 3.11 or newer and check the message above.
pause
exit /b 1

:extract
echo The hubsoc folder is incomplete. Do not run this file inside the ZIP.
echo Right-click hubsoc-Windows.zip, choose Extract All, then open the extracted hubsoc folder.
echo Run Start-hubsoc.bat from that folder, next to requirements.txt.
pause
exit /b 1
