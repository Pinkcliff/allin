@echo off
cd /d %~dp0

echo Testing Web Sync...
echo.

call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env

echo.
echo Running test script...
echo.

python test_sync.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Python script failed with exit code %ERRORLEVEL%
    echo.
)

pause
