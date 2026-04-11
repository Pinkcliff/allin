@echo off
echo Testing Web Sync...
echo.
cd /d %~dp0
D:\ProgramData\Anaconda3\Scripts\activate.bat my_env
python test_sync.py
pause
