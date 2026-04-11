@echo off
chcp 65001
echo ================================================
echo   关闭所有Python进程
echo ================================================
echo.

echo 正在查找Python进程...
tasklist | findstr python.exe

echo.
echo 即将关闭所有Python进程...
echo.
pause

taskkill /F /IM python.exe

echo.
echo 所有Python进程已关闭！
echo.
pause
