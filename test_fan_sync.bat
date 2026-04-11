@echo off
echo Testing fan data sync to web...
cd /d %~dp0
D:\ProgramData\Anaconda3\Scripts\activate.bat my_env
python test_fan_sync.py
pause
