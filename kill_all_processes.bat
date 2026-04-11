@echo off
chcp 65001
cls
echo ================================================
echo   强制关闭所有相关进程
echo ================================================
echo.

echo 正在关闭所有Python进程...
taskkill /F /IM python.exe 2>nul

echo.
echo 正在关闭所有Node进程...
taskkill /F /IM node.exe 2>nul

echo.
echo 正在检查端口占用...
echo 8000端口:
netstat -ano | findstr ":8000"
echo.
echo 5173端口:
netstat -ano | findstr ":5173"
echo.
echo 5174端口:
netstat -ano | findstr ":5174"

echo.
echo ================================================
echo   清理完成！
echo ================================================
echo.
echo 现在可以重新启动程序了
echo.
timeout /t 3
