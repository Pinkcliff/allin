@echo off
echo Starting Micro UAV Intelligent Wind Field Test and Evaluation System...
echo.

REM Activate my_env environment
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env

REM Change to project root directory
cd /d F:\A-User\cliff\allin

REM Start the program as a module
python -m src.main

pause
