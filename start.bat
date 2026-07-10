@echo off
setlocal
cd /d "%~dp0"

where py.exe >nul 2>&1
if not errorlevel 1 goto use_py

where python.exe >nul 2>&1
if not errorlevel 1 goto use_python

echo Python 3.11-3.13 was not found. Install Python and try again.
pause
exit /b 1

:use_py
py -3 "%~dp0scripts\start_app.py" %*
exit /b %errorlevel%

:use_python
python "%~dp0scripts\start_app.py" %*
exit /b %errorlevel%
