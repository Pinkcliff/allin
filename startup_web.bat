@echo off
echo ========================================
echo   Web Digital Twin System Startup
echo ========================================
echo.

REM Check if my_env exists
echo Checking conda environment...
call conda env list | findstr /C:"my_env" >nul
if errorlevel 1 (
    echo Error: Conda environment 'my_env' not found!
    echo Please create it first: conda create -n my_env python=3.11
    pause
    exit /b 1
)

REM Activate my_env environment
echo Activating my_env environment...
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env

REM Install backend dependencies
echo.
echo Installing backend dependencies...
cd /d "%~dp0web\backend"
pip install -q -r requirements.txt

REM Start backend server
echo.
echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0web\backend && python -m main"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

REM Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd /d "%~dp0web\frontend"
if not exist "node_modules" (
    echo Installing frontend dependencies (this may take a while)...
    call npm install
)

REM Start frontend server
echo.
echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d %~dp0web\frontend && npm run dev"

echo.
echo ========================================
echo   Web System Started Successfully!
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend:     http://localhost:5173
echo API Docs:     http://localhost:8000/docs
echo.
echo Default Accounts:
echo   Admin:     admin / admin123
echo   Operator:  operator / operator123
echo   Viewer:    viewer / viewer123
echo.
echo Press any key to stop all servers...
pause > nul

REM Stop all servers when key pressed
echo.
echo Stopping servers...
taskkill /FI "WINDOWTITLE eq Backend Server*" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq Frontend Server*" /T /F 2>nul
echo Servers stopped.
timeout /t 2 /nobreak > nul
