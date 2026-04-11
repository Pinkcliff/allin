@echo off
set PYTHON_EXE=D:\ProgramData\Anaconda3\envs\my_env\python.exe
cd /d %~dp0

echo Starting System...
echo.

echo [1/3] Desktop Client...
start "" "%PYTHON_EXE%" integrated_system\main.py
timeout /t 2 /nobreak >/dev/null

echo [2/3] Web Backend...
start "" /D "%~dp0web\backend" "%PYTHON_EXE%" main.py
timeout /t 2 /nobreak >/dev/null

echo [3/3] Web Frontend...
start "" /D "%~dp0web\frontend" npm run dev
timeout /t 2 /nobreak >/dev/null

echo.
echo ================================
echo System Started!
echo ================================
echo Frontend: http://localhost:5174
echo Backend:  http://localhost:8000
echo.
pause
