@echo off
echo Starting Micro UAV Intelligent Wind Field Test and Evaluation System...
echo.

REM Activate my_env environment
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env

REM Change to project directory
cd /d F:\A-User\cliff\allin\src

REM Start the program
python main.py

pause
