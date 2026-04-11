@echo off
chcp 65001 >nul
cd /d %~dp0

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher.ps1"
set choice=%ERRORLEVEL%

if "%choice%"=="1" goto desktop
if "%choice%"=="2" goto integrated
if "%choice%"=="3" goto webonly
goto end

:desktop
echo Starting desktop client...
set QT_QPA_PLATFORM_PLUGIN_PATH=D:\ProgramData\Anaconda3\envs\my_env\Lib\site-packages\PySide6\plugins\platforms
set PYTHONPATH=%CD%;%CD%\src
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env
start "" python src\main.py
goto end

:integrated
echo Starting integrated system...
cd /d %~dp0
echo Current directory: %CD%
echo.
set QT_QPA_PLATFORM_PLUGIN_PATH=D:\ProgramData\Anaconda3\envs\my_env\Lib\site-packages\PySide6\plugins\platforms
set PYTHONPATH=%CD%;%CD%\src;%CD%\integrated_system
echo Activating my_env environment...
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env
echo.
echo Launching integrated system...
python integrated_system\main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Integrated system exited with code %ERRORLEVEL%
    pause
)
goto end

:webonly
echo Starting web backend service...
cd /d %~dp0\web\backend
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env
start "" python main.py
timeout /t 3 >nul
echo.
echo Frontend: http://localhost:5174
echo Backend API: http://localhost:8000
echo.
start "" http://localhost:5174
goto end

:end
